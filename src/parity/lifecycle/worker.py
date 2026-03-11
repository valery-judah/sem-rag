"""Worker loop for queued lifecycle stage execution."""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from uuid import uuid4

from parity.lifecycle import (
    FailureCategory,
    LifecycleEvent,
    LifecycleInvariantError,
    LifecycleStage,
    ProcessingStatus,
    require_processing_status_transition,
)
from parity.persistence import (
    DocumentJob,
    DocumentJobRepository,
    DocumentJobStage,
    DocumentRepository,
    LifecycleEventRepository,
)
from parity.stages.base import StageExecutionError, StageRunner

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
    ) -> None:
        self._jobs = jobs
        self._documents = documents
        self._lifecycle_events = lifecycle_events
        self._orchestrator = orchestrator
        self._stage_runners = stage_runners

    def run_next(self) -> DocumentJob | None:
        """Run the next queued job and return its terminal job record."""

        job = self._jobs.claim_next()
        if job is None:
            return None

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
        return failed_job


def main() -> None:
    """Run the internal lifecycle worker loop."""

    from parity.app.deps import (
        _build_artifact_store,
        _build_engine,
        get_document_lifecycle_worker,
    )
    from parity.app.settings import load_settings

    settings = load_settings()
    worker = get_document_lifecycle_worker(
        engine=_build_engine(settings.database_url),
        artifact_store=_build_artifact_store(str(settings.artifact_root)),
    )
    poll_seconds = float(os.environ.get("PARITY_WORKER_POLL_SECONDS", "0.25"))
    while True:
        job = worker.run_next()
        if job is None:
            time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
