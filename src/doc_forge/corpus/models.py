"""Internal corpus and provenance models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from doc_forge.identifiers import DocId, WorkspaceId
from doc_forge.lifecycle import ProcessingStatus


class SourceType(StrEnum):
    """Supported source types for the MVP."""

    PDF = "pdf"
    MARKDOWN = "markdown"


class AnswerStatus(StrEnum):
    """Locked answer statuses for Phase 1."""

    SUPPORTED = "supported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class Document(BaseModel):
    """Stable top-level identity for an uploaded source artifact."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId
    workspace_id: WorkspaceId
    source_type: SourceType
    title: str
    filename: str
    uploaded_at: datetime
    ingest_status: ProcessingStatus
    storage_ref: str
    metadata: dict[str, str] | None = None


class Section(BaseModel):
    """Logical structural node recovered from source content."""

    model_config = ConfigDict(extra="forbid")

    section_id: str
    doc_id: DocId
    heading_path: list[str] = Field(min_length=1)
    depth: int = Field(ge=0)
    parent_section_id: str | None = None
    heading_text: str | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    source_start_offset: int | None = Field(default=None, ge=0)
    source_end_offset: int | None = Field(default=None, ge=0)
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

    chunk_id: str
    doc_id: DocId
    text: str
    ordinal: int = Field(ge=0)
    heading_path: list[str] = Field(min_length=1)
    section_id: str | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    source_start_offset: int | None = Field(default=None, ge=0)
    source_end_offset: int | None = Field(default=None, ge=0)
    lineage: dict[str, str] | None = None
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

    doc_id: DocId
    document_title: str
    snippet: str
    section_id: str | None = None
    heading_path: list[str] | None = Field(default=None, min_length=1)
    page_label: str | None = None
    chunk_id: str | None = None
    passage_anchor: str | None = None


class RetrievalHit(BaseModel):
    """Retrieved evidence forwarded to the answer layer."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    doc_id: DocId
    score: float
    source_reference: SourceReference


class Answer(BaseModel):
    """Answer payload returned by the future answering layer."""

    model_config = ConfigDict(extra="forbid")

    status: AnswerStatus
    answer_text: str
    source_references: list[SourceReference]
    insufficiency_note: str | None = None

    @model_validator(mode="after")
    def validate_answer_contract(self) -> Answer:
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
