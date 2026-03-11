"""Repository protocols and SQLAlchemy implementations for lifecycle metadata."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from parity._contracts import ProcessingStatus
from parity.lifecycle.models import LifecycleEvent

from .jobs import DocumentJob, document_job_to_row, document_jobs_table, row_to_document_job
from .models import (
    PersistedDocument,
    PersistedDocumentStatusUpdate,
    documents_table,
    lifecycle_event_to_row,
    lifecycle_events_table,
    row_to_lifecycle_event,
    row_to_persisted_document,
    utc_now,
)


class DocumentRepository(Protocol):
    """Storage operations for durable document metadata."""

    def create(self, document: PersistedDocument) -> None: ...

    def get(self, doc_id: str) -> PersistedDocument | None: ...

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

    def append(self, event: LifecycleEvent) -> None: ...

    def list_for_document(self, doc_id: str) -> list[LifecycleEvent]: ...


class DocumentJobRepository(Protocol):
    """Storage operations for document-scoped queued work records."""

    def create(self, job: DocumentJob) -> None: ...

    def get(self, job_id: str) -> DocumentJob | None: ...

    def list_for_document(self, doc_id: str) -> list[DocumentJob]: ...

    def update(self, job: DocumentJob) -> None: ...


class SqlDocumentRepository:
    """SQLAlchemy-backed document metadata repository."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create(self, document: PersistedDocument) -> None:
        with self._engine.begin() as conn:
            conn.execute(sa.insert(documents_table), [document.to_row()])

    def get(self, doc_id: str) -> PersistedDocument | None:
        stmt = sa.select(documents_table).where(documents_table.c.doc_id == doc_id)
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

    def append(self, event: LifecycleEvent) -> None:
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
