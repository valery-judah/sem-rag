from __future__ import annotations

from doc_forge.lifecycle.orchestrator import DocumentLifecycleOrchestrator
from doc_forge.persistence import DocumentJobStage, DocumentJobStatus
from tests.lifecycle.support import InMemoryJobRepository, make_job


def test_enqueue_stage_creates_job_when_document_has_no_active_work() -> None:
    jobs = InMemoryJobRepository()
    orchestrator = DocumentLifecycleOrchestrator(jobs=jobs)

    created = orchestrator.enqueue_stage(
        doc_id="doc-1",
        target_stage=DocumentJobStage.EXTRACT,
    )

    assert created is not None
    assert created.doc_id == "doc-1"
    assert created.target_stage is DocumentJobStage.EXTRACT
    assert jobs.get(created.job_id) == created


def test_enqueue_stage_returns_none_when_document_has_active_job() -> None:
    jobs = InMemoryJobRepository([make_job(doc_id="doc-1", status=DocumentJobStatus.QUEUED)])
    orchestrator = DocumentLifecycleOrchestrator(jobs=jobs)

    created = orchestrator.enqueue_stage(
        doc_id="doc-1",
        target_stage=DocumentJobStage.NORMALIZE,
    )

    assert created is None
    assert len(jobs.list_for_document("doc-1")) == 1


def test_next_stage_returns_expected_linear_sequence() -> None:
    orchestrator = DocumentLifecycleOrchestrator(jobs=InMemoryJobRepository())

    assert orchestrator.next_stage(DocumentJobStage.EXTRACT) is DocumentJobStage.NORMALIZE
    assert orchestrator.next_stage(DocumentJobStage.NORMALIZE) is DocumentJobStage.SECTIONIZE
    assert orchestrator.next_stage(DocumentJobStage.SECTIONIZE) is DocumentJobStage.CHUNK
    assert orchestrator.next_stage(DocumentJobStage.CHUNK) is DocumentJobStage.INDEX
    assert orchestrator.next_stage(DocumentJobStage.INDEX) is DocumentJobStage.READY_CHECK


def test_next_stage_returns_none_after_ready_check() -> None:
    orchestrator = DocumentLifecycleOrchestrator(jobs=InMemoryJobRepository())

    assert orchestrator.next_stage(DocumentJobStage.READY_CHECK) is None
