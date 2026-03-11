"""Deterministic Stage-7 grounded answer generation helpers."""

from __future__ import annotations

from typing import Protocol

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


def _join_sentences(*parts: str | None) -> str:
    normalized = [part.strip() for part in parts if part and part.strip()]
    return " ".join(normalized)


def _lowercase_first(text: str) -> str:
    if not text:
        return text
    return text[:1].lower() + text[1:]
