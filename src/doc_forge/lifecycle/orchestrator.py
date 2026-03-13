"""Document-scoped job orchestration helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import structlog

from doc_forge.app.log_events import LogEvent
from doc_forge.app.logging import get_logger
from doc_forge.identifiers import DocId
from doc_forge.persistence import DocumentJob, DocumentJobRepository, DocumentJobStage

_NEXT_STAGE: dict[DocumentJobStage, DocumentJobStage | None] = {
    DocumentJobStage.EXTRACT: DocumentJobStage.NORMALIZE,
    DocumentJobStage.NORMALIZE: DocumentJobStage.SECTIONIZE,
    DocumentJobStage.SECTIONIZE: DocumentJobStage.CHUNK,
    DocumentJobStage.CHUNK: DocumentJobStage.INDEX,
    DocumentJobStage.INDEX: DocumentJobStage.READY_CHECK,
    DocumentJobStage.READY_CHECK: None,
}


logger = get_logger(__name__)


class OrchestratorLogger:
    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._logger = logger

    def enqueue_skipped(self, doc_id: DocId, target_stage: str, error_code: str) -> None:
        self._logger.warning(
            LogEvent.WORKER_JOB_ENQUEUE_SKIPPED,
            doc_id=doc_id,
            target_stage=target_stage,
            error_code=error_code,
        )

    def enqueued(self, doc_id: DocId, job_id: str, target_stage: str, status: str) -> None:
        self._logger.info(
            LogEvent.WORKER_JOB_ENQUEUED,
            doc_id=doc_id,
            job_id=job_id,
            target_stage=target_stage,
            status=status,
        )


class DocumentLifecycleOrchestrator:
    """Own queued stage creation and next-stage sequencing."""

    def __init__(
        self,
        *,
        jobs: DocumentJobRepository,
        logger: OrchestratorLogger | None = None,
    ) -> None:
        self._jobs = jobs
        self._logger = logger or OrchestratorLogger(get_logger(self.__class__.__name__))

    def enqueue_stage(self, *, doc_id: DocId, target_stage: DocumentJobStage) -> DocumentJob | None:
        """Queue the next job when no active work already exists for the document."""

        if self._jobs.has_active_job(doc_id):
            self._logger.enqueue_skipped(
                doc_id=doc_id, target_stage=target_stage.value, error_code="active_job_exists"
            )
            return None
        queued_at = datetime.now(UTC)
        job = DocumentJob(
            job_id=f"job_{uuid4().hex}",
            doc_id=doc_id,
            target_stage=target_stage,
            created_at=queued_at,
            updated_at=queued_at,
        )
        self._jobs.create(job)
        self._logger.enqueued(
            doc_id=doc_id,
            job_id=job.job_id,
            target_stage=target_stage.value,
            status=job.status.value,
        )
        return job

    def next_stage(self, target_stage: DocumentJobStage) -> DocumentJobStage | None:
        """Return the next queued stage for a successful job."""

        return _NEXT_STAGE[target_stage]
