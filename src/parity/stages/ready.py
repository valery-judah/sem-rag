"""Readiness stage for indexed documents."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from parity.lifecycle import LifecycleEvent, LifecycleStage, ProcessingStatus
from parity.lifecycle.readiness import ReadinessService
from parity.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentRepository,
    LifecycleEventRepository,
)
from parity.stages.base import StageExecutionError, StageRunner


class ReadyDocumentStage(StageRunner):
    """Promote indexed documents to READY only after persisted checks pass."""

    target_stage = DocumentJobStage.READY_CHECK

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        lifecycle_events: LifecycleEventRepository,
        readiness: ReadinessService,
    ) -> None:
        self._documents = documents
        self._lifecycle_events = lifecycle_events
        self._readiness = readiness

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        document = self._documents.get(job.doc_id)
        if document is None:
            raise StageExecutionError(
                error_code="missing_document",
                error_detail=f"document {job.doc_id!r} was not found",
            )
        if document.ingest_status is not ProcessingStatus.INDEXED:
            raise StageExecutionError(
                error_code="invalid_document_status",
                error_detail=(
                    f"ready stage requires indexed document, got {document.ingest_status.value}"
                ),
            )
        result = self._readiness.evaluate(doc_id=document.doc_id)
        if not result.is_ready:
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
        return None
