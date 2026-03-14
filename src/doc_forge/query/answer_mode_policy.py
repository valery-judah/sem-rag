"""Deterministic Stage-6 answer-mode policy helpers."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    AnswerMode,
    AnswerModeDecision,
    CorpusSnapshot,
    InterpretedQuery,
    QueryRequest,
    QueryRequestType,
    QuerySpecificity,
    SupportAssessment,
    SupportQualifierReason,
    SupportState,
)
from .policies import QueryPolicy


class AnswerModePolicyDecision(BaseModel):
    """Structured answer-mode policy result plus trace metadata."""

    model_config = ConfigDict(extra="forbid")

    decision: AnswerModeDecision
    baseline_answer_mode: AnswerMode
    applied_override_rules: list[str] = Field(default_factory=lambda: [])
    policy_version: str = Field(min_length=1)


class AnswerModePolicy(Protocol):
    """Deterministic answer-mode policy seam."""

    def decide(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        support_assessment: SupportAssessment,
        policy: QueryPolicy,
    ) -> AnswerModePolicyDecision:
        """Return the answer-mode decision allowed by current support."""
        ...


class DeterministicAnswerModePolicy:
    """Stage-6 deterministic answer-mode policy."""

    def decide(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        support_assessment: SupportAssessment,
        policy: QueryPolicy,
    ) -> AnswerModePolicyDecision:
        del request, snapshot
        baseline = policy.answer_mode_by_support_state[support_assessment.support_state]
        reasons = set(support_assessment.qualifying_reason_codes)
        applied_rules: list[str] = []
        influenced_reasons: list[SupportQualifierReason] = []
        answer_mode = baseline

        if SupportQualifierReason.UNSUPPORTED_QUESTION_TYPE in reasons:
            answer_mode = AnswerMode.FULL_ABSTENTION
            applied_rules.append("unsupported_question_type_abstains")
            influenced_reasons.append(SupportQualifierReason.UNSUPPORTED_QUESTION_TYPE)
        elif (
            support_assessment.support_state is SupportState.INSUFFICIENT
            and SupportQualifierReason.NO_EVIDENCE_AVAILABLE in reasons
        ):
            answer_mode = AnswerMode.FULL_ABSTENTION
            applied_rules.append("empty_evidence_abstains")
            influenced_reasons.append(SupportQualifierReason.NO_EVIDENCE_AVAILABLE)
        elif (
            support_assessment.support_state is SupportState.INSUFFICIENT
            and SupportQualifierReason.SOURCE_NAVIGATION_LOCATOR_MISSING in reasons
        ):
            answer_mode = AnswerMode.SCOPED_ABSTENTION
            applied_rules.append("source_navigation_locator_missing_scopes_abstention")
            influenced_reasons.append(SupportQualifierReason.SOURCE_NAVIGATION_LOCATOR_MISSING)
        elif SupportQualifierReason.MATERIAL_CONFLICT in reasons:
            answer_mode = AnswerMode.QUALIFIED_UNCERTAINTY
            applied_rules.append("material_conflict_requires_uncertainty")
            influenced_reasons.append(SupportQualifierReason.MATERIAL_CONFLICT)
        elif (
            SupportQualifierReason.PROVENANCE_TOO_WEAK in reasons
            and interpreted_query.requires_source_navigation
        ):
            answer_mode = AnswerMode.SCOPED_ABSTENTION
            applied_rules.append("weak_source_navigation_provenance_scopes_abstention")
            influenced_reasons.append(SupportQualifierReason.PROVENANCE_TOO_WEAK)
        elif SupportQualifierReason.SCOPE_NARROWING_REQUIRED in reasons and (
            interpreted_query.specificity is QuerySpecificity.PRECISE
            or interpreted_query.requires_source_navigation
            or interpreted_query.request_type is QueryRequestType.FACT_LOOKUP
        ):
            answer_mode = AnswerMode.NARROWED_ANSWER
            applied_rules.append("scope_narrowing_requires_narrowed_answer")
            influenced_reasons.append(SupportQualifierReason.SCOPE_NARROWING_REQUIRED)

        answer_mode = _enforce_allowed_answer_mode(
            answer_mode=answer_mode,
            baseline=baseline,
            support_state=support_assessment.support_state,
        )
        must_surface_conflict = SupportQualifierReason.MATERIAL_CONFLICT in reasons
        decision = AnswerModeDecision(
            answer_mode=answer_mode,
            rationale=_build_rationale(
                answer_mode, support_assessment.support_state, applied_rules
            ),
            based_on_support_state=support_assessment.support_state,
            required_qualifying_reason_codes=influenced_reasons,
            allowed_scope_summary=_build_allowed_scope_summary(answer_mode, support_assessment),
            must_surface_conflict=must_surface_conflict,
        )
        return AnswerModePolicyDecision(
            decision=decision,
            baseline_answer_mode=baseline,
            applied_override_rules=applied_rules,
            policy_version=policy.answer_mode_policy_version,
        )


def _enforce_allowed_answer_mode(
    *,
    answer_mode: AnswerMode,
    baseline: AnswerMode,
    support_state: SupportState,
) -> AnswerMode:
    allowed_by_support_state = {
        SupportState.SUFFICIENT: {
            AnswerMode.DIRECT_ANSWER,
            AnswerMode.NARROWED_ANSWER,
            AnswerMode.QUALIFIED_ANSWER,
            AnswerMode.QUALIFIED_UNCERTAINTY,
            AnswerMode.SCOPED_ABSTENTION,
            AnswerMode.FULL_ABSTENTION,
        },
        SupportState.PARTIAL: {
            AnswerMode.NARROWED_ANSWER,
            AnswerMode.QUALIFIED_ANSWER,
            AnswerMode.QUALIFIED_UNCERTAINTY,
            AnswerMode.SCOPED_ABSTENTION,
            AnswerMode.FULL_ABSTENTION,
        },
        SupportState.INSUFFICIENT: {
            AnswerMode.SCOPED_ABSTENTION,
            AnswerMode.FULL_ABSTENTION,
        },
    }
    return answer_mode if answer_mode in allowed_by_support_state[support_state] else baseline


def _build_rationale(
    answer_mode: AnswerMode,
    support_state: SupportState,
    applied_rules: list[str],
) -> str:
    if applied_rules:
        return f"Applied Stage 6 policy rules: {', '.join(applied_rules)}."
    if answer_mode is AnswerMode.DIRECT_ANSWER and support_state is SupportState.SUFFICIENT:
        return "Sufficient support allows a direct answer."
    if answer_mode is AnswerMode.QUALIFIED_ANSWER and support_state is SupportState.PARTIAL:
        return "Partial support requires visible qualification."
    if answer_mode is AnswerMode.FULL_ABSTENTION and support_state is SupportState.INSUFFICIENT:
        return "Insufficient support requires abstention."
    return "The answer mode is constrained by the assessed support state."


def _build_allowed_scope_summary(
    answer_mode: AnswerMode,
    support_assessment: SupportAssessment,
) -> str:
    if answer_mode is AnswerMode.DIRECT_ANSWER:
        return "A direct answer may stay within the supported scope of the assembled evidence."
    if answer_mode is AnswerMode.NARROWED_ANSWER:
        return "Only the supported subpart of the request may be answered."
    if answer_mode is AnswerMode.QUALIFIED_ANSWER:
        return "Any answer must surface the unsupported gaps and remain qualified."
    if answer_mode is AnswerMode.QUALIFIED_UNCERTAINTY:
        return "Any answer must surface the material conflict or uncertainty explicitly."
    if answer_mode is AnswerMode.SCOPED_ABSTENTION:
        return (
            "The full request should be declined while preserving a clearly "
            "narrower supported scope."
        )
    if support_assessment.summary:
        return support_assessment.summary
    return "The full request should be declined because the current evidence does not support it."
