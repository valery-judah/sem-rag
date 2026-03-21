"""Worker loop for queued lifecycle stage execution."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from time import perf_counter
from typing import NotRequired
from uuid import uuid4

import structlog
from typing_extensions import TypedDict

from doc_forge.app.log_events import LogEvent
from doc_forge.app.logging import get_logger
from doc_forge.identifiers import DocId
from doc_forge.lifecycle import (
    FailureCategory,
    LifecycleEvent,
    LifecycleInvariantError,
    LifecycleStage,
    ProcessingStatus,
    require_processing_status_transition,
)
from doc_forge.persistence import (
    DocumentJob,
    DocumentJobRepository,
    DocumentJobStage,
    DocumentRepository,
    LifecycleEventRepository,
)
from doc_forge.stages.base import StageExecutionError, StageRunner

from .orchestrator import DocumentLifecycleOrchestrator

_JOB_STAGE_TO_LIFECYCLE_STAGE: dict[DocumentJobStage, LifecycleStage] = {
    DocumentJobStage.REGISTER: LifecycleStage.REGISTER,
    DocumentJobStage.EXTRACT: LifecycleStage.EXTRACT,
    DocumentJobStage.NORMALIZE: LifecycleStage.NORMALIZE,
    DocumentJobStage.SECTIONIZE: LifecycleStage.CHUNK,
    DocumentJobStage.CHUNK: LifecycleStage.CHUNK,
    DocumentJobStage.INDEX: LifecycleStage.INDEX,
    DocumentJobStage.READY_CHECK: LifecycleStage.READINESS,
}


logger = get_logger(__name__)


class WorkerLogContext(TypedDict):
    worker_id: NotRequired[str]
    queue_name: NotRequired[str]


class WorkerLogger:
    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._logger = logger

    def run_next_invoked(self) -> None:
        self._logger.info(LogEvent.WORKER_RUN_NEXT_INVOKED)

    def run_next_idle(self) -> None:
        self._logger.info(LogEvent.WORKER_RUN_NEXT_IDLE)

    def job_claimed(self, doc_id: DocId, job_id: str, target_stage: str, status: str) -> None:
        self._logger.info(
            LogEvent.WORKER_JOB_CLAIMED,
            doc_id=doc_id,
            job_id=job_id,
            target_stage=target_stage,
            status=status,
        )

    def job_started(self, doc_id: DocId, job_id: str, target_stage: str, status: str) -> None:
        self._logger.info(
            LogEvent.WORKER_JOB_STARTED,
            doc_id=doc_id,
            job_id=job_id,
            target_stage=target_stage,
            status=status,
        )

    def job_succeeded(
        self,
        doc_id: DocId,
        job_id: str,
        target_stage: str,
        status: str,
        duration_ms: int,
        next_stage: str | None = None,
    ) -> None:
        self._logger.info(
            LogEvent.WORKER_JOB_SUCCEEDED,
            doc_id=doc_id,
            job_id=job_id,
            target_stage=target_stage,
            next_stage=next_stage,
            status=status,
            duration_ms=duration_ms,
        )

    def job_failed(
        self,
        doc_id: DocId,
        job_id: str,
        target_stage: str,
        status: str,
        error_code: str,
        failure_category: str,
    ) -> None:
        self._logger.warning(
            LogEvent.WORKER_JOB_FAILED,
            doc_id=doc_id,
            job_id=job_id,
            target_stage=target_stage,
            status=status,
            error_code=error_code,
            failure_category=failure_category,
        )


class DocumentLifecycleWorker:
    """Claim queued jobs, dispatch stage runners, and record failures."""

    def __init__(
        self,
        *,
        jobs: DocumentJobRepository,
        documents: DocumentRepository,
        lifecycle_events: LifecycleEventRepository,
        orchestrator: DocumentLifecycleOrchestrator,
        stage_runners: dict[DocumentJobStage, StageRunner],
        logger: WorkerLogger | None = None,
    ) -> None:
        self._jobs = jobs
        self._documents = documents
        self._lifecycle_events = lifecycle_events
        self._orchestrator = orchestrator
        self._stage_runners = stage_runners
        self._logger = logger or WorkerLogger(get_logger(self.__class__.__name__))

    def run_next(self) -> DocumentJob | None:
        """Run the next queued job and return its terminal job record."""

        self._logger.run_next_invoked()
        job = self._jobs.claim_next()
        if job is None:
            self._logger.run_next_idle()
            return None
        started_at = perf_counter()
        self._logger.job_claimed(
            doc_id=job.doc_id,
            job_id=job.job_id,
            target_stage=job.target_stage.value,
            status=job.status.value,
        )

        runner = self._stage_runners.get(job.target_stage)
        if runner is None:
            return self._fail_job(
                job,
                StageExecutionError(
                    error_code="missing_stage_runner",
                    error_detail=f"no stage runner registered for {job.target_stage.value}",
                    failure_category=FailureCategory.INTERNAL,
                ),
            )

        try:
            self._logger.job_started(
                doc_id=job.doc_id,
                job_id=job.job_id,
                target_stage=job.target_stage.value,
                status=job.status.value,
            )
            next_stage = runner.run(job)
        except StageExecutionError as exc:
            return self._fail_job(job, exc)
        except Exception as exc:  # pragma: no cover - unexpected safety net
            return self._fail_job(
                job,
                StageExecutionError(
                    error_code="internal_stage_error",
                    error_detail=str(exc),
                    failure_category=FailureCategory.INTERNAL,
                ),
            )

        completed = self._jobs.mark_succeeded(job.job_id)
        if next_stage is not None:
            self._orchestrator.enqueue_stage(doc_id=job.doc_id, target_stage=next_stage)
        self._logger.job_succeeded(
            doc_id=job.doc_id,
            job_id=job.job_id,
            target_stage=job.target_stage.value,
            next_stage=None if next_stage is None else next_stage.value,
            status=completed.status.value,
            duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
        )
        return completed

    def _fail_job(self, job: DocumentJob, exc: StageExecutionError) -> DocumentJob:
        failed_job = self._jobs.mark_failed(
            job.job_id,
            error_code=exc.error_code,
            error_detail=exc.error_detail,
        )
        document = self._documents.get(job.doc_id)
        if document is None:
            return failed_job
        if document.ingest_status is ProcessingStatus.FAILED:
            return failed_job

        try:
            require_processing_status_transition(
                document.ingest_status,
                ProcessingStatus.FAILED,
            )
        except LifecycleInvariantError:
            return failed_job

        failed_at = datetime.now(UTC)
        self._documents.update_status(
            doc_id=job.doc_id,
            status=ProcessingStatus.FAILED,
            failure_code=exc.error_code,
            failure_detail=exc.error_detail,
            updated_at=failed_at,
        )
        self._lifecycle_events.append(
            LifecycleEvent(
                event_id=f"event_{uuid4().hex}",
                doc_id=job.doc_id,
                stage=_JOB_STAGE_TO_LIFECYCLE_STAGE[job.target_stage],
                from_status=document.ingest_status,
                to_status=ProcessingStatus.FAILED,
                occurred_at=failed_at,
                failure_category=exc.failure_category,
                detail={
                    "job_stage": job.target_stage.value,
                    "error_code": exc.error_code,
                    "error_detail": exc.error_detail,
                },
            )
        )
        self._logger.job_failed(
            doc_id=job.doc_id,
            job_id=job.job_id,
            target_stage=job.target_stage.value,
            status=failed_job.status.value,
            error_code=exc.error_code,
            failure_category=exc.failure_category.value,
        )
        return failed_job


def main() -> None:
    """Run the internal lifecycle worker loop."""

    from doc_forge.app.deps import (
        _build_artifact_store,  # pyright: ignore[reportPrivateUsage]
        _build_engine,  # pyright: ignore[reportPrivateUsage]
        get_document_lifecycle_worker,
    )
    from doc_forge.app.settings import get_settings

    settings = get_settings()
    worker = get_document_lifecycle_worker(
        engine=_build_engine(settings.database_url),
        artifact_store=_build_artifact_store(str(settings.artifact_root)),
    )
    poll_seconds = settings.worker_poll_seconds
    while True:
        job = worker.run_next()
        if job is None:
            time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
