"""Stage-5 deterministic context assembly."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from doc_forge.identifiers import QueryId
from doc_forge.query.context_assembly import (
    ContextAssembler,
    ContextAssemblyDecision,
    ContextAssemblyResult,
)
from doc_forge.query.contracts import (
    ContextItem,
    ContextManifest,
    CorpusSnapshot,
    EvidenceSet,
    InterpretedQuery,
    QueryRequest,
    QueryStageName,
)
from doc_forge.query.policies import QueryPolicy
from doc_forge.query.trace import QueryStageTrace, QueryStageTraceStatus, utc_now

STAGE_NAME = QueryStageName.ASSEMBLE_CONTEXT


class ContextAssemblyStageResult(BaseModel):
    """Structured result of the context-assembly stage."""

    model_config = ConfigDict(extra="forbid")

    context_assembly: ContextAssemblyResult
    trace: QueryStageTrace


class ContextAssemblyTracePayload(BaseModel):
    """Structured trace payload for Stage 5 context assembly."""

    model_config = ConfigDict(extra="forbid")

    interpreted_query: InterpretedQuery
    snapshot_doc_ids: list[str] = Field(default_factory=list)
    evidence_set_ids: list[str] = Field(default_factory=list)
    ordered_evidence_set_ids: list[str] = Field(default_factory=list)
    token_budget: int = Field(ge=1)
    token_budget_used: int = Field(ge=0)
    included_evidence_set_ids: list[str] = Field(default_factory=list)
    dropped_evidence_set_ids: list[str] = Field(default_factory=list)
    inclusion_reasons: dict[str, str] = Field(default_factory=dict)
    exclusion_reasons: dict[str, str] = Field(default_factory=dict)
    duplicate_suppression_notes: list[str] = Field(default_factory=list)
    context_items: list[ContextItem] = Field(default_factory=list)
    decisions: list[ContextAssemblyDecision] = Field(default_factory=list)


def run(
    *,
    query_id: QueryId,
    request: QueryRequest,
    snapshot: CorpusSnapshot,
    interpreted_query: InterpretedQuery,
    evidence_sets: list[EvidenceSet],
    policy: QueryPolicy,
    assembler: ContextAssembler,
) -> ContextAssemblyStageResult:
    """Assemble a deterministic context manifest from selected evidence sets."""

    started_at = utc_now()
    context_assembly = assembler.assemble(
        request=request,
        snapshot=snapshot,
        interpreted_query=interpreted_query,
        evidence_sets=evidence_sets,
        policy=policy,
    )
    finished_at = utc_now()
    manifest: ContextManifest = context_assembly.manifest
    payload = ContextAssemblyTracePayload(
        interpreted_query=interpreted_query,
        snapshot_doc_ids=snapshot.eligible_doc_ids,
        evidence_set_ids=[evidence_set.evidence_set_id for evidence_set in evidence_sets],
        ordered_evidence_set_ids=manifest.ordered_evidence_set_ids,
        token_budget=manifest.token_budget,
        token_budget_used=manifest.token_budget_used,
        included_evidence_set_ids=manifest.included_evidence_set_ids,
        dropped_evidence_set_ids=manifest.dropped_evidence_set_ids,
        inclusion_reasons=manifest.inclusion_reasons,
        exclusion_reasons=manifest.exclusion_reasons,
        duplicate_suppression_notes=manifest.duplicate_suppression_notes,
        context_items=manifest.context_items,
        decisions=context_assembly.decisions,
    )
    trace = QueryStageTrace(
        query_id=query_id,
        stage_name=STAGE_NAME,
        stage_status=QueryStageTraceStatus.SUCCEEDED,
        started_at=started_at,
        finished_at=finished_at,
        payload=payload.model_dump(mode="json"),
    )
    return ContextAssemblyStageResult(context_assembly=context_assembly, trace=trace)
