"""Stage-6 answer-mode decision."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from doc_forge.query.answer_mode_policy import AnswerModePolicy, AnswerModePolicyDecision
from doc_forge.query.contracts import (
    AnswerModeDecision,
    CorpusSnapshot,
    InterpretedQuery,
    QueryRequest,
    QueryStageName,
    SupportAssessment,
    SupportQualifierReason,
    SupportState,
)
from doc_forge.query.policies import QueryPolicy
from doc_forge.query.trace import QueryStageTrace, QueryStageTraceStatus, utc_now

STAGE_NAME = QueryStageName.DECIDE_ANSWER_MODE


class AnswerModeDecisionStageResult(BaseModel):
    """Structured result of the answer-mode stage."""

    model_config = ConfigDict(extra="forbid")

    answer_mode_policy: AnswerModePolicyDecision
    trace: QueryStageTrace


class AnswerModeDecisionTracePayload(BaseModel):
    """Structured trace payload for Stage 6 answer-mode policy."""

    model_config = ConfigDict(extra="forbid")

    based_on_support_state: SupportState
    qualifying_reason_codes: list[SupportQualifierReason] = Field(default_factory=list)
    baseline_answer_mode: str = Field(min_length=1)
    applied_override_rules: list[str] = Field(default_factory=list)
    final_answer_mode: str = Field(min_length=1)
    allowed_scope_summary: str | None = None
    must_surface_conflict: bool
    policy_version: str = Field(min_length=1)


def run(
    *,
    query_id: str,
    request: QueryRequest,
    snapshot: CorpusSnapshot,
    interpreted_query: InterpretedQuery,
    support_assessment: SupportAssessment,
    policy: QueryPolicy,
    answer_mode_policy: AnswerModePolicy,
) -> AnswerModeDecisionStageResult:
    """Choose the allowed answer posture from the assessed support state."""

    started_at = utc_now()
    answer_mode_result = answer_mode_policy.decide(
        request=request,
        snapshot=snapshot,
        interpreted_query=interpreted_query,
        support_assessment=support_assessment,
        policy=policy,
    )
    finished_at = utc_now()
    decision: AnswerModeDecision = answer_mode_result.decision
    payload = AnswerModeDecisionTracePayload(
        based_on_support_state=decision.based_on_support_state,
        qualifying_reason_codes=support_assessment.qualifying_reason_codes,
        baseline_answer_mode=answer_mode_result.baseline_answer_mode.value,
        applied_override_rules=answer_mode_result.applied_override_rules,
        final_answer_mode=decision.answer_mode.value,
        allowed_scope_summary=decision.allowed_scope_summary,
        must_surface_conflict=decision.must_surface_conflict,
        policy_version=answer_mode_result.policy_version,
    )
    trace = QueryStageTrace(
        query_id=query_id,
        stage_name=STAGE_NAME,
        stage_status=QueryStageTraceStatus.SUCCEEDED,
        started_at=started_at,
        finished_at=finished_at,
        payload=payload.model_dump(mode="json"),
    )
    return AnswerModeDecisionStageResult(answer_mode_policy=answer_mode_result, trace=trace)
