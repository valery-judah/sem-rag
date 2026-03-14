from __future__ import annotations

import pathlib
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any, Protocol, TypedDict, Unpack

import pytest
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.engine import Engine

from doc_forge.corpus import Chunk, Document, Section, SourceType
from doc_forge.identifiers import DocId, WorkspaceId
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.lifecycle.models import FailureCategory, LifecycleEvent, LifecycleStage
from doc_forge.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentJobStatus,
    PersistedDocument,
    apply_migrations,
)


@pytest.fixture
def db_url(tmp_path: pathlib.Path) -> str:
    database_path = tmp_path / "lifecycle-metadata.db"
    return f"sqlite+pysqlite:///{database_path}"


@pytest.fixture
def sql_engine(db_url: str) -> Iterator[Engine]:
    apply_migrations(db_url)
    engine = sa.create_engine(db_url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:  # pyright: ignore[reportUnusedFunction]
            del connection_record
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    try:
        yield engine
    finally:
        engine.dispose()


class DocumentOverrides(TypedDict, total=False):
    title: str
    filename: str
    uploaded_at: datetime
    ingest_status: ProcessingStatus
    storage_ref: str
    metadata: dict[str, str] | None


class DocumentFactory(Protocol):
    def __call__(
        self,
        doc_id: DocId = "doc-1",
        workspace_id: WorkspaceId = "workspace-1",
        source_type: SourceType = SourceType.PDF,
        **overrides: Unpack[DocumentOverrides],
    ) -> Document: ...


@pytest.fixture
def document_factory() -> DocumentFactory:
    def make(
        doc_id: DocId = "doc-1",
        workspace_id: WorkspaceId = "workspace-1",
        source_type: SourceType = SourceType.PDF,
        **overrides: Unpack[DocumentOverrides],
    ) -> Document:
        filename = f"{doc_id}.pdf" if source_type is SourceType.PDF else f"{doc_id}.md"
        base: dict[str, Any] = {
            "doc_id": doc_id,
            "workspace_id": workspace_id,
            "source_type": source_type,
            "title": f"Title for {doc_id}",
            "filename": filename,
            "uploaded_at": datetime(2026, 3, 8, tzinfo=UTC),
            "ingest_status": ProcessingStatus.READY,
            "storage_ref": f"file:///tmp/{doc_id}",
            "metadata": {"origin": "test"},
        }
        base.update(overrides)
        return Document(**base)

    return make


class SectionOverrides(TypedDict, total=False):
    heading_path: list[str]
    depth: int
    parent_section_id: str | None
    heading_text: str | None
    page_start: int | None
    page_end: int | None
    source_start_offset: int | None
    source_end_offset: int | None
    structure_confidence: float | None


class SectionFactory(Protocol):
    def __call__(
        self,
        doc_id: DocId = "doc-1",
        section_id: str = "section-1",
        **overrides: Unpack[SectionOverrides],
    ) -> Section: ...


@pytest.fixture
def section_factory() -> SectionFactory:
    def make(
        doc_id: DocId = "doc-1",
        section_id: str = "section-1",
        **overrides: Unpack[SectionOverrides],
    ) -> Section:
        base: dict[str, Any] = {
            "section_id": section_id,
            "doc_id": doc_id,
            "heading_path": ["Chapter 1"],
            "depth": 0,
            "heading_text": "Chapter 1",
            "page_start": 1,
            "page_end": 1,
        }
        base.update(overrides)
        return Section(**base)

    return make


class ChunkOverrides(TypedDict, total=False):
    text: str
    ordinal: int
    heading_path: list[str]
    section_id: str | None
    page_start: int | None
    page_end: int | None
    source_start_offset: int | None
    source_end_offset: int | None
    lineage: dict[str, Any] | None
    debug_metadata: dict[str, Any] | None


class ChunkFactory(Protocol):
    def __call__(
        self,
        doc_id: DocId = "doc-1",
        chunk_id: str = "chunk-1",
        **overrides: Unpack[ChunkOverrides],
    ) -> Chunk: ...


@pytest.fixture
def chunk_factory() -> ChunkFactory:
    def make(
        doc_id: DocId = "doc-1",
        chunk_id: str = "chunk-1",
        **overrides: Unpack[ChunkOverrides],
    ) -> Chunk:
        base: dict[str, Any] = {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "text": "Consensus requires stable coordination for replicated state.",
            "ordinal": 0,
            "heading_path": ["Chapter 1", "Overview"],
            "page_start": 2,
            "page_end": 2,
            "source_start_offset": 10,
            "source_end_offset": 65,
        }
        base.update(overrides)
        return Chunk(**base)

    return make


class PersistedDocumentOverrides(TypedDict, total=False):
    title: str
    filename: str
    uploaded_at: datetime
    ingest_status: ProcessingStatus
    storage_ref: str
    metadata_json: dict[str, str] | None
    checksum: str | None
    raw_storage_path: str | None
    failure_code: str | None
    failure_detail: str | None
    created_at: datetime
    updated_at: datetime


class PersistedDocumentFactory(Protocol):
    def __call__(
        self,
        doc_id: DocId = "doc-1",
        workspace_id: WorkspaceId = "workspace-1",
        source_type: SourceType = SourceType.PDF,
        **overrides: Unpack[PersistedDocumentOverrides],
    ) -> PersistedDocument: ...


@pytest.fixture
def persisted_document_factory() -> PersistedDocumentFactory:
    def make(
        doc_id: DocId = "doc-1",
        workspace_id: WorkspaceId = "workspace-1",
        source_type: SourceType = SourceType.PDF,
        **overrides: Unpack[PersistedDocumentOverrides],
    ) -> PersistedDocument:
        filename = f"{doc_id}.pdf" if source_type is SourceType.PDF else f"{doc_id}.md"
        base: dict[str, Any] = {
            "doc_id": doc_id,
            "workspace_id": workspace_id,
            "source_type": source_type,
            "title": f"Title for {doc_id}",
            "filename": filename,
            "uploaded_at": datetime(2026, 3, 8, tzinfo=UTC),
            "ingest_status": ProcessingStatus.REGISTERED,
            "storage_ref": f"file:///tmp/{filename}",
            "metadata_json": {"origin": "test"},
            "checksum": "sha256:abc",
            "raw_storage_path": f"raw/{workspace_id}/{doc_id}/{filename}",
            "created_at": datetime(2026, 3, 8, 1, tzinfo=UTC),
            "updated_at": datetime(2026, 3, 8, 1, tzinfo=UTC),
        }
        base.update(overrides)
        return PersistedDocument(**base)

    return make


class LifecycleEventOverrides(TypedDict, total=False):
    stage: LifecycleStage
    from_status: ProcessingStatus | None
    to_status: ProcessingStatus
    occurred_at: datetime
    failure_category: FailureCategory | None
    detail: dict[str, str]


class LifecycleEventFactory(Protocol):
    def __call__(
        self,
        doc_id: DocId = "doc-1",
        event_id: str = "event-1",
        **overrides: Unpack[LifecycleEventOverrides],
    ) -> LifecycleEvent: ...


@pytest.fixture
def lifecycle_event_factory() -> LifecycleEventFactory:
    def make(
        doc_id: DocId = "doc-1",
        event_id: str = "event-1",
        **overrides: Unpack[LifecycleEventOverrides],
    ) -> LifecycleEvent:
        base: dict[str, Any] = {
            "event_id": event_id,
            "doc_id": doc_id,
            "stage": LifecycleStage.REGISTER,
            "from_status": ProcessingStatus.UPLOADED,
            "to_status": ProcessingStatus.REGISTERED,
            "occurred_at": datetime(2026, 3, 8, 2, tzinfo=UTC),
            "detail": {"origin": "test"},
        }
        base.update(overrides)
        return LifecycleEvent(**base)

    return make


class DocumentJobOverrides(TypedDict, total=False):
    target_stage: DocumentJobStage
    status: DocumentJobStatus
    attempt_count: int
    not_before: datetime | None
    error_code: str | None
    error_detail: str | None
    created_at: datetime
    updated_at: datetime


class DocumentJobFactory(Protocol):
    def __call__(
        self,
        doc_id: DocId = "doc-1",
        job_id: str = "job-1",
        **overrides: Unpack[DocumentJobOverrides],
    ) -> DocumentJob: ...


@pytest.fixture
def document_job_factory() -> DocumentJobFactory:
    def make(
        doc_id: DocId = "doc-1",
        job_id: str = "job-1",
        **overrides: Unpack[DocumentJobOverrides],
    ) -> DocumentJob:
        base: dict[str, Any] = {
            "job_id": job_id,
            "doc_id": doc_id,
            "target_stage": DocumentJobStage.EXTRACT,
            "status": DocumentJobStatus.QUEUED,
            "attempt_count": 0,
            "not_before": datetime(2026, 3, 8, 3, tzinfo=UTC),
            "error_code": None,
            "error_detail": None,
            "created_at": datetime(2026, 3, 8, 3, tzinfo=UTC),
            "updated_at": datetime(2026, 3, 8, 3, tzinfo=UTC),
        }
        base.update(overrides)
        return DocumentJob(**base)

    return make
