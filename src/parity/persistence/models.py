"""Storage-facing lifecycle metadata models and SQL schema definitions."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict, Field, field_validator

from parity._contracts import Document, ProcessingStatus, SourceType
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


def _coerce_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    raise TypeError(f"expected datetime, got {type(value).__name__}")
