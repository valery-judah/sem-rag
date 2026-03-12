from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.engine import Engine

from doc_forge.corpus import Chunk, Document, Section, SourceType
from doc_forge.identifiers import DocId, WorkspaceId
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.lifecycle.models import LifecycleEvent, LifecycleStage
from doc_forge.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentJobStatus,
    PersistedDocument,
    apply_migrations,
)


@pytest.fixture
def db_url(tmp_path) -> str:
    database_path = tmp_path / "lifecycle-metadata.db"
    return f"sqlite+pysqlite:///{database_path}"


@pytest.fixture
def sql_engine(db_url: str) -> Iterator[Engine]:
    apply_migrations(db_url)
    engine = sa.create_engine(db_url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
            del connection_record
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def document_factory():
    def make(
        doc_id: DocId = "doc-1",
        workspace_id: WorkspaceId = "workspace-1",
        source_type: SourceType = SourceType.PDF,
        **overrides: object,
    ) -> Document:
        filename = f"{doc_id}.pdf" if source_type is SourceType.PDF else f"{doc_id}.md"
        base = {
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


@pytest.fixture
def section_factory():
    def make(
        doc_id: DocId = "doc-1",
        section_id: str = "section-1",
        **overrides: object,
    ) -> Section:
        base = {
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


@pytest.fixture
def chunk_factory():
    def make(
        doc_id: DocId = "doc-1",
        chunk_id: str = "chunk-1",
        **overrides: object,
    ) -> Chunk:
        base = {
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


@pytest.fixture
def persisted_document_factory():
    def make(
        doc_id: DocId = "doc-1",
        workspace_id: WorkspaceId = "workspace-1",
        source_type: SourceType = SourceType.PDF,
        **overrides: object,
    ) -> PersistedDocument:
        filename = f"{doc_id}.pdf" if source_type is SourceType.PDF else f"{doc_id}.md"
        base = {
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


@pytest.fixture
def lifecycle_event_factory():
    def make(
        doc_id: DocId = "doc-1",
        event_id: str = "event-1",
        **overrides: object,
    ) -> LifecycleEvent:
        base = {
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


@pytest.fixture
def document_job_factory():
    def make(
        doc_id: DocId = "doc-1",
        job_id: str = "job-1",
        **overrides: object,
    ) -> DocumentJob:
        base = {
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
