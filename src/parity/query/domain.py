"""Query-domain runtime state objects."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    AnswerDraft,
    AnswerModeDecision,
    CitationBundle,
    ContextManifest,
    CorpusSnapshot,
    EvidenceSet,
    InterpretedQuery,
    QueryRequest,
    QueryRun,
    RetrievedCandidate,
    SupportAssessment,
)


class QueryRuntimeState(BaseModel):
    """Internal runtime state threaded through the staged query lifecycle."""

    model_config = ConfigDict(extra="forbid")

    request: QueryRequest
    run: QueryRun
    snapshot: CorpusSnapshot | None = None
    interpreted_query: InterpretedQuery | None = None
    retrieved_candidates: list[RetrievedCandidate] = Field(default_factory=list)
    evidence_sets: list[EvidenceSet] = Field(default_factory=list)
    context_manifest: ContextManifest | None = None
    support_assessment: SupportAssessment | None = None
    answer_mode_decision: AnswerModeDecision | None = None
    answer_draft: AnswerDraft | None = None
    citation_bundle: CitationBundle | None = None
