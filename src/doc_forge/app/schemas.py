from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from doc_forge.corpus.models import SourceType
from doc_forge.identifiers import DocId, QueryId, WorkspaceId
from doc_forge.lifecycle.status import ProcessingStatus
from doc_forge.persistence.jobs import DocumentJobStage
from doc_forge.query.contracts import (
    AnswerMode,
    CitationSupportRole,
    DuplicateSuppressionMode,
    QueryRunStatus,
    QueryStageName,
    SupportQualifierReason,
    SupportState,
    TrustFailureLabel,
)
from doc_forge.query.trace import QueryStageTraceStatus

from .api_examples import (
    DOCUMENT_DETAIL_RESPONSE_EXAMPLE,
    ERROR_RESPONSE_EXAMPLE,
    QUERY_ANSWER_RESPONSE_EXAMPLE,
    QUERY_CITATION_REVIEW_EXAMPLE,
    QUERY_RUN_REVIEW_SUMMARY_EXAMPLE,
    QUERY_TRACE_REVIEW_EXAMPLE,
    RETRIEVAL_QUERY_REQUEST_EXAMPLE,
    SYSTEM_STATUS_RESPONSE_EXAMPLE,
    WORKER_JOB_RESULT_EXAMPLE,
)

# ---------------------------------------------------------------------------
# Decoupled DTOs mapped from internal domain concepts
# ---------------------------------------------------------------------------


class VectorSearchHit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chunk_id: str
    doc_id: DocId
    score: float


class SourceLocator(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page_number: int | None = None
    line_number: int | None = None


class SourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    doc_id: DocId
    document_title: str
    snippet: str
    section_id: str | None = None
    heading_path: list[str] | None = Field(default=None, min_length=1)
    page_label: str | None = None
    chunk_id: str | None = None
    passage_anchor: str | None = None


class QueryTerminalFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")
    error_code: str = Field(min_length=1)
    error_class: str = Field(min_length=1)
    stage_name: QueryStageName | None = None
    message: str = Field(min_length=1)
    trust_failure_labels: list[TrustFailureLabel] = Field(default_factory=lambda: [])


class QueryPolicyOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")
    retrieval_candidate_cap: int | None = Field(default=None, ge=1)
    evidence_set_cap: int | None = Field(default=None, ge=1)
    neighbor_expansion_enabled: bool | None = Field(default=None)
    neighbor_expansion_cap: int | None = Field(default=None, ge=0)
    duplicate_suppression_mode: DuplicateSuppressionMode | None = Field(default=None)
    context_token_budget: int | None = Field(default=None, ge=1)
    deterministic_tie_break_order: tuple[str, ...] | None = Field(default=None)
    citation_include_heading_path: bool | None = Field(default=None)
    citation_include_locator: bool | None = Field(default=None)


class CorpusSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: WorkspaceId
    query_started_at: datetime
    eligible_doc_ids: list[DocId] = Field(default_factory=lambda: [])
    retrieval_index_version: str | None = None
    readiness_version: str | None = None


class QuerySnapshotSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: WorkspaceId = Field(min_length=1)
    query_started_at: datetime
    eligible_doc_ids: list[DocId] = Field(default_factory=lambda: [])
    retrieval_index_version: str | None = None
    readiness_version: str | None = None


class AnswerDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer_text: str = Field(min_length=1)
    visible_limitations: list[str] = Field(default_factory=lambda: [])
    should_render_citations: bool = True
    grounded_evidence_set_ids: list[str] = Field(default_factory=lambda: [])
    generator_version: str = Field(min_length=1)


class CitationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_set_id: str = Field(min_length=1)
    source_reference: SourceReference
    support_role: CitationSupportRole


class CitationBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    citations: list[CitationRecord] = Field(default_factory=lambda: [])
    material_doc_ids: list[DocId] = Field(default_factory=lambda: [])
    renderer_version: str | None = None


class FinalQueryArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: AnswerDraft
    citations: CitationBundle
    support_state: SupportState
    qualifying_reason_codes: list[SupportQualifierReason] = Field(default_factory=lambda: [])
    answer_mode: AnswerMode
    trust_failure_labels: list[TrustFailureLabel] = Field(default_factory=lambda: [])
    created_at: datetime


class QueryStageTimingSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_name: str = Field(min_length=1)
    stage_status: str = Field(min_length=1)
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)


class QueryTraceTimingSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trace_count: int = Field(ge=0)
    total_duration_ms: int | None = Field(default=None, ge=0)
    stages: list[QueryStageTimingSummary] = Field(default_factory=lambda: [])


class QueryStageTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_id: QueryId = Field(min_length=1)
    stage_name: QueryStageName
    stage_status: QueryStageTraceStatus
    started_at: datetime
    finished_at: datetime | None = None
    payload: dict[str, object] = Field(default_factory=lambda: {})


class QueryTraceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_id: QueryId = Field(min_length=1)
    run_status: QueryRunStatus
    stage_traces: list[QueryStageTrace] = Field(default_factory=lambda: [])


# ---------------------------------------------------------------------------
# API Request/Response Boundaries
# ---------------------------------------------------------------------------


class RetrievalQueryRequest(BaseModel):
    """Internal request payload for document-scoped retrieval smoke queries."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": RETRIEVAL_QUERY_REQUEST_EXAMPLE},
    )

    doc_id: DocId = Field(..., description="The ID of the document to query.")
    query: str = Field(
        min_length=1, description="The textual query to run against the document's chunks."
    )
    k: int = Field(default=3, ge=1, description="The maximum number of chunks to return.")


class QueryAnswerResponse(BaseModel):
    """Clean public-facing answer payload for a completed query."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": QUERY_ANSWER_RESPONSE_EXAMPLE},
    )

    query_id: QueryId = Field(min_length=1, description="The unique query identifier.")
    answer: AnswerDraft = Field(description="The generated answer draft.")
    support_state: SupportState = Field(
        description="The assessed evidence support state (e.g., sufficient, partial, insufficient)."
    )
    answer_mode: AnswerMode = Field(
        description="The selected answer generation mode (e.g., direct_answer, full_abstention)."
    )
    citations: CitationBundle = Field(description="The assembled citations supporting the answer.")
    message: str = Field(min_length=1, description="Human-readable result message.")


class WorkerJobResult(BaseModel):
    """Payload representing a triggered worker job result."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": WORKER_JOB_RESULT_EXAMPLE},
    )

    job_id: str | None = Field(default=None, description="The job ID that was executed, if any.")
    status: str | None = Field(
        default=None, description="The terminal status of the executed job, if any."
    )


class ErrorResponse(BaseModel):
    """Standardized error response payload."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": ERROR_RESPONSE_EXAMPLE},
    )

    detail: str = Field(
        ...,
        description="A human-readable explanation of the error.",
        json_schema_extra={"example": ERROR_RESPONSE_EXAMPLE["detail"]},
    )


class SystemStatusResponse(BaseModel):
    """Standardized system status response payload."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": SYSTEM_STATUS_RESPONSE_EXAMPLE},
    )

    status: str = Field(..., description="The current status of the system component.")


class DocumentDetailResponse(BaseModel):
    """Detailed metadata response for a specific registered document."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": DOCUMENT_DETAIL_RESPONSE_EXAMPLE},
    )

    doc_id: str = Field(min_length=1, description="The unique identifier of the document.")
    workspace_id: str = Field(min_length=1, description="The workspace this document belongs to.")
    source_type: str = Field(
        min_length=1, description="The type of the source artifact (e.g., pdf, markdown)."
    )
    title: str = Field(min_length=1, description="The title of the document.")
    filename: str = Field(min_length=1, description="The original filename of the document.")
    uploaded_at: str = Field(min_length=1, description="ISO-8601 formatted upload timestamp.")
    checksum: str = Field(
        min_length=1, description="SHA-256 checksum of the original source content."
    )
    ingest_status: str = Field(min_length=1, description="Current ingestion lifecycle status.")
    failure_code: str | None = Field(
        default=None, description="Standardized error code if the ingest failed."
    )
    failure_detail: str | None = Field(
        default=None, description="Human-readable detail if the ingest failed."
    )
    raw_storage_path: str = Field(
        min_length=1, description="The logical path where the raw file is stored."
    )


class UploadDocumentResponse(BaseModel):
    """Internal response payload for successful document uploads."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId = Field(
        ...,
        description="Unique identifier for the registered document.",
        json_schema_extra={"example": "doc_1234abcd"},
    )
    ingest_status: ProcessingStatus = Field(
        ...,
        description="The current processing status of the document.",
        json_schema_extra={"example": "registered"},
    )
    source_type: SourceType = Field(
        ...,
        description="The detected source type of the document.",
        json_schema_extra={"example": "pdf"},
    )
    filename: str = Field(
        ...,
        description="The original filename of the uploaded document.",
        json_schema_extra={"example": "report.pdf"},
    )
    title: str = Field(
        ...,
        description="The resolved title of the document.",
        json_schema_extra={"example": "Q3 Financial Report"},
    )
    uploaded_at: datetime = Field(
        ..., description="The UTC timestamp when the document was uploaded."
    )
    checksum: str = Field(
        ...,
        description="The SHA-256 checksum of the uploaded file content.",
        json_schema_extra={
            "example": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        },
    )


class DocumentStatusResponse(BaseModel):
    """Internal status payload for one persisted document."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId = Field(
        ...,
        description="The unique identifier of the document.",
        json_schema_extra={"example": "doc_1234abcd"},
    )
    ingest_status: ProcessingStatus = Field(
        ...,
        description="The current ingestion status of the document.",
        json_schema_extra={"example": "indexed"},
    )
    source_type: SourceType = Field(
        ..., description="The source type of the document.", json_schema_extra={"example": "pdf"}
    )
    title: str = Field(
        ...,
        description="The title of the document.",
        json_schema_extra={"example": "Q3 Financial Report"},
    )
    filename: str = Field(
        ...,
        description="The original filename of the document.",
        json_schema_extra={"example": "report.pdf"},
    )
    failure_code: str | None = Field(
        default=None,
        description="A machine-readable code if the document processing failed.",
        json_schema_extra={"example": "extraction_failed"},
    )
    failure_detail: str | None = Field(
        default=None,
        description="A human-readable explanation if the document processing failed.",
        json_schema_extra={"example": "Failed to extract text from page 3"},
    )
    active_job_stage: DocumentJobStage | None = Field(
        default=None,
        description="The currently active processing job stage, if any.",
        json_schema_extra={"example": "chunk"},
    )


class RetryDocumentResponse(BaseModel):
    """Internal response payload for a queued retry."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId = Field(
        ...,
        description="The unique identifier of the document.",
        json_schema_extra={"example": "doc_1234abcd"},
    )
    ingest_status: ProcessingStatus = Field(
        ...,
        description="The new status of the document after queuing for retry.",
        json_schema_extra={"example": "registered"},
    )
    queued_stage: DocumentJobStage = Field(
        ...,
        description="The specific processing stage that has been queued for execution.",
        json_schema_extra={"example": "extract"},
    )


class RetrievalQueryResponse(BaseModel):
    """Internal retrieval smoke-query payload."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId = Field(
        ...,
        description="The unique identifier of the document searched against.",
        json_schema_extra={"example": "doc_1234abcd"},
    )
    hits: list[VectorSearchHit] = Field(
        default_factory=lambda: [],
        description="The list of vector search hits (chunks) returned from the vector store.",
    )


class DocumentArtifactRefsResponse(BaseModel):
    """Internal artifact-inspection response payload."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId = Field(
        ...,
        description="The unique identifier of the document.",
        json_schema_extra={"example": "doc_1234abcd"},
    )
    raw_path: str = Field(
        ...,
        description="The filesystem path to the original raw uploaded file.",
        json_schema_extra={"example": "/data/artifacts/doc_1234abcd/raw.pdf"},
    )
    extracted_path: str | None = Field(
        default=None,
        description="The filesystem path to the extracted text artifact.",
        json_schema_extra={"example": "/data/artifacts/doc_1234abcd/extracted.json"},
    )
    normalized_path: str | None = Field(
        default=None,
        description="The filesystem path to the normalized text artifact.",
        json_schema_extra={"example": "/data/artifacts/doc_1234abcd/normalized.json"},
    )


class SubmitQueryRequest(BaseModel):
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


class QueryRunSummaryResponse(BaseModel):
    """Summary view over one persisted query run."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": QUERY_RUN_REVIEW_SUMMARY_EXAMPLE},
    )

    query_id: QueryId = Field(min_length=1, description="The unique query identifier.")
    workspace_id: WorkspaceId = Field(
        min_length=1,
        description="The workspace this query was executed in.",
    )
    question: str = Field(min_length=1, description="The user's original question.")
    status: QueryRunStatus = Field(description="Terminal status of the overall query run.")
    submitted_at: datetime = Field(description="When the query was submitted.")
    completed_at: datetime | None = Field(
        default=None, description="When the query finished executing."
    )
    policy_snapshot: dict[str, object] = Field(
        description="The applied policy configuration for this run."
    )
    snapshot_summary: QuerySnapshotSummary | None = Field(
        default=None, description="Snapshot of the corpus used."
    )
    support_state: SupportState | None = Field(
        default=None, description="The assessed evidence support state."
    )
    answer_mode: AnswerMode | None = Field(
        default=None, description="The selected answer generation mode."
    )
    trust_failure_labels: list[TrustFailureLabel] = Field(
        default_factory=lambda: [], description="Identified trust failure signals."
    )
    visible_limitations: list[str] = Field(
        default_factory=lambda: [], description="Disclaimers regarding answer quality."
    )
    has_answer: bool = Field(
        default=False, description="Whether a final answer was successfully generated."
    )
    terminal_failure: QueryTerminalFailure | None = Field(
        default=None, description="Details if the query failed execution."
    )
    trace_summary: QueryTraceTimingSummary = Field(description="Aggregated stage timing details.")


class QueryTraceReviewResponse(BaseModel):
    """Detailed persisted trace review payload."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": QUERY_TRACE_REVIEW_EXAMPLE},
    )

    summary: QueryRunSummaryResponse = Field(description="Overall query run summary.")
    snapshot: CorpusSnapshot | None = Field(
        default=None, description="The corpus snapshot captured at query time."
    )
    trace_bundle: QueryTraceBundle = Field(description="The full stage-by-stage execution trace.")
    final_artifacts: FinalQueryArtifacts | None = Field(
        default=None,
        description="The final answer and citation artifacts, if generation succeeded.",
    )


class QueryCitationReviewResponse(BaseModel):
    """Citation-only review payload."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": QUERY_CITATION_REVIEW_EXAMPLE},
    )

    query_id: QueryId = Field(min_length=1, description="The unique query identifier.")
    support_state: SupportState = Field(description="The assessed evidence support state.")
    answer_mode: AnswerMode = Field(description="The selected answer generation mode.")
    trust_failure_labels: list[TrustFailureLabel] = Field(
        default_factory=lambda: [], description="Identified trust failure signals."
    )
    citations: CitationBundle = Field(description="The assembled citations for the answer.")
