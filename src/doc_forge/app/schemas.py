from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from doc_forge.identifiers import DocId, QueryId
from doc_forge.query import AnswerDraft, AnswerMode, CitationBundle, SupportState

from .api_examples import (
    DOCUMENT_DETAIL_RESPONSE_EXAMPLE,
    ERROR_RESPONSE_EXAMPLE,
    QUERY_ANSWER_RESPONSE_EXAMPLE,
    RETRIEVAL_QUERY_REQUEST_EXAMPLE,
    SYSTEM_STATUS_RESPONSE_EXAMPLE,
    WORKER_JOB_RESULT_EXAMPLE,
)


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
