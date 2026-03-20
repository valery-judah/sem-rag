"""Internal contracts for the staged query subsystem."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from doc_forge.corpus import SourceReference
from doc_forge.identifiers import DocId, QueryId, WorkspaceId


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


class QueryRunStatus(StrEnum):
    """Lifecycle status for an internal query run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class QueryTerminalFailure(BaseModel):
    """Compact persisted summary for a terminal failed query run."""

    model_config = ConfigDict(extra="forbid")

    error_code: str = Field(min_length=1)
    error_class: str = Field(min_length=1)
    stage_name: QueryStageName | None = None
    message: str = Field(min_length=1)
    trust_failure_labels: list[TrustFailureLabel] = Field(default_factory=lambda: [])


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


class SupportQualifierReason(StrEnum):
    """Deterministic reason codes that narrow or block answer posture."""

    UNSUPPORTED_QUESTION_TYPE = "unsupported_question_type"
    NO_EVIDENCE_AVAILABLE = "no_evidence_available"
    MISSING_MATERIAL_COVERAGE = "missing_material_coverage"
    SCOPE_NARROWING_REQUIRED = "scope_narrowing_required"
    MATERIAL_CONFLICT = "material_conflict"
    PROVENANCE_TOO_WEAK = "provenance_too_weak"
    SOURCE_NAVIGATION_LOCATOR_MISSING = "source_navigation_locator_missing"


class QueryRequestType(StrEnum):
    """High-level query intent family used by interpretation."""

    FACT_LOOKUP = "fact_lookup"
    EXPLANATION = "explanation"
    SYNTHESIS = "synthesis"
    SOURCE_NAVIGATION = "source_navigation"
    COMPARISON = "comparison"
    UNSUPPORTED = "unsupported"


class QuerySpecificity(StrEnum):
    """Interpretation-level specificity used by downstream retrieval policy."""

    PRECISE = "precise"
    SECTION_SCOPED = "section_scoped"
    BROAD = "broad"


class SynthesisMode(StrEnum):
    """Interpretation-level synthesis scope."""

    NONE = "none"
    SINGLE_DOCUMENT = "single_document"
    CROSS_DOCUMENT = "cross_document"


class UnsupportedCapability(StrEnum):
    """MVP capability boundaries surfaced during interpretation."""

    EXTERNAL_KNOWLEDGE = "external_knowledge"
    IMAGE_OR_FIGURE_REASONING = "image_or_figure_reasoning"
    TABLE_HEAVY_ANSWERING = "table_heavy_answering"
    OCR_REQUIRED = "ocr_required"


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

    retrieval_candidate_cap: int | None = Field(
        default=None, ge=1, description="Max raw candidates to retrieve."
    )
    evidence_set_cap: int | None = Field(
        default=None, ge=1, description="Max evidence sets to build."
    )
    neighbor_expansion_enabled: bool | None = Field(
        default=None, description="Enable adjacent chunk expansion."
    )
    neighbor_expansion_cap: int | None = Field(
        default=None, ge=0, description="Max adjacent chunks to expand."
    )
    duplicate_suppression_mode: DuplicateSuppressionMode | None = Field(
        default=None, description="How to handle duplicates."
    )
    context_token_budget: int | None = Field(
        default=None, ge=1, description="Token budget for context assembly."
    )
    deterministic_tie_break_order: tuple[str, ...] | None = Field(
        default=None, description="Tie-break ordering rule."
    )
    citation_include_heading_path: bool | None = Field(
        default=None, description="Include heading path in citations."
    )
    citation_include_locator: bool | None = Field(
        default=None, description="Include locator (page/line) in citations."
    )


class QueryRequest(BaseModel):
    """Internal query request envelope."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=1,
        description="The user's question.",
        json_schema_extra={"example": "What uses embeddings to retrieve related passages?"},
    )
    workspace_id: WorkspaceId = Field(
        description="The workspace scope to search against.",
        json_schema_extra={"example": "workspace_alpha"},
    )
    policy_overrides: QueryPolicyOverride | None = Field(
        default=None, description="Optional overrides for query policies."
    )


class QueryRun(BaseModel):
    """Internal record for a query run."""

    model_config = ConfigDict(extra="forbid")

    query_id: QueryId = Field(min_length=1)
    workspace_id: WorkspaceId
    question: str = Field(min_length=1)
    submitted_at: datetime = Field(default_factory=utc_now)
    status: QueryRunStatus = QueryRunStatus.PENDING
    policy_snapshot: dict[str, object]
    completed_at: datetime | None = None
    terminal_failure: QueryTerminalFailure | None = None

    @model_validator(mode="after")
    def validate_terminal_fields(self) -> QueryRun:
        if self.completed_at is not None and self.completed_at < self.submitted_at:
            raise ValueError("completed_at must be greater than or equal to submitted_at")
        if self.status is QueryRunStatus.FAILED and self.completed_at is None:
            raise ValueError("failed query runs must include completed_at")
        if self.status is QueryRunStatus.FAILED and self.terminal_failure is None:
            raise ValueError("failed query runs must include terminal_failure")
        if self.status is not QueryRunStatus.FAILED and self.terminal_failure is not None:
            raise ValueError("terminal_failure is only valid for failed query runs")
        if self.status is QueryRunStatus.SUCCEEDED and self.completed_at is None:
            raise ValueError("succeeded query runs must include completed_at")
        return self


class CorpusSnapshot(BaseModel):
    """Stable corpus boundary captured at query start."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: WorkspaceId
    query_started_at: datetime = Field(default_factory=utc_now)
    eligible_doc_ids: list[DocId] = Field(default_factory=lambda: [])
    retrieval_index_version: str | None = None
    readiness_version: str | None = None


class InterpretedQuery(BaseModel):
    """Structured interpretation output consumed by downstream stages."""

    model_config = ConfigDict(extra="forbid")

    normalized_question: str = Field(min_length=1)
    request_type: QueryRequestType
    answer_shape: str = Field(min_length=1)
    specificity: QuerySpecificity
    scope_hints: list[str] = Field(default_factory=lambda: [])
    requires_synthesis: bool = False
    synthesis_mode: SynthesisMode = SynthesisMode.NONE
    requires_source_navigation: bool = False
    unsupported_capability_flags: list[UnsupportedCapability] = Field(default_factory=lambda: [])
    normalization_notes: list[str] = Field(default_factory=lambda: [])


class RetrievedCandidate(BaseModel):
    """Provenance-preserving retrieval candidate contract."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId
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
    unit_rank: int = Field(ge=1)
    added_by_neighbor_expansion: bool = False
    selection_reason: str = Field(min_length=1)


class EvidenceSet(BaseModel):
    """Explicit evidence grouping prepared for later context assembly."""

    model_config = ConfigDict(extra="forbid")

    evidence_set_id: str = Field(min_length=1)
    grouping_mode: EvidenceGroupingMode
    evidence_units: list[EvidenceUnit] = Field(min_length=1)
    purpose: str = Field(min_length=1)
    coverage_notes: list[str] = Field(default_factory=lambda: [])
    conflict_flags: list[str] = Field(default_factory=lambda: [])
    assembly_reason: str = Field(min_length=1)


class ContextItem(BaseModel):
    """Structured rendered context item derived from one evidence set."""

    model_config = ConfigDict(extra="forbid")

    evidence_set_id: str = Field(min_length=1)
    assembly_rank: int = Field(ge=1)
    rendered_text: str = Field(min_length=1)
    contributing_doc_ids: list[DocId] = Field(min_length=1)
    heading_paths: list[list[str]] = Field(default_factory=lambda: [])
    locators: list[str] = Field(default_factory=lambda: [])
    estimated_token_count: int = Field(ge=1)


class ContextManifest(BaseModel):
    """Deterministic, inspectable model-facing context description."""

    model_config = ConfigDict(extra="forbid")

    ordered_evidence_set_ids: list[str] = Field(default_factory=lambda: [])
    included_evidence_set_ids: list[str] = Field(default_factory=lambda: [])
    dropped_evidence_set_ids: list[str] = Field(default_factory=lambda: [])
    inclusion_reasons: dict[str, str] = Field(default_factory=lambda: {})
    exclusion_reasons: dict[str, str] = Field(default_factory=lambda: {})
    token_budget: int = Field(ge=1)
    token_budget_used: int = Field(ge=0)
    context_items: list[ContextItem] = Field(default_factory=lambda: [])
    duplicate_suppression_notes: list[str] = Field(default_factory=lambda: [])

    @model_validator(mode="after")
    def validate_budget(self) -> ContextManifest:
        if self.token_budget_used > self.token_budget:
            raise ValueError("token_budget_used must not exceed token_budget")
        context_item_ids = [item.evidence_set_id for item in self.context_items]
        if context_item_ids != self.included_evidence_set_ids:
            raise ValueError("context_items must align to included_evidence_set_ids in order")
        ordered_ids = set(self.ordered_evidence_set_ids)
        included_ids = set(self.included_evidence_set_ids)
        dropped_ids = set(self.dropped_evidence_set_ids)
        if included_ids & dropped_ids:
            raise ValueError("included and dropped evidence set ids must be disjoint")
        if not included_ids.issubset(ordered_ids):
            raise ValueError(
                "included evidence set ids must be drawn from ordered_evidence_set_ids"
            )
        if not dropped_ids.issubset(ordered_ids):
            raise ValueError("dropped evidence set ids must be drawn from ordered_evidence_set_ids")
        if set(self.inclusion_reasons) != included_ids:
            raise ValueError("inclusion_reasons must cover exactly the included evidence set ids")
        if set(self.exclusion_reasons) != dropped_ids:
            raise ValueError("exclusion_reasons must cover exactly the dropped evidence set ids")
        return self


class SupportAssessment(BaseModel):
    """Structured support judgment for a query run."""

    model_config = ConfigDict(extra="forbid")

    support_state: SupportState
    qualifying_reason_codes: list[SupportQualifierReason] = Field(default_factory=lambda: [])
    trust_failure_labels: list[TrustFailureLabel] = Field(default_factory=lambda: [])
    summary: str | None = None
    unsupported_gaps: list[str] = Field(default_factory=lambda: [])
    conflicting_evidence_notes: list[str] = Field(default_factory=lambda: [])
    provenance_warnings: list[str] = Field(default_factory=lambda: [])


class AnswerModeDecision(BaseModel):
    """Policy-selected answer mode and its justification."""

    model_config = ConfigDict(extra="forbid")

    answer_mode: AnswerMode
    rationale: str = Field(min_length=1)
    based_on_support_state: SupportState
    required_qualifying_reason_codes: list[SupportQualifierReason] = Field(
        default_factory=lambda: []
    )
    allowed_scope_summary: str | None = None
    must_surface_conflict: bool = False


class AnswerDraft(BaseModel):
    """Generated answer text plus visible limitation hints."""

    model_config = ConfigDict(extra="forbid")

    answer_text: str = Field(min_length=1)
    visible_limitations: list[str] = Field(default_factory=lambda: [])
    should_render_citations: bool = True
    grounded_evidence_set_ids: list[str] = Field(default_factory=lambda: [])
    generator_version: str = Field(min_length=1)


class CitationRecord(BaseModel):
    """Single citation plus its support role."""

    model_config = ConfigDict(extra="forbid")

    evidence_set_id: str = Field(min_length=1)
    source_reference: SourceReference
    support_role: CitationSupportRole


class CitationBundle(BaseModel):
    """Bundle of provenance-derived citations for an answer."""

    model_config = ConfigDict(extra="forbid")

    citations: list[CitationRecord] = Field(default_factory=lambda: [])
    material_doc_ids: list[DocId] = Field(default_factory=lambda: [])
    renderer_version: str | None = None


class FinalQueryArtifacts(BaseModel):
    """Durable final answer artifacts persisted after Stage 7."""

    model_config = ConfigDict(extra="forbid")

    answer: AnswerDraft
    citations: CitationBundle
    support_state: SupportState
    qualifying_reason_codes: list[SupportQualifierReason] = Field(default_factory=lambda: [])
    answer_mode: AnswerMode
    trust_failure_labels: list[TrustFailureLabel] = Field(default_factory=lambda: [])
    created_at: datetime = Field(default_factory=utc_now)
