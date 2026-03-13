from __future__ import annotations

from typing import Any, cast

import pytest

from doc_forge.app.logging import configure_logging, reset_logging
from doc_forge.lifecycle import FailureCategory, ProcessingStatus
from doc_forge.lifecycle.orchestrator import DocumentLifecycleOrchestrator
from doc_forge.lifecycle.worker import DocumentLifecycleWorker
from doc_forge.persistence import DocumentJobStage, DocumentJobStatus
from tests.lifecycle.support import (
    FailingStageRunner,
    InMemoryDocumentRepository,
    InMemoryJobRepository,
    InMemoryLifecycleEventRepository,
    SuccessfulStageRunner,
    make_job,
    make_persisted_document,
    make_stage_error,
)


@pytest.fixture(autouse=True)
def _configured_logging() -> None:
    reset_logging()
    configure_logging(service="test-service", environment="test", level="INFO")
    yield
    reset_logging()


def _structured_logs(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [
        cast(dict[str, Any], record.msg)
        for record in caplog.records
        if isinstance(record.msg, dict)
    ]


def test_run_next_returns_none_when_queue_is_empty(caplog: pytest.LogCaptureFixture) -> None:
    jobs = InMemoryJobRepository()
    worker = DocumentLifecycleWorker(
        jobs=jobs,
        documents=InMemoryDocumentRepository(),
        lifecycle_events=InMemoryLifecycleEventRepository(),
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        stage_runners={},
    )

    assert worker.run_next() is None
    structured_logs = _structured_logs(caplog)
    assert any(log["event"] == "worker.run_next.invoked" for log in structured_logs)
    assert any(log["event"] == "worker.run_next.idle" for log in structured_logs)


def test_worker_marks_job_failed_when_stage_runner_is_missing() -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.REGISTERED,
    )
    jobs = InMemoryJobRepository([make_job(doc_id=document.doc_id)])
    documents = InMemoryDocumentRepository([document])
    lifecycle_events = InMemoryLifecycleEventRepository()
    worker = DocumentLifecycleWorker(
        jobs=jobs,
        documents=documents,
        lifecycle_events=lifecycle_events,
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        stage_runners={},
    )

    result = worker.run_next()

    assert result is not None
    assert result.status is DocumentJobStatus.FAILED
    assert result.error_code == "missing_stage_runner"
    stored = documents.get(document.doc_id)
    assert stored is not None
    assert stored.ingest_status is ProcessingStatus.FAILED
    assert lifecycle_events.appended[0].failure_category is FailureCategory.INTERNAL
    assert lifecycle_events.appended[0].detail["job_stage"] == DocumentJobStage.EXTRACT.value


def test_worker_marks_job_failed_on_stage_execution_error() -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.REGISTERED,
    )
    jobs = InMemoryJobRepository([make_job(doc_id=document.doc_id)])
    documents = InMemoryDocumentRepository([document])
    lifecycle_events = InMemoryLifecycleEventRepository()
    worker = DocumentLifecycleWorker(
        jobs=jobs,
        documents=documents,
        lifecycle_events=lifecycle_events,
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        stage_runners={
            DocumentJobStage.EXTRACT: FailingStageRunner(
                make_stage_error(
                    error_code="extract_failed",
                    error_detail="extract stage failed",
                )
            )
        },
    )

    result = worker.run_next()

    assert result is not None
    assert result.status is DocumentJobStatus.FAILED
    assert result.error_code == "extract_failed"
    assert result.error_detail == "extract stage failed"
    stored = documents.get(document.doc_id)
    assert stored is not None
    assert stored.failure_code == "extract_failed"
    assert lifecycle_events.appended[0].failure_category is FailureCategory.PROCESSING


def test_worker_emits_failed_job_log(caplog: pytest.LogCaptureFixture) -> None:
    document = make_persisted_document(
        doc_id="doc-log-fail",
        ingest_status=ProcessingStatus.REGISTERED,
    )
    jobs = InMemoryJobRepository([make_job(doc_id=document.doc_id)])
    worker = DocumentLifecycleWorker(
        jobs=jobs,
        documents=InMemoryDocumentRepository([document]),
        lifecycle_events=InMemoryLifecycleEventRepository(),
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        stage_runners={
            DocumentJobStage.EXTRACT: FailingStageRunner(
                make_stage_error(
                    error_code="extract_failed",
                    error_detail="extract stage failed",
                )
            )
        },
    )

    result = worker.run_next()

    assert result is not None
    structured_logs = _structured_logs(caplog)
    assert any(
        log["event"] == "worker.job.failed"
        and log["doc_id"] == "doc-log-fail"
        and log["error_code"] == "extract_failed"
        and log["failure_category"] == "processing"
        for log in structured_logs
    )


def test_worker_wraps_unexpected_exception_as_internal_stage_error() -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.REGISTERED,
    )
    jobs = InMemoryJobRepository([make_job(doc_id=document.doc_id)])
    documents = InMemoryDocumentRepository([document])
    lifecycle_events = InMemoryLifecycleEventRepository()
    worker = DocumentLifecycleWorker(
        jobs=jobs,
        documents=documents,
        lifecycle_events=lifecycle_events,
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        stage_runners={DocumentJobStage.EXTRACT: FailingStageRunner(RuntimeError("boom"))},
    )

    result = worker.run_next()

    assert result is not None
    assert result.status is DocumentJobStatus.FAILED
    assert result.error_code == "internal_stage_error"
    assert result.error_detail == "boom"
    assert lifecycle_events.appended[0].failure_category is FailureCategory.INTERNAL


def test_worker_marks_job_succeeded_and_enqueues_next_stage() -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.REGISTERED,
    )
    jobs = InMemoryJobRepository([make_job(doc_id=document.doc_id)])
    runner = SuccessfulStageRunner(next_stage=DocumentJobStage.NORMALIZE)
    worker = DocumentLifecycleWorker(
        jobs=jobs,
        documents=InMemoryDocumentRepository([document]),
        lifecycle_events=InMemoryLifecycleEventRepository(),
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        stage_runners={DocumentJobStage.EXTRACT: runner},
    )

    result = worker.run_next()

    assert result is not None
    assert result.status is DocumentJobStatus.SUCCEEDED
    assert [job.target_stage for job in jobs.list_for_document(document.doc_id)] == [
        DocumentJobStage.EXTRACT,
        DocumentJobStage.NORMALIZE,
    ]
    assert jobs.list_for_document(document.doc_id)[1].status is DocumentJobStatus.QUEUED
    assert runner.calls[0].status is DocumentJobStatus.RUNNING


def test_worker_does_not_enqueue_when_runner_returns_no_next_stage() -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.INDEXED,
    )
    jobs = InMemoryJobRepository(
        [make_job(doc_id=document.doc_id, target_stage=DocumentJobStage.READY_CHECK)]
    )
    worker = DocumentLifecycleWorker(
        jobs=jobs,
        documents=InMemoryDocumentRepository([document]),
        lifecycle_events=InMemoryLifecycleEventRepository(),
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        stage_runners={DocumentJobStage.READY_CHECK: SuccessfulStageRunner(next_stage=None)},
    )

    result = worker.run_next()

    assert result is not None
    assert result.status is DocumentJobStatus.SUCCEEDED
    assert len(jobs.list_for_document(document.doc_id)) == 1


def test_worker_skips_document_status_update_when_document_row_is_missing() -> None:
    jobs = InMemoryJobRepository([make_job(doc_id="missing-doc")])
    documents = InMemoryDocumentRepository()
    lifecycle_events = InMemoryLifecycleEventRepository()
    worker = DocumentLifecycleWorker(
        jobs=jobs,
        documents=documents,
        lifecycle_events=lifecycle_events,
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        stage_runners={DocumentJobStage.EXTRACT: FailingStageRunner(make_stage_error())},
    )

    result = worker.run_next()

    assert result is not None
    assert result.status is DocumentJobStatus.FAILED
    assert documents.status_updates == []
    assert lifecycle_events.appended == []


def test_worker_does_not_append_duplicate_failure_when_document_already_failed() -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.FAILED,
        failure_code="existing_failure",
        failure_detail="existing detail",
    )
    jobs = InMemoryJobRepository([make_job(doc_id=document.doc_id)])
    documents = InMemoryDocumentRepository([document])
    lifecycle_events = InMemoryLifecycleEventRepository()
    worker = DocumentLifecycleWorker(
        jobs=jobs,
        documents=documents,
        lifecycle_events=lifecycle_events,
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        stage_runners={DocumentJobStage.EXTRACT: FailingStageRunner(make_stage_error())},
    )

    result = worker.run_next()

    assert result is not None
    assert result.status is DocumentJobStatus.FAILED
    assert documents.status_updates == []
    assert lifecycle_events.appended == []


def test_worker_stops_failure_transition_when_invariant_disallows_failed_state() -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.READY,
    )
    jobs = InMemoryJobRepository([make_job(doc_id=document.doc_id)])
    documents = InMemoryDocumentRepository([document])
    lifecycle_events = InMemoryLifecycleEventRepository()
    worker = DocumentLifecycleWorker(
        jobs=jobs,
        documents=documents,
        lifecycle_events=lifecycle_events,
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        stage_runners={DocumentJobStage.EXTRACT: FailingStageRunner(make_stage_error())},
    )

    result = worker.run_next()

    assert result is not None
    assert result.status is DocumentJobStatus.FAILED
    assert documents.status_updates == []
    assert lifecycle_events.appended == []
