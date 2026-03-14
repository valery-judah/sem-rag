"""Stage-7 citation rendering."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from doc_forge.identifiers import QueryId
from doc_forge.query.citation_rendering import CitationRenderer, CitationRenderingResult
from doc_forge.query.contracts import (
    AnswerDraft,
    AnswerModeDecision,
    CitationBundle,
    ContextManifest,
    CorpusSnapshot,
    EvidenceSet,
    InterpretedQuery,
    QueryRequest,
    QueryStageName,
    SupportAssessment,
)
from doc_forge.query.policies import QueryPolicy
from doc_forge.query.trace import QueryStageTrace, QueryStageTraceStatus, utc_now

STAGE_NAME = QueryStageName.RENDER_CITATIONS


class RenderCitationsStageResult(BaseModel):
    """Structured result of the citation-rendering stage."""

    model_config = ConfigDict(extra="forbid")

    rendering: CitationRenderingResult
    trace: QueryStageTrace


class RenderCitationsTracePayload(BaseModel):
    """Structured trace payload for Stage 7 citation rendering."""

    model_config = ConfigDict(extra="forbid")

    grounded_evidence_set_ids: list[str] = Field(default_factory=list)
    citation_count: int = Field(ge=0)
    citation_doc_ids: list[str] = Field(default_factory=list)
    citation_support_roles: list[str] = Field(default_factory=list)
    provenance_warnings: list[str] = Field(default_factory=list)
    renderer_version: str = Field(min_length=1)


def run(
    *,
    query_id: QueryId,
    request: QueryRequest,
    snapshot: CorpusSnapshot,
    interpreted_query: InterpretedQuery,
    evidence_sets: list[EvidenceSet],
    context_manifest: ContextManifest,
    support_assessment: SupportAssessment,
    answer_mode_decision: AnswerModeDecision,
    answer_draft: AnswerDraft,
    policy: QueryPolicy,
    renderer: CitationRenderer,
) -> RenderCitationsStageResult:
    """Render citations from stored provenance only."""

    del request, snapshot
    started_at = utc_now()
    rendering = renderer.render(
        interpreted_query=interpreted_query,
        evidence_sets=evidence_sets,
        context_manifest=context_manifest,
        support_assessment=support_assessment,
        answer_mode_decision=answer_mode_decision,
        answer_draft=answer_draft,
        policy=policy,
    )
    finished_at = utc_now()
    citation_bundle: CitationBundle = rendering.citation_bundle
    payload = RenderCitationsTracePayload(
        grounded_evidence_set_ids=answer_draft.grounded_evidence_set_ids,
        citation_count=len(citation_bundle.citations),
        citation_doc_ids=citation_bundle.material_doc_ids,
        citation_support_roles=[
            citation.support_role.value for citation in citation_bundle.citations
        ],
        provenance_warnings=rendering.provenance_warnings,
        renderer_version=rendering.renderer_version,
    )
    trace = QueryStageTrace(
        query_id=query_id,
        stage_name=STAGE_NAME,
        stage_status=QueryStageTraceStatus.SUCCEEDED,
        started_at=started_at,
        finished_at=finished_at,
        payload=payload.model_dump(mode="json"),
    )
    return RenderCitationsStageResult(rendering=rendering, trace=trace)
