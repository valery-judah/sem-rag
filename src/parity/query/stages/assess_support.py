"""Stage-6 support assessment."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from parity.query.contracts import (
    ContextManifest,
    CorpusSnapshot,
    EvidenceSet,
    InterpretedQuery,
    QueryRequest,
    QueryStageName,
    SupportAssessment,
    SupportState,
)
from parity.query.policies import QueryPolicy
from parity.query.support_assessment import (
    HybridSupportAssessor,
    StructuredSupportJudgment,
    SupportAssessmentPrecheck,
    SupportAssessmentResult,
)
from parity.query.trace import QueryStageTrace, QueryStageTraceStatus, utc_now

STAGE_NAME = QueryStageName.ASSESS_SUPPORT


class SupportAssessmentStageResult(BaseModel):
    """Structured result of the support-assessment stage."""

    model_config = ConfigDict(extra="forbid")

    support_assessment: SupportAssessmentResult
    trace: QueryStageTrace


class SupportAssessmentTracePayload(BaseModel):
    """Structured trace payload for Stage 6 support assessment."""

    model_config = ConfigDict(extra="forbid")

    interpreted_query: InterpretedQuery
    snapshot_doc_ids: list[str] = Field(default_factory=list)
    evidence_set_ids: list[str] = Field(default_factory=list)
    included_evidence_set_ids: list[str] = Field(default_factory=list)
    precheck_results: list[SupportAssessmentPrecheck] = Field(default_factory=list)
    support_ceiling: SupportState | None = None
    structured_judgment: StructuredSupportJudgment | None = None
    qualifying_reason_codes: list[str] = Field(default_factory=list)
    summary: str | None = None
    unsupported_gaps: list[str] = Field(default_factory=list)
    conflicting_evidence_notes: list[str] = Field(default_factory=list)
    provenance_warnings: list[str] = Field(default_factory=list)
    trust_failure_labels: list[str] = Field(default_factory=list)
    final_support_state: SupportState
    support_assessment_policy_version: str = Field(min_length=1)


def run(
    *,
    query_id: str,
    request: QueryRequest,
    snapshot: CorpusSnapshot,
    interpreted_query: InterpretedQuery,
    evidence_sets: list[EvidenceSet],
    context_manifest: ContextManifest,
    policy: QueryPolicy,
    assessor: HybridSupportAssessor,
) -> SupportAssessmentStageResult:
    """Assess support sufficiency over the assembled context."""

    started_at = utc_now()
    support_assessment = assessor.assess(
        request=request,
        snapshot=snapshot,
        interpreted_query=interpreted_query,
        evidence_sets=evidence_sets,
        context_manifest=context_manifest,
        policy=policy,
    )
    finished_at = utc_now()
    assessment: SupportAssessment = support_assessment.assessment
    payload = SupportAssessmentTracePayload(
        interpreted_query=interpreted_query,
        snapshot_doc_ids=snapshot.eligible_doc_ids,
        evidence_set_ids=[evidence_set.evidence_set_id for evidence_set in evidence_sets],
        included_evidence_set_ids=context_manifest.included_evidence_set_ids,
        precheck_results=support_assessment.precheck_results,
        support_ceiling=support_assessment.support_ceiling,
        structured_judgment=support_assessment.structured_judgment,
        qualifying_reason_codes=[reason.value for reason in assessment.qualifying_reason_codes],
        summary=assessment.summary,
        unsupported_gaps=assessment.unsupported_gaps,
        conflicting_evidence_notes=assessment.conflicting_evidence_notes,
        provenance_warnings=assessment.provenance_warnings,
        trust_failure_labels=[label.value for label in assessment.trust_failure_labels],
        final_support_state=assessment.support_state,
        support_assessment_policy_version=policy.support_assessment_policy_version,
    )
    trace = QueryStageTrace(
        query_id=query_id,
        stage_name=STAGE_NAME,
        stage_status=QueryStageTraceStatus.SUCCEEDED,
        started_at=started_at,
        finished_at=finished_at,
        payload=payload.model_dump(mode="json"),
    )
    return SupportAssessmentStageResult(support_assessment=support_assessment, trace=trace)
