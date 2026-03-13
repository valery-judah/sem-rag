"""Readiness stage for indexed documents."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from doc_forge.app.logging import get_logger
from doc_forge.lifecycle import LifecycleEvent, LifecycleStage, ProcessingStatus
from doc_forge.lifecycle.readiness import ReadinessService
from doc_forge.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentRepository,
    LifecycleEventRepository,
)
from doc_forge.stages.base import StageExecutionError, StageLogger, StageRunner

logger = get_logger(__name__)


class ReadyDocumentStage(StageRunner):
    """Promote indexed documents to READY only after persisted checks pass."""

    target_stage = DocumentJobStage.READY_CHECK

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        lifecycle_events: LifecycleEventRepository,
        readiness: ReadinessService,
        logger: StageLogger | None = None,
    ) -> None:
        self._documents = documents
        self._lifecycle_events = lifecycle_events
        self._readiness = readiness
        self._logger = logger or StageLogger(get_logger(self.__class__.__name__))

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        started_at = perf_counter()
        self._logger.stage_started(
            stage_name="ready_check",
            doc_id=job.doc_id,
            job_id=job.job_id,
        )
        document = self._documents.get(job.doc_id)
        if document is None:
            self._logger.stage_failed(
                stage_name="ready_check",
                doc_id=job.doc_id,
                job_id=job.job_id,
                duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
                error_code="missing_document",
            )
            raise StageExecutionError(
                error_code="missing_document",
                error_detail=f"document {job.doc_id!r} was not found",
            )
        if document.ingest_status is not ProcessingStatus.INDEXED:
            self._logger.stage_failed(
                stage_name="ready_check",
                doc_id=job.doc_id,
                job_id=job.job_id,
                duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
                error_code="invalid_document_status",
            )
            raise StageExecutionError(
                error_code="invalid_document_status",
                error_detail=(
                    f"ready stage requires indexed document, got {document.ingest_status.value}"
                ),
            )
        result = self._readiness.evaluate(doc_id=document.doc_id)
        if not result.is_ready:
            self._logger.stage_failed(
                stage_name="ready_check",
                doc_id=document.doc_id,
                job_id=job.job_id,
                duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
                error_code="readiness_check_failed",
                reasons=result.reasons,
                section_count=result.section_count,
                chunk_count=result.chunk_count,
                index_entry_count=result.index_entry_count,
            )
            raise StageExecutionError(
                error_code="readiness_check_failed",
                error_detail=", ".join(result.reasons),
            )
        completed_at = datetime.now(UTC)
        self._documents.update_status(
            doc_id=document.doc_id,
            status=ProcessingStatus.READY,
            updated_at=completed_at,
        )
        self._lifecycle_events.append(
            LifecycleEvent(
                event_id=f"event_{uuid4().hex}",
                doc_id=document.doc_id,
                stage=LifecycleStage.READINESS,
                from_status=ProcessingStatus.INDEXED,
                to_status=ProcessingStatus.READY,
                occurred_at=completed_at,
                detail={
                    "section_count": str(result.section_count),
                    "chunk_count": str(result.chunk_count),
                    "index_entry_count": str(result.index_entry_count),
                },
            )
        )
        self._logger.stage_completed(
            stage_name="ready_check",
            doc_id=document.doc_id,
            job_id=job.job_id,
            duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
            section_count=result.section_count,
            chunk_count=result.chunk_count,
            index_entry_count=result.index_entry_count,
        )
        return None
