"""Runtime job models and SQL schema for document lifecycle queue metadata."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from enum import StrEnum

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict, Field, field_validator

from doc_forge.identifiers import DocId

from .models import metadata, utc_now


class DocumentJobStage(StrEnum):
    """Named stages that can be queued for document processing."""

    REGISTER = "REGISTER"
    EXTRACT = "EXTRACT"
    NORMALIZE = "NORMALIZE"
    SECTIONIZE = "SECTIONIZE"
    CHUNK = "CHUNK"
    INDEX = "INDEX"
    READY_CHECK = "READY_CHECK"


class DocumentJobStatus(StrEnum):
    """Current execution state for a queued document job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentJob(BaseModel):
    """Durable queue row for stage-oriented document work."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    doc_id: DocId
    target_stage: DocumentJobStage
    status: DocumentJobStatus = DocumentJobStatus.QUEUED
    attempt_count: int = Field(default=0, ge=0)
    not_before: datetime | None = None
    error_code: str | None = None
    error_detail: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("not_before", "created_at", "updated_at", mode="before")
    @classmethod
    def normalize_datetime_fields(cls, value: object) -> datetime | None:
        if value is None:
            return None
        return _coerce_datetime(value)

    def to_row(self) -> dict[str, object]:
        """Serialize a document job into SQL-ready values."""

        return self.model_dump(mode="python")


document_jobs_table = sa.Table(
    "document_jobs",
    metadata,
    sa.Column("job_id", sa.Text(), primary_key=True),
    sa.Column(
        "doc_id",
        sa.Text(),
        sa.ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column("target_stage", sa.Text(), nullable=False),
    sa.Column("status", sa.Text(), nullable=False),
    sa.Column("attempt_count", sa.Integer(), nullable=False),
    sa.Column("not_before", sa.DateTime(timezone=True), nullable=True),
    sa.Column("error_code", sa.Text(), nullable=True),
    sa.Column("error_detail", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)


def document_job_to_row(job: DocumentJob) -> dict[str, object]:
    """Serialize a document job into a SQLAlchemy row mapping."""

    return job.to_row()


def row_to_document_job(row: Mapping[str, object]) -> DocumentJob:
    """Rehydrate a document job from a SQLAlchemy mapping row."""

    return DocumentJob.model_validate(dict(row))


def _coerce_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    raise TypeError(f"expected datetime, got {type(value).__name__}")
