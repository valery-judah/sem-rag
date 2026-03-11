"""Internal contracts for the staged query subsystem."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from parity._contracts import SourceReference


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


class QueryRunStatus(StrEnum):
    """Lifecycle status for an internal query run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class QueryStageName(StrEnum):
    """Semantic query runtime stages."""

    INTERPRET = "interpret"
    RETRIEVE = "retrieve"
    SELECT = "select"
    ASSEMBLE_CONTEXT = "assemble_context"
    ASSESS_SUPPORT = "assess_support"
    DECIDE_ANSWER_MODE = "decide_answer_mode"
    GENERATE = "generate"
    RENDER_CITATIONS = "render_citations"


class SupportState(StrEnum):
    """Support sufficiency states."""

    SUFFICIENT = "sufficient"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class AnswerMode(StrEnum):
    """Policy-selected answer posture."""

    DIRECT_ANSWER = "direct_answer"
    NARROWED_ANSWER = "narrowed_answer"
    QUALIFIED_ANSWER = "qualified_answer"
    FULL_ABSTENTION = "full_abstention"
    SCOPED_ABSTENTION = "scoped_abstention"
    QUALIFIED_UNCERTAINTY = "qualified_uncertainty"


class TrustFailureLabel(StrEnum):
    """Reserved trust-failure labels used by later stages and evals."""

    U1 = "U1"
    U2 = "U2"
    A1 = "A1"
    A2 = "A2"
    P1 = "P1"
    P2 = "P2"
    S1 = "S1"


class QueryRequestType(StrEnum):
    """High-level query intent family used by interpretation."""

    FACT_LOOKUP = "fact_lookup"
    EXPLANATION = "explanation"
    SYNTHESIS = "synthesis"
    SOURCE_NAVIGATION = "source_navigation"
    COMPARISON = "comparison"
    UNSUPPORTED = "unsupported"


class EvidenceGroupingMode(StrEnum):
    """Evidence grouping strategies for later selection stages."""

    SINGLE_PASSAGE = "single_passage"
    PASSAGE_WITH_NEIGHBOR = "passage_with_neighbor"
    SAME_DOCUMENT_MULTI_PASSAGE = "same_document_multi_passage"
    MULTI_DOCUMENT = "multi_document"


class CitationSupportRole(StrEnum):
    """Role a citation plays in the final answer."""

    PRIMARY = "primary"
    SUPPORTING = "supporting"
    CONTEXT = "context"


class DuplicateSuppressionMode(StrEnum):
    """Deterministic duplicate suppression strategies."""

    EXACT_SPAN = "exact_span"
    HEADING_AND_LOCATOR = "heading_and_locator"


class QueryPolicyOverride(BaseModel):
    """Internal per-request override surface for query policy defaults."""

    model_config = ConfigDict(extra="forbid")

    retrieval_candidate_cap: int | None = Field(default=None, ge=1)
    evidence_set_cap: int | None = Field(default=None, ge=1)
    neighbor_expansion_enabled: bool | None = None
    neighbor_expansion_cap: int | None = Field(default=None, ge=0)
    duplicate_suppression_mode: DuplicateSuppressionMode | None = None
    context_token_budget: int | None = Field(default=None, ge=1)
    deterministic_tie_break_order: tuple[str, ...] | None = None
    citation_include_heading_path: bool | None = None
    citation_include_locator: bool | None = None


class QueryRequest(BaseModel):
    """Internal query request envelope."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    policy_overrides: QueryPolicyOverride | None = None


class QueryRun(BaseModel):
    """Internal record for a query run."""

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    submitted_at: datetime = Field(default_factory=utc_now)
    status: QueryRunStatus = QueryRunStatus.PENDING
    policy_snapshot: dict[str, object]


class CorpusSnapshot(BaseModel):
    """Stable corpus boundary captured at query start."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1)
    query_started_at: datetime = Field(default_factory=utc_now)
    eligible_doc_ids: list[str] = Field(default_factory=list)
    retrieval_index_version: str | None = None
    readiness_version: str | None = None


class InterpretedQuery(BaseModel):
    """Structured interpretation output consumed by downstream stages."""

    model_config = ConfigDict(extra="forbid")

    normalized_question: str = Field(min_length=1)
    request_type: QueryRequestType
    answer_shape: str = Field(min_length=1)
    scope_hints: list[str] = Field(default_factory=list)
    requires_synthesis: bool = False
    requires_source_navigation: bool = False
    unsupported_question_type_signal: str | None = None


class RetrievedCandidate(BaseModel):
    """Provenance-preserving retrieval candidate contract."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    section_id: str | None = None
    heading_path: list[str] = Field(min_length=1)
    locator: str | None = None
    retrieval_score: float
    retrieval_rank: int = Field(ge=1)


class EvidenceUnit(BaseModel):
    """Minimal provenance-bearing support unit used by evidence grouping."""

    model_config = ConfigDict(extra="forbid")

    evidence_unit_id: str = Field(min_length=1)
    candidate: RetrievedCandidate
    source_reference: SourceReference


class EvidenceSet(BaseModel):
    """Explicit evidence grouping prepared for later context assembly."""

    model_config = ConfigDict(extra="forbid")

    evidence_set_id: str = Field(min_length=1)
    grouping_mode: EvidenceGroupingMode
    evidence_units: list[EvidenceUnit] = Field(min_length=1)
    rationale: str = Field(min_length=1)


class ContextManifest(BaseModel):
    """Deterministic, inspectable model-facing context description."""

    model_config = ConfigDict(extra="forbid")

    ordered_evidence_set_ids: list[str] = Field(default_factory=list)
    dropped_evidence_set_ids: list[str] = Field(default_factory=list)
    inclusion_reasons: dict[str, str] = Field(default_factory=dict)
    exclusion_reasons: dict[str, str] = Field(default_factory=dict)
    token_budget: int = Field(ge=1)
    token_budget_used: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_budget(self) -> ContextManifest:
        if self.token_budget_used > self.token_budget:
            raise ValueError("token_budget_used must not exceed token_budget")
        return self


class SupportAssessment(BaseModel):
    """Structured support judgment for a query run."""

    model_config = ConfigDict(extra="forbid")

    support_state: SupportState
    qualifying_reasons: list[str] = Field(default_factory=list)
    trust_failure_labels: list[TrustFailureLabel] = Field(default_factory=list)
    summary: str | None = None


class AnswerModeDecision(BaseModel):
    """Policy-selected answer mode and its justification."""

    model_config = ConfigDict(extra="forbid")

    answer_mode: AnswerMode
    rationale: str = Field(min_length=1)
    based_on_support_state: SupportState


class AnswerDraft(BaseModel):
    """Generated answer text plus visible limitation hints."""

    model_config = ConfigDict(extra="forbid")

    answer_text: str = Field(min_length=1)
    visible_limitations: list[str] = Field(default_factory=list)
    should_render_citations: bool = True


class CitationRecord(BaseModel):
    """Single citation plus its support role."""

    model_config = ConfigDict(extra="forbid")

    source_reference: SourceReference
    support_role: CitationSupportRole


class CitationBundle(BaseModel):
    """Bundle of provenance-derived citations for an answer."""

    model_config = ConfigDict(extra="forbid")

    citations: list[CitationRecord] = Field(default_factory=list)
    renderer_version: str | None = None
