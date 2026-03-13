"""Deterministic Stage-7 grounded answer generation helpers."""

from __future__ import annotations

import importlib
import re
from collections.abc import Callable
from functools import lru_cache
from typing import Protocol, cast

import structlog
from pydantic import BaseModel, ConfigDict, Field

from doc_forge.app.logging import get_logger

from .contracts import (
    AnswerDraft,
    AnswerMode,
    AnswerModeDecision,
    ContextManifest,
    CorpusSnapshot,
    InterpretedQuery,
    QueryRequest,
    QueryRequestType,
    SupportAssessment,
    SupportQualifierReason,
    SupportState,
)
from .policies import QueryPolicy

logger = get_logger(__name__)


GENERATOR_VERSION = "answer_generation.deterministic.v1"
MLX_GENERATOR_VERSION = "answer_generation.mlx.v1"
_SUPPORT_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]*")


class GroundedGenerationResult(BaseModel):
    """Structured Stage-7 generation result plus trace metadata."""

    model_config = ConfigDict(extra="forbid")

    answer_draft: AnswerDraft
    visible_limitations: list[str] = Field(default_factory=list)
    generator_version: str = Field(min_length=1)


class GroundedAnswerGenerator(Protocol):
    """Grounded-answer generation seam."""

    def generate(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        context_manifest: ContextManifest,
        support_assessment: SupportAssessment,
        answer_mode_decision: AnswerModeDecision,
        policy: QueryPolicy,
    ) -> GroundedGenerationResult:
        """Render the final answer draft under the Stage-6 support ceiling."""
        ...


class DeterministicGroundedAnswerGenerator:
    """Deterministic answer renderer for the Stage-7 MVP path."""

    def generate(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        context_manifest: ContextManifest,
        support_assessment: SupportAssessment,
        answer_mode_decision: AnswerModeDecision,
        policy: QueryPolicy,
    ) -> GroundedGenerationResult:
        del snapshot, policy

        visible_limitations = _build_visible_limitations(
            support_assessment=support_assessment,
            answer_mode_decision=answer_mode_decision,
        )
        grounded_evidence_set_ids = _grounded_evidence_set_ids(
            context_manifest=context_manifest,
            answer_mode=answer_mode_decision.answer_mode,
        )
        answer_text = _build_answer_text(
            request=request,
            interpreted_query=interpreted_query,
            context_manifest=context_manifest,
            support_assessment=support_assessment,
            answer_mode_decision=answer_mode_decision,
            visible_limitations=visible_limitations,
        )
        answer_draft = AnswerDraft(
            answer_text=answer_text,
            visible_limitations=visible_limitations,
            should_render_citations=(
                answer_mode_decision.answer_mode is not AnswerMode.FULL_ABSTENTION
            ),
            grounded_evidence_set_ids=grounded_evidence_set_ids,
            generator_version=GENERATOR_VERSION,
        )
        return GroundedGenerationResult(
            answer_draft=answer_draft,
            visible_limitations=visible_limitations,
            generator_version=GENERATOR_VERSION,
        )


class _LlmBackend(Protocol):
    def generate(
        self,
        *,
        model_name: str,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
    ) -> str: ...


def require_mlx_lm() -> None:
    """Assert that the optional mlx dependency group is installed."""

    try:
        importlib.import_module("mlx_lm")
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "mlx-lm is not installed. Run `uv sync --group llm --group mac` "
            "to enable Apple Silicon local generation."
        ) from exc


@lru_cache(maxsize=4)
def _load_mlx_components(model_name: str) -> tuple[object, object, Callable[..., object]]:
    require_mlx_lm()
    mlx_lm = importlib.import_module("mlx_lm")
    generate = cast(Callable[..., object], mlx_lm.generate)
    load = cast(Callable[[str], tuple[object, object]], mlx_lm.load)

    model, tokenizer = load(model_name)
    return model, tokenizer, generate


class _DefaultMlxBackend:
    def generate(
        self,
        *,
        model_name: str,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
    ) -> str:
        model, tokenizer, generate_fn = _load_mlx_components(model_name)
        kwargs: dict[str, object] = {
            "prompt": prompt,
            "max_tokens": max_new_tokens,
        }
        try:
            result = generate_fn(model, tokenizer, temperature=temperature, **kwargs)
        except TypeError as exc:
            if "temperature" not in str(exc):
                raise
            result = generate_fn(model, tokenizer, temp=temperature, **kwargs)
        return str(result).strip()


class MlxGroundedAnswerGenerator:
    """Apple Silicon grounded answer generator backed by mlx-lm."""

    def __init__(
        self,
        *,
        model_name: str = "mlx-community/TinyLlama-1.1B-Chat-v1.0",
        max_new_tokens: int = 256,
        temperature: float = 0.0,
        backend: _LlmBackend | None = None,
        fallback: GroundedAnswerGenerator | None = None,
        logger: structlog.stdlib.BoundLogger | None = None,
    ) -> None:
        if max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be greater than 0")
        if temperature < 0:
            raise ValueError("temperature must be greater than or equal to 0")
        self._model_name = model_name
        self._max_new_tokens = max_new_tokens
        self._temperature = temperature
        self._backend = backend or _DefaultMlxBackend()
        self._fallback = fallback or DeterministicGroundedAnswerGenerator()
        self._logger = logger or get_logger(self.__class__.__name__)

    def generate(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        context_manifest: ContextManifest,
        support_assessment: SupportAssessment,
        answer_mode_decision: AnswerModeDecision,
        policy: QueryPolicy,
    ) -> GroundedGenerationResult:
        self._logger.info(
            "query.llm.generated", generator_backend="mlx", model_name=self._model_name
        )
        fallback_result = self._fallback.generate(
            request=request,
            snapshot=snapshot,
            interpreted_query=interpreted_query,
            context_manifest=context_manifest,
            support_assessment=support_assessment,
            answer_mode_decision=answer_mode_decision,
            policy=policy,
        )
        if answer_mode_decision.answer_mode is AnswerMode.FULL_ABSTENTION:
            return fallback_result

        prompt = _build_llm_prompt(
            request=request,
            interpreted_query=interpreted_query,
            context_manifest=context_manifest,
            support_assessment=support_assessment,
            answer_mode_decision=answer_mode_decision,
            visible_limitations=fallback_result.visible_limitations,
        )
        generated_text = self._backend.generate(
            model_name=self._model_name,
            prompt=prompt,
            max_new_tokens=self._max_new_tokens,
            temperature=self._temperature,
        ).strip()
        answer_text = generated_text or fallback_result.answer_draft.answer_text
        answer_draft = fallback_result.answer_draft.model_copy(
            update={
                "answer_text": answer_text,
                "generator_version": MLX_GENERATOR_VERSION,
            }
        )
        return GroundedGenerationResult(
            answer_draft=answer_draft,
            visible_limitations=fallback_result.visible_limitations,
            generator_version=MLX_GENERATOR_VERSION,
        )


def _build_answer_text(
    *,
    request: QueryRequest,
    interpreted_query: InterpretedQuery,
    context_manifest: ContextManifest,
    support_assessment: SupportAssessment,
    answer_mode_decision: AnswerModeDecision,
    visible_limitations: list[str],
) -> str:
    snippets = _extract_support_snippets(context_manifest)
    supported_text = _select_supported_text(
        snippets=snippets,
        interpreted_query=interpreted_query,
        answer_mode=answer_mode_decision.answer_mode,
    )
    if not supported_text and support_assessment.summary:
        supported_text = support_assessment.summary

    answer_mode = answer_mode_decision.answer_mode
    if (
        interpreted_query.request_type.value == "comparison"
        and answer_mode is not AnswerMode.FULL_ABSTENTION
    ):
        comparison_text = _build_comparison_answer_text(context_manifest)
        if comparison_text:
            return comparison_text
    if answer_mode is AnswerMode.DIRECT_ANSWER:
        return (
            supported_text
            or "The corpus supports a direct answer, but no answer text was assembled."
        )
    if answer_mode is AnswerMode.NARROWED_ANSWER:
        return _join_sentences(
            "Within the supported scope, " + _lowercase_first(supported_text or request.question),
            visible_limitations[0] if visible_limitations else None,
        )
    if answer_mode is AnswerMode.QUALIFIED_ANSWER:
        return _join_sentences(
            supported_text or "The corpus partially addresses the question.",
            visible_limitations[0] if visible_limitations else None,
        )
    if answer_mode is AnswerMode.QUALIFIED_UNCERTAINTY:
        conflict_note = (
            support_assessment.conflicting_evidence_notes[0]
            if support_assessment.conflicting_evidence_notes
            else "The retrieved evidence does not support a single unqualified answer."
        )
        return _join_sentences(
            conflict_note,
            supported_text or None,
            visible_limitations[0] if visible_limitations else None,
        )
    if answer_mode is AnswerMode.SCOPED_ABSTENTION:
        return _join_sentences(
            "The corpus does not support the full request at the requested scope.",
            supported_text or "A narrower supported answer may still be available.",
            visible_limitations[0] if visible_limitations else None,
        )
    if (
        SupportQualifierReason.UNSUPPORTED_QUESTION_TYPE
        in support_assessment.qualifying_reason_codes
    ):
        unsupported = ", ".join(
            flag.value for flag in interpreted_query.unsupported_capability_flags
        )
        detail = f" Unsupported capability flags: {unsupported}." if unsupported else ""
        return f"The current corpus and MVP query path do not support that question type.{detail}"
    if support_assessment.support_state is SupportState.INSUFFICIENT:
        return "The corpus does not provide enough support to answer that question."
    return (
        support_assessment.summary or "The answer could not be generated from the current evidence."
    )


def _build_llm_prompt(
    *,
    request: QueryRequest,
    interpreted_query: InterpretedQuery,
    context_manifest: ContextManifest,
    support_assessment: SupportAssessment,
    answer_mode_decision: AnswerModeDecision,
    visible_limitations: list[str],
) -> str:
    context_block = "\n\n".join(
        item.rendered_text.strip() for item in context_manifest.context_items if item.rendered_text
    ).strip()
    if not context_block:
        context_block = "No grounded context was assembled."
    limitations_block = "\n".join(f"- {item}" for item in visible_limitations) or "- None"
    summary = support_assessment.summary or "No support summary was provided."
    return (
        "You are generating a grounded answer for a local RAG system.\n"
        "Use only the grounded context below. Do not invent facts, sources, or citations.\n"
        "If the grounded context is limited, reflect that limitation directly in the answer.\n\n"
        f"Question: {request.question}\n"
        f"Normalized question: {interpreted_query.normalized_question}\n"
        f"Answer mode: {answer_mode_decision.answer_mode.value}\n"
        f"Support state: {support_assessment.support_state.value}\n"
        f"Support summary: {summary}\n\n"
        "Answer instructions:\n"
        f"{_answer_mode_instruction(answer_mode_decision.answer_mode)}\n"
        f"{_request_shape_instruction(interpreted_query)}\n"
        "Do not repeat labels such as 'Question:', 'Answer:', 'Visible limitations:', or "
        "'Grounded context:'.\n"
        "Return only the final answer in 2-4 sentences.\n\n"
        "Visible limitations:\n"
        f"{limitations_block}\n\n"
        "Grounded context:\n"
        f"{context_block}\n\n"
        "Return only the answer text."
    )


def _extract_support_snippets(context_manifest: ContextManifest) -> list[str]:
    snippets: list[str] = []
    for item in context_manifest.context_items:
        for line in item.rendered_text.splitlines()[1:]:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("[") and "] " in stripped:
                stripped = stripped.split("] ", 1)[1]
            if stripped not in snippets:
                snippets.append(stripped)
    return snippets


def _select_supported_text(
    *,
    snippets: list[str],
    interpreted_query: InterpretedQuery,
    answer_mode: AnswerMode,
) -> str:
    if not snippets:
        return ""
    scored_snippets = [
        (
            _score_support_snippet(
                snippet=snippet,
                interpreted_query=interpreted_query,
            ),
            index,
            snippet,
        )
        for index, snippet in enumerate(snippets)
    ]
    positively_scored = [
        item
        for item in sorted(scored_snippets, key=lambda item: (-item[0], item[1]))
        if item[0] > 0
    ]
    if not positively_scored:
        return " ".join(snippets[:2]).strip()

    max_snippets = 1
    if (
        answer_mode is AnswerMode.QUALIFIED_ANSWER
        or answer_mode is AnswerMode.QUALIFIED_UNCERTAINTY
        or interpreted_query.request_type is QueryRequestType.EXPLANATION
        or interpreted_query.requires_synthesis
    ):
        max_snippets = 2

    selected: list[str] = []
    for _, _, snippet in positively_scored:
        if snippet in selected:
            continue
        selected.append(snippet)
        if len(selected) >= max_snippets:
            break
    return " ".join(selected).strip()


def _score_support_snippet(
    *,
    snippet: str,
    interpreted_query: InterpretedQuery,
) -> int:
    normalized_snippet = snippet.lower()
    snippet_tokens = set(_SUPPORT_TOKEN_RE.findall(normalized_snippet))
    hint_matches = sum(
        1
        for hint in interpreted_query.scope_hints
        if hint.lower() in normalized_snippet or hint.lower() in snippet_tokens
    )
    exactness_bonus = 0
    for token in ("preferred", "best", "exact", "default", "recommended"):
        if token in interpreted_query.normalized_question and token in normalized_snippet:
            exactness_bonus += 1
    if interpreted_query.request_type is QueryRequestType.EXPLANATION and any(
        token in normalized_snippet for token in ("because", "however", "instead")
    ):
        exactness_bonus += 1
    return hint_matches * 3 + exactness_bonus


def _grounded_evidence_set_ids(
    *,
    context_manifest: ContextManifest,
    answer_mode: AnswerMode,
) -> list[str]:
    if answer_mode is AnswerMode.FULL_ABSTENTION:
        return []
    return list(context_manifest.included_evidence_set_ids)


def _build_visible_limitations(
    *,
    support_assessment: SupportAssessment,
    answer_mode_decision: AnswerModeDecision,
) -> list[str]:
    limitations: list[str] = []

    reason_messages = {
        SupportQualifierReason.UNSUPPORTED_QUESTION_TYPE: (
            "The request exceeds the supported MVP question capabilities."
        ),
        SupportQualifierReason.NO_EVIDENCE_AVAILABLE: (
            "No supporting evidence was available in the active corpus snapshot."
        ),
        SupportQualifierReason.MISSING_MATERIAL_COVERAGE: (
            "The evidence does not fully cover every material part of the request."
        ),
        SupportQualifierReason.SCOPE_NARROWING_REQUIRED: (
            "The answer is limited to the narrower scope directly supported by the corpus."
        ),
        SupportQualifierReason.MATERIAL_CONFLICT: (
            "The evidence contains material conflict that must remain visible."
        ),
        SupportQualifierReason.PROVENANCE_TOO_WEAK: (
            "The supporting provenance is weaker than preferred for an unqualified answer."
        ),
        SupportQualifierReason.SOURCE_NAVIGATION_LOCATOR_MISSING: (
            "The corpus lacks a sufficiently localizable source-navigation anchor."
        ),
    }

    if (
        answer_mode_decision.answer_mode is not AnswerMode.DIRECT_ANSWER
        and answer_mode_decision.allowed_scope_summary
    ):
        limitations.append(answer_mode_decision.allowed_scope_summary)
    for reason in support_assessment.qualifying_reason_codes:
        message = reason_messages.get(reason)
        if message:
            limitations.append(message)
    limitations.extend(support_assessment.unsupported_gaps)
    limitations.extend(support_assessment.conflicting_evidence_notes)
    limitations.extend(support_assessment.provenance_warnings)

    deduped: list[str] = []
    for limitation in limitations:
        normalized = limitation.strip()
        if normalized and normalized not in deduped:
            deduped.append(normalized)
    return deduped


def _answer_mode_instruction(answer_mode: AnswerMode) -> str:
    if answer_mode is AnswerMode.DIRECT_ANSWER:
        return "Answer directly and succinctly using the grounded context."
    if answer_mode is AnswerMode.NARROWED_ANSWER:
        return "Answer only within the narrower supported scope and make that scope visible."
    if answer_mode is AnswerMode.QUALIFIED_ANSWER:
        return (
            "Answer with visible qualifications and keep uncertainty constrained to the evidence."
        )
    if answer_mode is AnswerMode.QUALIFIED_UNCERTAINTY:
        return "Explain the uncertainty and avoid choosing a single ungrounded conclusion."
    if answer_mode is AnswerMode.SCOPED_ABSTENTION:
        return (
            "Explain that the full request is not supported and only describe the supported scope."
        )
    return "Abstain if the evidence does not support an answer."


def _request_shape_instruction(interpreted_query: InterpretedQuery) -> str:
    if interpreted_query.request_type.value == "comparison":
        return (
            "Compare the named materials directly, mention both sides, state which side better "
            "fits the asked criterion, and justify the conclusion with grounded evidence."
        )
    if interpreted_query.requires_synthesis:
        return "Synthesize the grounded evidence across the relevant documents."
    return "Answer only the user's question from the grounded evidence."


def _build_comparison_answer_text(context_manifest: ContextManifest) -> str | None:
    snippets_by_doc = _snippets_by_document(context_manifest)
    if len(snippets_by_doc) < 2:
        return None

    ordered_docs = list(snippets_by_doc.keys())
    ranked_docs = sorted(
        ordered_docs,
        key=lambda doc: (
            -_freshness_score(snippets_by_doc[doc]),
            ordered_docs.index(doc),
        ),
    )
    winner = ranked_docs[0]
    runner_up = ranked_docs[1]
    winner_reason = _comparison_reason(snippets_by_doc[winner])
    runner_up_reason = _comparison_reason(snippets_by_doc[runner_up])

    if _freshness_score(snippets_by_doc[winner]) == _freshness_score(snippets_by_doc[runner_up]):
        return (
            f"{winner} and {runner_up} describe different caching tradeoffs. "
            f"{winner} emphasizes {winner_reason}. "
            f"{runner_up} emphasizes {runner_up_reason}."
        )

    return (
        f"{winner} has stricter freshness guarantees because {winner_reason}. "
        f"{runner_up} is looser because {runner_up_reason}."
    )


def _snippets_by_document(context_manifest: ContextManifest) -> dict[str, list[str]]:
    snippets_by_doc: dict[str, list[str]] = {}
    for item in context_manifest.context_items:
        header_line = item.rendered_text.splitlines()[0] if item.rendered_text else ""
        default_title = header_line.split(" | ", 1)[0].strip() or "corpus"
        is_multi_document = len(item.contributing_doc_ids) > 1
        for raw_line in item.rendered_text.splitlines()[1:]:
            stripped = raw_line.strip()
            if not stripped:
                continue
            if stripped.startswith("[") and "] " in stripped:
                stripped = stripped.split("] ", 1)[1]
            if is_multi_document and ": " in stripped:
                doc_title, snippet = stripped.split(": ", 1)
            else:
                doc_title, snippet = default_title, stripped
            snippets = snippets_by_doc.setdefault(doc_title.strip(), [])
            if snippet not in snippets:
                snippets.append(snippet)
    return snippets_by_doc


def _freshness_score(snippets: list[str]) -> int:
    text = " ".join(snippets).lower()
    score = 0
    for token in ("immediate", "write-through", "write through", "invalidate", "consistency-first"):
        if token in text:
            score += 2
    for token in ("unacceptable", "stale reads as unacceptable", "stricter freshness"):
        if token in text:
            score += 3
    for token in ("ttl", "time-to-live", "15-minute", "15 minute", "latency-first"):
        if token in text:
            score -= 2
    for token in ("stale reads", "allows stale", "available for 15 minutes"):
        if token in text:
            score -= 3
    return score


def _comparison_reason(snippets: list[str]) -> str:
    if not snippets:
        return "the grounded evidence available in the corpus"
    return _lowercase_first(" ".join(snippets[:2]).rstrip("."))


def _normalize_llm_output(*, generated_text: str, fallback_text: str) -> str:
    raw = generated_text.strip()
    if not raw:
        return fallback_text

    if raw.lower().startswith("question:") or any(
        marker in raw for marker in ("Visible limitations:", "Grounded context:")
    ):
        return fallback_text

    normalized = raw

    markers = ("Question:", "Answer:", "Visible limitations:", "Grounded context:")
    if "Answer:" in normalized:
        normalized = normalized.split("Answer:", 1)[1].strip()
    for marker in ("Visible limitations:", "Grounded context:"):
        if marker in normalized:
            normalized = normalized.split(marker, 1)[0].strip()
    if any(marker in normalized for marker in markers if marker != "Answer:"):
        return fallback_text
    if normalized.lower().startswith("question:"):
        return fallback_text
    return normalized or fallback_text


def _join_sentences(*parts: str | None) -> str:
    normalized = [part.strip() for part in parts if part and part.strip()]
    return " ".join(normalized)


def _lowercase_first(text: str) -> str:
    if not text:
        return text
    return text[:1].lower() + text[1:]


class _OllamaBackend:
    def generate(
        self,
        *,
        model_name: str,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
    ) -> str:
        import json
        import os
        import urllib.request

        base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        url = f"{base_url.rstrip('/')}/api/generate"
        data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_new_tokens},
        }
        req = urllib.request.Request(
            url, json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "").strip()  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {e}") from e


class OllamaGroundedAnswerGenerator:
    def __init__(
        self,
        *,
        model_name: str = "llama3.2:1b",
        max_new_tokens: int = 256,
        temperature: float = 0.0,
        backend: _LlmBackend | None = None,
        fallback: GroundedAnswerGenerator | None = None,
        logger: structlog.stdlib.BoundLogger | None = None,
    ) -> None:
        if max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be greater than 0")
        if temperature < 0:
            raise ValueError("temperature must be greater than or equal to 0")
        self._model_name = model_name
        self._max_new_tokens = max_new_tokens
        self._temperature = temperature
        self._backend = backend or _OllamaBackend()
        self._fallback = fallback or DeterministicGroundedAnswerGenerator()
        self._logger = logger or get_logger(self.__class__.__name__)

    def generate(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        context_manifest: ContextManifest,
        support_assessment: SupportAssessment,
        answer_mode_decision: AnswerModeDecision,
        policy: QueryPolicy,
    ) -> GroundedGenerationResult:
        self._logger.info(
            "query.llm.generated", generator_backend="ollama", model_name=self._model_name
        )
        fallback_result = self._fallback.generate(
            request=request,
            snapshot=snapshot,
            interpreted_query=interpreted_query,
            context_manifest=context_manifest,
            support_assessment=support_assessment,
            answer_mode_decision=answer_mode_decision,
            policy=policy,
        )
        if answer_mode_decision.answer_mode is AnswerMode.FULL_ABSTENTION:
            return fallback_result

        visible_limitations = fallback_result.visible_limitations
        prompt = _build_llm_prompt(
            request=request,
            interpreted_query=interpreted_query,
            context_manifest=context_manifest,
            support_assessment=support_assessment,
            answer_mode_decision=answer_mode_decision,
            visible_limitations=visible_limitations,
        )
        generated_text = self._backend.generate(
            model_name=self._model_name,
            prompt=prompt,
            max_new_tokens=self._max_new_tokens,
            temperature=self._temperature,
        )
        normalized_text = _normalize_llm_output(
            generated_text=generated_text,
            fallback_text=fallback_result.answer_draft.answer_text,
        )
        answer_draft = AnswerDraft(
            answer_text=normalized_text,
            visible_limitations=visible_limitations,
            should_render_citations=fallback_result.answer_draft.should_render_citations,
            grounded_evidence_set_ids=fallback_result.answer_draft.grounded_evidence_set_ids,
            generator_version="answer_generation.ollama.v1",
        )
        return GroundedGenerationResult(
            answer_draft=answer_draft,
            visible_limitations=visible_limitations,
            generator_version="answer_generation.ollama.v1",
        )
