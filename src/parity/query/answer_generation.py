"""Deterministic Stage-7 grounded answer generation helpers."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from functools import lru_cache
from typing import Protocol, cast

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    AnswerDraft,
    AnswerMode,
    AnswerModeDecision,
    ContextManifest,
    CorpusSnapshot,
    InterpretedQuery,
    QueryRequest,
    SupportAssessment,
    SupportQualifierReason,
    SupportState,
)
from .policies import QueryPolicy

GENERATOR_VERSION = "answer_generation.deterministic.v1"
MLX_GENERATOR_VERSION = "answer_generation.mlx.v1"


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
            "mlx-lm is not installed. Run `make sync-mac` or "
            "`uv sync --group llm --group mac` to enable Apple Silicon local generation."
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
    supported_text = " ".join(snippets[:2]).strip()
    if not supported_text and support_assessment.summary:
        supported_text = support_assessment.summary

    answer_mode = answer_mode_decision.answer_mode
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
        f"{_answer_mode_instruction(answer_mode_decision.answer_mode)}\n\n"
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


def _join_sentences(*parts: str | None) -> str:
    normalized = [part.strip() for part in parts if part and part.strip()]
    return " ".join(normalized)


def _lowercase_first(text: str) -> str:
    if not text:
        return text
    return text[:1].lower() + text[1:]
