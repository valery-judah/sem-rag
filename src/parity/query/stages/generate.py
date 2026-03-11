"""Stage-7 grounded answer generation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from parity.query.answer_generation import GroundedAnswerGenerator, GroundedGenerationResult
from parity.query.contracts import (
    AnswerDraft,
    AnswerMode,
    AnswerModeDecision,
    ContextManifest,
    CorpusSnapshot,
    InterpretedQuery,
    QueryRequest,
    QueryStageName,
    SupportAssessment,
    SupportState,
)
from parity.query.policies import QueryPolicy
from parity.query.trace import QueryStageTrace, QueryStageTraceStatus, utc_now

STAGE_NAME = QueryStageName.GENERATE


class GenerateStageResult(BaseModel):
    """Structured result of the grounded-generation stage."""

    model_config = ConfigDict(extra="forbid")

    generation: GroundedGenerationResult
    trace: QueryStageTrace


class GenerateTracePayload(BaseModel):
    """Structured trace payload for Stage 7 grounded generation."""

    model_config = ConfigDict(extra="forbid")

    based_on_support_state: SupportState
    based_on_answer_mode: AnswerMode
    visible_limitations: list[str] = Field(default_factory=list)
    grounded_evidence_set_ids: list[str] = Field(default_factory=list)
    answer_text: str = Field(min_length=1)
    should_render_citations: bool
    generator_version: str = Field(min_length=1)


def run(
    *,
    query_id: str,
    request: QueryRequest,
    snapshot: CorpusSnapshot,
    interpreted_query: InterpretedQuery,
    context_manifest: ContextManifest,
    support_assessment: SupportAssessment,
    answer_mode_decision: AnswerModeDecision,
    policy: QueryPolicy,
    generator: GroundedAnswerGenerator,
) -> GenerateStageResult:
    """Render grounded answer text without widening beyond Stage 6 posture."""

    started_at = utc_now()
    generation = generator.generate(
        request=request,
        snapshot=snapshot,
        interpreted_query=interpreted_query,
        context_manifest=context_manifest,
        support_assessment=support_assessment,
        answer_mode_decision=answer_mode_decision,
        policy=policy,
    )
    finished_at = utc_now()
    answer_draft: AnswerDraft = generation.answer_draft
    payload = GenerateTracePayload(
        based_on_support_state=answer_mode_decision.based_on_support_state,
        based_on_answer_mode=answer_mode_decision.answer_mode,
        visible_limitations=answer_draft.visible_limitations,
        grounded_evidence_set_ids=answer_draft.grounded_evidence_set_ids,
        answer_text=answer_draft.answer_text,
        should_render_citations=answer_draft.should_render_citations,
        generator_version=generation.generator_version,
    )
    trace = QueryStageTrace(
        query_id=query_id,
        stage_name=STAGE_NAME,
        stage_status=QueryStageTraceStatus.SUCCEEDED,
        started_at=started_at,
        finished_at=finished_at,
        payload=payload.model_dump(mode="json"),
    )
    return GenerateStageResult(generation=generation, trace=trace)
