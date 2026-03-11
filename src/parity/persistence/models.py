"""Storage-facing lifecycle metadata models and SQL schema definitions."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict, Field, field_validator

from parity._contracts import Chunk, Document, ProcessingStatus, Section, SourceType
from parity.indexing import ChunkEmbedding, IndexEntry
from parity.lifecycle.models import FailureCategory, LifecycleEvent, LifecycleStage


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


metadata = sa.MetaData()

documents_table = sa.Table(
    "documents",
    metadata,
    sa.Column("doc_id", sa.Text(), primary_key=True),
    sa.Column("workspace_id", sa.Text(), nullable=False, index=True),
    sa.Column("source_type", sa.Text(), nullable=False),
    sa.Column("title", sa.Text(), nullable=False),
    sa.Column("filename", sa.Text(), nullable=False),
    sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("ingest_status", sa.Text(), nullable=False),
    sa.Column("storage_ref", sa.Text(), nullable=False),
    sa.Column("metadata_json", sa.JSON(), nullable=True),
    sa.Column("checksum", sa.Text(), nullable=True),
    sa.Column("raw_storage_path", sa.Text(), nullable=True),
    sa.Column("failure_code", sa.Text(), nullable=True),
    sa.Column("failure_detail", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)

lifecycle_events_table = sa.Table(
    "lifecycle_events",
    metadata,
    sa.Column("event_id", sa.Text(), primary_key=True),
    sa.Column(
        "doc_id",
        sa.Text(),
        sa.ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column("stage", sa.Text(), nullable=False),
    sa.Column("from_status", sa.Text(), nullable=True),
    sa.Column("to_status", sa.Text(), nullable=False),
    sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("failure_category", sa.Text(), nullable=True),
    sa.Column("detail_json", sa.JSON(), nullable=False),
)

sections_table = sa.Table(
    "sections",
    metadata,
    sa.Column("section_id", sa.Text(), primary_key=True),
    sa.Column(
        "doc_id",
        sa.Text(),
        sa.ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column("heading_path_json", sa.JSON(), nullable=False),
    sa.Column("depth", sa.Integer(), nullable=False),
    sa.Column("parent_section_id", sa.Text(), nullable=True),
    sa.Column("heading_text", sa.Text(), nullable=True),
    sa.Column("page_start", sa.Integer(), nullable=True),
    sa.Column("page_end", sa.Integer(), nullable=True),
    sa.Column("source_start_offset", sa.Integer(), nullable=True),
    sa.Column("source_end_offset", sa.Integer(), nullable=True),
    sa.Column("structure_confidence", sa.Float(), nullable=True),
    sa.UniqueConstraint("doc_id", "section_id", name="uq_sections_doc_section"),
    sa.ForeignKeyConstraint(
        ["doc_id", "parent_section_id"],
        ["sections.doc_id", "sections.section_id"],
        ondelete="CASCADE",
    ),
)

chunks_table = sa.Table(
    "chunks",
    metadata,
    sa.Column("chunk_id", sa.Text(), primary_key=True),
    sa.Column(
        "doc_id",
        sa.Text(),
        sa.ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column("text", sa.Text(), nullable=False),
    sa.Column("ordinal", sa.Integer(), nullable=False),
    sa.Column("heading_path_json", sa.JSON(), nullable=False),
    sa.Column("section_id", sa.Text(), nullable=True),
    sa.Column("page_start", sa.Integer(), nullable=True),
    sa.Column("page_end", sa.Integer(), nullable=True),
    sa.Column("source_start_offset", sa.Integer(), nullable=True),
    sa.Column("source_end_offset", sa.Integer(), nullable=True),
    sa.Column("lineage_json", sa.JSON(), nullable=True),
    sa.Column("debug_metadata_json", sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(
        ["doc_id", "section_id"],
        ["sections.doc_id", "sections.section_id"],
        ondelete="CASCADE",
    ),
)

index_entries_table = sa.Table(
    "index_entries",
    metadata,
    sa.Column(
        "chunk_id",
        sa.Text(),
        sa.ForeignKey("chunks.chunk_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "doc_id",
        sa.Text(),
        sa.ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column("index_backend", sa.Text(), nullable=False),
    sa.Column("index_key", sa.Text(), nullable=False),
    sa.Column("index_version", sa.Text(), nullable=False),
    sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
)

chunk_embeddings_table = sa.Table(
    "chunk_embeddings",
    metadata,
    sa.Column(
        "chunk_id",
        sa.Text(),
        sa.ForeignKey("chunks.chunk_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "doc_id",
        sa.Text(),
        sa.ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column("embedding_model", sa.Text(), nullable=False),
    sa.Column("embedding_vector_json", sa.JSON(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)


class PersistedDocument(BaseModel):
    """Durable document metadata row used by lifecycle persistence."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    workspace_id: str
    source_type: SourceType
    title: str
    filename: str
    uploaded_at: datetime
    ingest_status: ProcessingStatus
    storage_ref: str
    metadata_json: dict[str, str] | None = None
    checksum: str | None = None
    raw_storage_path: str | None = None
    failure_code: str | None = None
    failure_detail: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("uploaded_at", "created_at", "updated_at", mode="before")
    @classmethod
    def normalize_datetime_fields(cls, value: object) -> datetime:
        return _coerce_datetime(value)

    @classmethod
    def from_contract(
        cls,
        document: Document,
        *,
        checksum: str | None = None,
        raw_storage_path: str | None = None,
        failure_code: str | None = None,
        failure_detail: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> PersistedDocument:
        """Lift the current internal document contract into a durable storage model."""

        return cls(
            doc_id=document.doc_id,
            workspace_id=document.workspace_id,
            source_type=document.source_type,
            title=document.title,
            filename=document.filename,
            uploaded_at=document.uploaded_at,
            ingest_status=document.ingest_status,
            storage_ref=document.storage_ref,
            metadata_json=document.metadata,
            checksum=checksum,
            raw_storage_path=raw_storage_path,
            failure_code=failure_code,
            failure_detail=failure_detail,
            created_at=created_at or utc_now(),
            updated_at=updated_at or utc_now(),
        )

    def to_contract(self) -> Document:
        """Project durable storage metadata back into the current document contract shape."""

        return Document(
            doc_id=self.doc_id,
            workspace_id=self.workspace_id,
            source_type=self.source_type,
            title=self.title,
            filename=self.filename,
            uploaded_at=self.uploaded_at,
            ingest_status=self.ingest_status,
            storage_ref=self.storage_ref,
            metadata=self.metadata_json,
        )

    def to_row(self) -> dict[str, object]:
        """Serialize a persisted document into SQL-ready values."""

        return self.model_dump(mode="python")


class PersistedDocumentStatusUpdate(BaseModel):
    """Typed SQL update payload for document status changes."""

    model_config = ConfigDict(extra="forbid")

    ingest_status: ProcessingStatus
    failure_code: str | None = None
    failure_detail: str | None = None
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("updated_at", mode="before")
    @classmethod
    def normalize_updated_at(cls, value: object) -> datetime:
        return _coerce_datetime(value)

    @classmethod
    def for_status(
        cls,
        *,
        status: ProcessingStatus,
        failure_code: str | None = None,
        failure_detail: str | None = None,
        updated_at: datetime | None = None,
    ) -> PersistedDocumentStatusUpdate:
        """Build a storage update payload from lifecycle status semantics."""

        return cls(
            ingest_status=status,
            failure_code=failure_code if status is ProcessingStatus.FAILED else None,
            failure_detail=failure_detail if status is ProcessingStatus.FAILED else None,
            updated_at=updated_at or utc_now(),
        )

    def to_row(self) -> dict[str, object]:
        """Serialize a status update into SQL-ready values."""

        return self.model_dump(mode="python")


class PersistedLifecycleEvent(BaseModel):
    """Storage-facing lifecycle event row."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    doc_id: str
    stage: LifecycleStage
    from_status: ProcessingStatus | None = None
    to_status: ProcessingStatus
    occurred_at: datetime
    failure_category: FailureCategory | None = None
    detail_json: dict[str, str] = Field(default_factory=dict)

    @field_validator("occurred_at", mode="before")
    @classmethod
    def normalize_occurred_at(cls, value: object) -> datetime:
        return _coerce_datetime(value)

    @classmethod
    def from_runtime_event(cls, event: LifecycleEvent) -> PersistedLifecycleEvent:
        """Project a runtime lifecycle event into its storage shape."""

        return cls(
            event_id=event.event_id,
            doc_id=event.doc_id,
            stage=event.stage,
            from_status=event.from_status,
            to_status=event.to_status,
            occurred_at=event.occurred_at,
            failure_category=event.failure_category,
            detail_json=event.detail,
        )

    def to_runtime_event(self) -> LifecycleEvent:
        """Project a storage lifecycle event row back into the runtime shape."""

        return LifecycleEvent(
            event_id=self.event_id,
            doc_id=self.doc_id,
            stage=self.stage,
            from_status=self.from_status,
            to_status=self.to_status,
            occurred_at=self.occurred_at,
            failure_category=self.failure_category,
            detail=self.detail_json,
        )

    def to_row(self) -> dict[str, object]:
        """Serialize a storage lifecycle event into SQL-ready values."""

        return self.model_dump(mode="python")


class PersistedSection(BaseModel):
    """Storage-facing section row."""

    model_config = ConfigDict(extra="forbid")

    section_id: str
    doc_id: str
    heading_path_json: list[str]
    depth: int
    parent_section_id: str | None = None
    heading_text: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    source_start_offset: int | None = None
    source_end_offset: int | None = None
    structure_confidence: float | None = None

    @classmethod
    def from_contract(cls, section: Section) -> PersistedSection:
        """Project a contract section into its storage shape."""

        return cls(
            section_id=section.section_id,
            doc_id=section.doc_id,
            heading_path_json=section.heading_path,
            depth=section.depth,
            parent_section_id=section.parent_section_id,
            heading_text=section.heading_text,
            page_start=section.page_start,
            page_end=section.page_end,
            source_start_offset=section.source_start_offset,
            source_end_offset=section.source_end_offset,
            structure_confidence=section.structure_confidence,
        )

    def to_contract(self) -> Section:
        """Project a storage section row back into the contract shape."""

        return Section(
            section_id=self.section_id,
            doc_id=self.doc_id,
            heading_path=self.heading_path_json,
            depth=self.depth,
            parent_section_id=self.parent_section_id,
            heading_text=self.heading_text,
            page_start=self.page_start,
            page_end=self.page_end,
            source_start_offset=self.source_start_offset,
            source_end_offset=self.source_end_offset,
            structure_confidence=self.structure_confidence,
        )

    def to_row(self) -> dict[str, object]:
        """Serialize a storage section into SQL-ready values."""

        return self.model_dump(mode="python")


class PersistedChunk(BaseModel):
    """Storage-facing chunk row."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    doc_id: str
    text: str
    ordinal: int
    heading_path_json: list[str]
    section_id: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    source_start_offset: int | None = None
    source_end_offset: int | None = None
    lineage_json: dict[str, str] | None = None
    debug_metadata_json: dict[str, str] | None = None

    @classmethod
    def from_contract(cls, chunk: Chunk) -> PersistedChunk:
        """Project a contract chunk into its storage shape."""

        return cls(
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            text=chunk.text,
            ordinal=chunk.ordinal,
            heading_path_json=chunk.heading_path,
            section_id=chunk.section_id,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            source_start_offset=chunk.source_start_offset,
            source_end_offset=chunk.source_end_offset,
            lineage_json=chunk.lineage,
            debug_metadata_json=chunk.debug_metadata,
        )

    def to_contract(self) -> Chunk:
        """Project a storage chunk row back into the contract shape."""

        return Chunk(
            chunk_id=self.chunk_id,
            doc_id=self.doc_id,
            text=self.text,
            ordinal=self.ordinal,
            heading_path=self.heading_path_json,
            section_id=self.section_id,
            page_start=self.page_start,
            page_end=self.page_end,
            source_start_offset=self.source_start_offset,
            source_end_offset=self.source_end_offset,
            lineage=self.lineage_json,
            debug_metadata=self.debug_metadata_json,
        )

    def to_row(self) -> dict[str, object]:
        """Serialize a storage chunk into SQL-ready values."""

        return self.model_dump(mode="python")


class PersistedIndexEntry(BaseModel):
    """Storage-facing index-entry row."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    doc_id: str
    index_backend: str
    index_key: str
    index_version: str
    published_at: datetime

    @field_validator("published_at", mode="before")
    @classmethod
    def normalize_published_at(cls, value: object) -> datetime:
        return _coerce_datetime(value)

    @classmethod
    def from_runtime(cls, entry: IndexEntry) -> PersistedIndexEntry:
        return cls(**entry.model_dump(mode="python"))

    def to_runtime(self) -> IndexEntry:
        return IndexEntry(**self.model_dump(mode="python"))

    def to_row(self) -> dict[str, object]:
        return self.model_dump(mode="python")


class PersistedChunkEmbedding(BaseModel):
    """Storage-facing chunk-embedding row."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    doc_id: str
    embedding_model: str
    embedding_vector_json: list[float]
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def normalize_created_at(cls, value: object) -> datetime:
        return _coerce_datetime(value)

    @classmethod
    def from_runtime(cls, embedding: ChunkEmbedding) -> PersistedChunkEmbedding:
        return cls(
            chunk_id=embedding.chunk_id,
            doc_id=embedding.doc_id,
            embedding_model=embedding.embedding_model,
            embedding_vector_json=embedding.embedding_vector,
            created_at=embedding.created_at,
        )

    def to_runtime(self) -> ChunkEmbedding:
        return ChunkEmbedding(
            chunk_id=self.chunk_id,
            doc_id=self.doc_id,
            embedding_model=self.embedding_model,
            embedding_vector=self.embedding_vector_json,
            created_at=self.created_at,
        )

    def to_row(self) -> dict[str, object]:
        return self.model_dump(mode="python")


def persisted_document_to_row(document: PersistedDocument) -> dict[str, object]:
    """Serialize a persisted document model into a SQLAlchemy row mapping."""

    return document.to_row()


def row_to_persisted_document(row: Mapping[str, object]) -> PersistedDocument:
    """Rehydrate a persisted document from a SQLAlchemy mapping row."""

    return PersistedDocument.model_validate(dict(row))


def lifecycle_event_to_row(event: LifecycleEvent) -> dict[str, object]:
    """Serialize a lifecycle event into a SQLAlchemy row mapping."""

    return PersistedLifecycleEvent.from_runtime_event(event).to_row()


def row_to_lifecycle_event(row: Mapping[str, object]) -> LifecycleEvent:
    """Rehydrate a lifecycle event from a SQLAlchemy mapping row."""

    return PersistedLifecycleEvent.model_validate(dict(row)).to_runtime_event()


def persisted_section_to_row(section: PersistedSection) -> dict[str, object]:
    """Serialize a persisted section into a SQLAlchemy row mapping."""

    return section.to_row()


def row_to_persisted_section(row: Mapping[str, object]) -> PersistedSection:
    """Rehydrate a persisted section from a SQLAlchemy mapping row."""

    return PersistedSection.model_validate(dict(row))


def persisted_chunk_to_row(chunk: PersistedChunk) -> dict[str, object]:
    """Serialize a persisted chunk into a SQLAlchemy row mapping."""

    return chunk.to_row()


def row_to_persisted_chunk(row: Mapping[str, object]) -> PersistedChunk:
    """Rehydrate a persisted chunk from a SQLAlchemy mapping row."""

    return PersistedChunk.model_validate(dict(row))


def index_entry_to_row(entry: IndexEntry) -> dict[str, object]:
    """Serialize a runtime index entry into a SQLAlchemy row mapping."""

    return PersistedIndexEntry.from_runtime(entry).to_row()


def row_to_index_entry(row: Mapping[str, object]) -> IndexEntry:
    """Rehydrate an index entry from a SQLAlchemy mapping row."""

    return PersistedIndexEntry.model_validate(dict(row)).to_runtime()


def chunk_embedding_to_row(embedding: ChunkEmbedding) -> dict[str, object]:
    """Serialize a runtime chunk embedding into a SQLAlchemy row mapping."""

    return PersistedChunkEmbedding.from_runtime(embedding).to_row()


def row_to_chunk_embedding(row: Mapping[str, object]) -> ChunkEmbedding:
    """Rehydrate a chunk embedding from a SQLAlchemy mapping row."""

    return PersistedChunkEmbedding.model_validate(dict(row)).to_runtime()


def _coerce_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    raise TypeError(f"expected datetime, got {type(value).__name__}")
