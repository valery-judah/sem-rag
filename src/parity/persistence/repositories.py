"""Repository protocols and SQLAlchemy implementations for lifecycle metadata."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

import sqlalchemy as sa
from sqlalchemy.engine import Connection, Engine

from parity._contracts import Chunk, ProcessingStatus, Section
from parity.lifecycle.models import LifecycleEvent

from .jobs import DocumentJob, document_job_to_row, document_jobs_table, row_to_document_job
from .models import (
    PersistedChunk,
    PersistedDocument,
    PersistedDocumentStatusUpdate,
    PersistedSection,
    chunks_table,
    documents_table,
    lifecycle_event_to_row,
    lifecycle_events_table,
    persisted_chunk_to_row,
    persisted_section_to_row,
    row_to_lifecycle_event,
    row_to_persisted_chunk,
    row_to_persisted_document,
    row_to_persisted_section,
    sections_table,
    utc_now,
)


class DocumentRepository(Protocol):
    """Storage operations for durable document metadata."""

    def create(
        self,
        document: PersistedDocument,
        *,
        connection: Connection | None = None,
    ) -> None: ...

    def get(
        self,
        doc_id: str,
        *,
        connection: Connection | None = None,
    ) -> PersistedDocument | None: ...

    def list_by_workspace(self, workspace_id: str) -> list[PersistedDocument]: ...

    def update_status(
        self,
        *,
        doc_id: str,
        status: ProcessingStatus,
        failure_code: str | None = None,
        failure_detail: str | None = None,
        updated_at: datetime | None = None,
    ) -> None: ...


class LifecycleEventRepository(Protocol):
    """Append-only event log operations for lifecycle transitions."""

    def append(
        self,
        event: LifecycleEvent,
        *,
        connection: Connection | None = None,
    ) -> None: ...

    def list_for_document(self, doc_id: str) -> list[LifecycleEvent]: ...


class DocumentJobRepository(Protocol):
    """Storage operations for document-scoped queued work records."""

    def create(self, job: DocumentJob) -> None: ...

    def get(self, job_id: str) -> DocumentJob | None: ...

    def list_for_document(self, doc_id: str) -> list[DocumentJob]: ...

    def update(self, job: DocumentJob) -> None: ...


class SectionRepository(Protocol):
    """Storage operations for document sections."""

    def save(self, sections: list[Section]) -> None: ...

    def list_for_document(self, doc_id: str) -> list[Section]: ...

    def replace_for_document(self, doc_id: str, sections: list[Section]) -> None: ...


class ChunkRepository(Protocol):
    """Storage operations for document chunks."""

    def save(self, chunks: list[Chunk]) -> None: ...

    def list_for_document(self, doc_id: str) -> list[Chunk]: ...

    def replace_for_document(self, doc_id: str, chunks: list[Chunk]) -> None: ...


class SqlDocumentRepository:
    """SQLAlchemy-backed document metadata repository."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create(
        self,
        document: PersistedDocument,
        *,
        connection: Connection | None = None,
    ) -> None:
        if connection is not None:
            connection.execute(sa.insert(documents_table), [document.to_row()])
            return
        with self._engine.begin() as conn:
            conn.execute(sa.insert(documents_table), [document.to_row()])

    def get(
        self,
        doc_id: str,
        *,
        connection: Connection | None = None,
    ) -> PersistedDocument | None:
        stmt = sa.select(documents_table).where(documents_table.c.doc_id == doc_id)
        if connection is not None:
            row = connection.execute(stmt).mappings().first()
        else:
            with self._engine.begin() as conn:
                row = conn.execute(stmt).mappings().first()
        if row is None:
            return None
        return row_to_persisted_document(dict(row))

    def list_by_workspace(self, workspace_id: str) -> list[PersistedDocument]:
        stmt = (
            sa.select(documents_table)
            .where(documents_table.c.workspace_id == workspace_id)
            .order_by(documents_table.c.doc_id)
        )
        with self._engine.begin() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [row_to_persisted_document(dict(row)) for row in rows]

    def update_status(
        self,
        *,
        doc_id: str,
        status: ProcessingStatus,
        failure_code: str | None = None,
        failure_detail: str | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        values = PersistedDocumentStatusUpdate.for_status(
            status=status,
            failure_code=failure_code,
            failure_detail=failure_detail,
            updated_at=updated_at or utc_now(),
        ).to_row()

        stmt = (
            sa.update(documents_table)
            .where(documents_table.c.doc_id == doc_id)
            .values(**values)
        )
        with self._engine.begin() as conn:
            result = conn.execute(stmt)
        if result.rowcount != 1:
            raise LookupError(f"document {doc_id!r} was not found")


class SqlLifecycleEventRepository:
    """SQLAlchemy-backed lifecycle event repository."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def append(
        self,
        event: LifecycleEvent,
        *,
        connection: Connection | None = None,
    ) -> None:
        if connection is not None:
            connection.execute(
                sa.insert(lifecycle_events_table),
                [lifecycle_event_to_row(event)],
            )
            return
        with self._engine.begin() as conn:
            conn.execute(sa.insert(lifecycle_events_table), [lifecycle_event_to_row(event)])

    def list_for_document(self, doc_id: str) -> list[LifecycleEvent]:
        stmt = (
            sa.select(lifecycle_events_table)
            .where(lifecycle_events_table.c.doc_id == doc_id)
            .order_by(
                lifecycle_events_table.c.occurred_at,
                lifecycle_events_table.c.event_id,
            )
        )
        with self._engine.begin() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [row_to_lifecycle_event(dict(row)) for row in rows]


class SqlDocumentJobRepository:
    """SQLAlchemy-backed repository for queued document jobs."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create(self, job: DocumentJob) -> None:
        with self._engine.begin() as conn:
            conn.execute(sa.insert(document_jobs_table), [document_job_to_row(job)])

    def get(self, job_id: str) -> DocumentJob | None:
        stmt = sa.select(document_jobs_table).where(document_jobs_table.c.job_id == job_id)
        with self._engine.begin() as conn:
            row = conn.execute(stmt).mappings().first()
        if row is None:
            return None
        return row_to_document_job(dict(row))

    def list_for_document(self, doc_id: str) -> list[DocumentJob]:
        stmt = (
            sa.select(document_jobs_table)
            .where(document_jobs_table.c.doc_id == doc_id)
            .order_by(document_jobs_table.c.created_at, document_jobs_table.c.job_id)
        )
        with self._engine.begin() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [row_to_document_job(dict(row)) for row in rows]

    def update(self, job: DocumentJob) -> None:
        stmt = (
            sa.update(document_jobs_table)
            .where(document_jobs_table.c.job_id == job.job_id)
            .values(**document_job_to_row(job))
        )
        with self._engine.begin() as conn:
            result = conn.execute(stmt)
        if result.rowcount != 1:
            raise LookupError(f"document job {job.job_id!r} was not found")


class SqlSectionRepository:
    """SQLAlchemy-backed repository for document sections."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(self, sections: list[Section]) -> None:
        rows = [
            persisted_section_to_row(PersistedSection.from_contract(section))
            for section in sections
        ]
        if not rows:
            return
        with self._engine.begin() as conn:
            conn.execute(sa.insert(sections_table), rows)

    def list_for_document(self, doc_id: str) -> list[Section]:
        stmt = (
            sa.select(sections_table)
            .where(sections_table.c.doc_id == doc_id)
            .order_by(sections_table.c.depth, sections_table.c.section_id)
        )
        with self._engine.begin() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [row_to_persisted_section(dict(row)).to_contract() for row in rows]

    def replace_for_document(self, doc_id: str, sections: list[Section]) -> None:
        _require_matching_doc_id(doc_id, sections)
        with self._engine.begin() as conn:
            conn.execute(sa.delete(sections_table).where(sections_table.c.doc_id == doc_id))
            if sections:
                self._insert_sections(conn, sections)

    def _insert_sections(self, conn: Connection, sections: list[Section]) -> None:
        rows = [
            persisted_section_to_row(PersistedSection.from_contract(section))
            for section in sections
        ]
        conn.execute(sa.insert(sections_table), rows)


class SqlChunkRepository:
    """SQLAlchemy-backed repository for document chunks."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(self, chunks: list[Chunk]) -> None:
        rows = [persisted_chunk_to_row(PersistedChunk.from_contract(chunk)) for chunk in chunks]
        if not rows:
            return
        with self._engine.begin() as conn:
            conn.execute(sa.insert(chunks_table), rows)

    def list_for_document(self, doc_id: str) -> list[Chunk]:
        stmt = (
            sa.select(chunks_table)
            .where(chunks_table.c.doc_id == doc_id)
            .order_by(chunks_table.c.ordinal, chunks_table.c.chunk_id)
        )
        with self._engine.begin() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [row_to_persisted_chunk(dict(row)).to_contract() for row in rows]

    def replace_for_document(self, doc_id: str, chunks: list[Chunk]) -> None:
        _require_matching_doc_id(doc_id, chunks)
        with self._engine.begin() as conn:
            conn.execute(sa.delete(chunks_table).where(chunks_table.c.doc_id == doc_id))
            if chunks:
                self._insert_chunks(conn, chunks)

    def _insert_chunks(self, conn: Connection, chunks: list[Chunk]) -> None:
        rows = [persisted_chunk_to_row(PersistedChunk.from_contract(chunk)) for chunk in chunks]
        conn.execute(sa.insert(chunks_table), rows)


def _require_matching_doc_id(doc_id: str, records: list[Section] | list[Chunk]) -> None:
    if any(record.doc_id != doc_id for record in records):
        raise ValueError("all persisted records must belong to the target document")
