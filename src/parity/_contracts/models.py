"""Pydantic models for internal MVP shared contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .lifecycle import ProcessingStatus


class SourceType(StrEnum):
    """Supported source types for the MVP."""

    # Text-based PDF input handled by the ingestion pipeline.
    PDF = "pdf"
    # Native Markdown input handled by the ingestion pipeline.
    MARKDOWN = "markdown"


class AnswerStatus(StrEnum):
    """Locked answer statuses for Phase 1."""

    # The answer is backed by at least one inspectable source reference.
    SUPPORTED = "supported"
    # The system must answer honestly when support is missing.
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class Document(BaseModel):
    """Stable top-level identity for an uploaded source artifact."""

    model_config = ConfigDict(extra="forbid")

    # Stable document identifier within the internal corpus.
    doc_id: str
    # Ownership/corpus boundary for later ingestion and retrieval flows.
    workspace_id: str
    # Input format lock for Phase 1.
    source_type: SourceType
    # Human-readable document title used in answer citations and inspection.
    title: str
    # Original uploaded filename.
    filename: str
    # Time the source artifact entered the system.
    uploaded_at: datetime
    # Current processing state in the locked lifecycle.
    ingest_status: ProcessingStatus
    # Durable pointer to the raw uploaded artifact.
    storage_ref: str
    # Optional non-contractual metadata carried alongside the core identity.
    metadata: dict[str, str] | None = None


class Section(BaseModel):
    """Logical structural node recovered from source content."""

    model_config = ConfigDict(extra="forbid")

    # Stable section identifier inside a document.
    section_id: str
    # Owning document identity.
    doc_id: str
    # Required structural breadcrumb used across parsing and retrieval.
    heading_path: list[str] = Field(min_length=1)
    # Nesting depth relative to the document root.
    depth: int = Field(ge=0)
    # Optional link to the containing section for hierarchy reconstruction.
    parent_section_id: str | None = None
    # The local heading text when recoverable.
    heading_text: str | None = None
    # Coarse source location for page-oriented inputs.
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    # Character or byte offsets into the normalized source text when available.
    source_start_offset: int | None = Field(default=None, ge=0)
    source_end_offset: int | None = Field(default=None, ge=0)
    # Optional parser confidence, kept out of required contract semantics.
    structure_confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_ranges(self) -> Section:
        if (
            self.page_start is not None
            and self.page_end is not None
            and self.page_end < self.page_start
        ):
            raise ValueError("page_end must be greater than or equal to page_start")
        if (
            self.source_start_offset is not None
            and self.source_end_offset is not None
            and self.source_end_offset < self.source_start_offset
        ):
            raise ValueError(
                "source_end_offset must be greater than or equal to source_start_offset",
            )
        return self


class Chunk(BaseModel):
    """Retrieval-addressable text unit used by Search / RAG."""

    model_config = ConfigDict(extra="forbid")

    # Stable retrieval-unit identifier.
    chunk_id: str
    # Owning document identity.
    doc_id: str
    # Text forwarded into retrieval and answer generation.
    text: str
    # Position of the chunk within document order.
    ordinal: int = Field(ge=0)
    # Structural breadcrumb retained with the chunk.
    heading_path: list[str] = Field(min_length=1)
    # Optional parent section link when chunking preserves section membership.
    section_id: str | None = None
    # Coarse page location when recoverable.
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    # Offsets into source text for traceability and debug inspection.
    source_start_offset: int | None = Field(default=None, ge=0)
    source_end_offset: int | None = Field(default=None, ge=0)
    # Internal hook for transformation lineage like parser/chunker versions.
    lineage: dict[str, str] | None = None
    # Extra debug-only payload that should not change contract semantics.
    debug_metadata: dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_ranges(self) -> Chunk:
        if (
            self.page_start is not None
            and self.page_end is not None
            and self.page_end < self.page_start
        ):
            raise ValueError("page_end must be greater than or equal to page_start")
        if (
            self.source_start_offset is not None
            and self.source_end_offset is not None
            and self.source_end_offset < self.source_start_offset
        ):
            raise ValueError(
                "source_end_offset must be greater than or equal to source_start_offset",
            )
        return self


class SourceReference(BaseModel):
    """Inspectable provenance anchor for evidence-backed answers."""

    model_config = ConfigDict(extra="forbid")

    # This minimum trio is the degraded-but-still-inspectable citation shape.
    doc_id: str
    # Human-readable title shown in answer provenance.
    document_title: str
    # Inspectable supporting text shown to users and downstream tooling.
    snippet: str
    # Optional structural pointer when the parser recovered section identity.
    section_id: str | None = None
    # Optional breadcrumb for section/chapter context.
    heading_path: list[str] | None = Field(default=None, min_length=1)
    # User-facing page label when page precision is available.
    page_label: str | None = None
    # Link back to the originating chunk when retained.
    chunk_id: str | None = None
    # Optional stable passage locator for deep-linking or inspection tools.
    passage_anchor: str | None = None


class RetrievalHit(BaseModel):
    """Retrieved evidence forwarded to the answer layer."""

    model_config = ConfigDict(extra="forbid")

    # Retrieved chunk identity.
    chunk_id: str
    # Owning document identity.
    doc_id: str
    # Retrieval relevance score passed to downstream consumers.
    score: float
    # Evidence packaged into the inspectable citation shape.
    source_reference: SourceReference


class Answer(BaseModel):
    """Answer payload returned by the future answering layer."""

    model_config = ConfigDict(extra="forbid")

    # Locked Phase 1 answer outcome.
    status: AnswerStatus
    # User-facing answer text in both success and insufficiency cases.
    answer_text: str
    # Evidence list for supported answers; must be empty for insufficiency.
    source_references: list[SourceReference]
    # Required explanation when the answer lacks enough supporting evidence.
    insufficiency_note: str | None = None

    @model_validator(mode="after")
    def validate_answer_contract(self) -> Answer:
        # Phase 1 locks two honest answer shapes: supported-with-evidence or
        # insufficient_evidence-without-fabricated-citations.
        if self.status is AnswerStatus.SUPPORTED and not self.source_references:
            raise ValueError("supported answers must include at least one source reference")
        if self.status is AnswerStatus.SUPPORTED and self.insufficiency_note is not None:
            raise ValueError("supported answers must not include an insufficiency_note")
        if self.status is AnswerStatus.INSUFFICIENT_EVIDENCE and not self.insufficiency_note:
            raise ValueError(
                "insufficient_evidence answers must include an insufficiency_note",
            )
        if self.status is AnswerStatus.INSUFFICIENT_EVIDENCE and self.source_references:
            raise ValueError(
                "insufficient_evidence answers must use an explicit empty source_references list",
            )
        return self
