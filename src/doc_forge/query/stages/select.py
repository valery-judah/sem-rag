"""Stage-4 query selection and evidence-set construction."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from doc_forge.identifiers import QueryId
from doc_forge.query.contracts import (
    CorpusSnapshot,
    EvidenceSet,
    InterpretedQuery,
    QueryRequest,
    QueryStageName,
    RetrievedCandidate,
)
from doc_forge.query.policies import QueryPolicy
from doc_forge.query.selection import QuerySelector, SelectionDecision, SelectionResult
from doc_forge.query.trace import QueryStageTrace, QueryStageTraceStatus, utc_now

STAGE_NAME = QueryStageName.SELECT


class SelectionStageResult(BaseModel):
    """Structured result of the selection stage."""

    model_config = ConfigDict(extra="forbid")

    selection: SelectionResult
    trace: QueryStageTrace


class SelectionTracePayload(BaseModel):
    """Structured trace payload for Stage 4 selection."""

    model_config = ConfigDict(extra="forbid")

    interpreted_query: InterpretedQuery
    snapshot_doc_ids: list[str] = Field(default_factory=list)
    retrieved_candidate_count: int = Field(ge=0)
    selected_candidates: list[RetrievedCandidate] = Field(default_factory=list)
    decisions: list[SelectionDecision] = Field(default_factory=list)
    evidence_sets: list[EvidenceSet] = Field(default_factory=list)
    duplicate_suppression_mode: str = Field(min_length=1)
    duplicate_suppression_notes: list[str] = Field(default_factory=list)
    neighbor_expansion_enabled: bool
    neighbor_expansion_cap: int = Field(ge=0)
    neighbor_expansion_notes: list[dict[str, object]] = Field(default_factory=list)
    evidence_set_cap: int = Field(ge=1)


def run(
    *,
    query_id: QueryId,
    request: QueryRequest,
    snapshot: CorpusSnapshot,
    interpreted_query: InterpretedQuery,
    retrieved_candidates: list[RetrievedCandidate],
    policy: QueryPolicy,
    selector: QuerySelector,
) -> SelectionStageResult:
    """Select and group evidence structures from retrieved candidates."""

    started_at = utc_now()
    selection = selector.select(
        request=request,
        snapshot=snapshot,
        interpreted_query=interpreted_query,
        retrieved_candidates=retrieved_candidates,
        policy=policy,
    )
    finished_at = utc_now()
    payload = SelectionTracePayload(
        interpreted_query=interpreted_query,
        snapshot_doc_ids=snapshot.eligible_doc_ids,
        retrieved_candidate_count=len(retrieved_candidates),
        selected_candidates=selection.selected_candidates,
        decisions=selection.decisions,
        evidence_sets=selection.evidence_sets,
        duplicate_suppression_mode=policy.duplicate_suppression_mode.value,
        duplicate_suppression_notes=selection.duplicate_suppression_notes,
        neighbor_expansion_enabled=policy.neighbor_expansion_enabled,
        neighbor_expansion_cap=policy.neighbor_expansion_cap,
        neighbor_expansion_notes=[
            note.model_dump(mode="json") for note in selection.neighbor_expansion_notes
        ],
        evidence_set_cap=policy.evidence_set_cap,
    )
    trace = QueryStageTrace(
        query_id=query_id,
        stage_name=STAGE_NAME,
        stage_status=QueryStageTraceStatus.SUCCEEDED,
        started_at=started_at,
        finished_at=finished_at,
        payload=payload.model_dump(mode="json"),
    )
    return SelectionStageResult(selection=selection, trace=trace)
