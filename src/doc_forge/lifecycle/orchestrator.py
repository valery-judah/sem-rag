"""Document-scoped job orchestration helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from doc_forge.persistence import DocumentJob, DocumentJobRepository, DocumentJobStage

_NEXT_STAGE: dict[DocumentJobStage, DocumentJobStage | None] = {
    DocumentJobStage.EXTRACT: DocumentJobStage.NORMALIZE,
    DocumentJobStage.NORMALIZE: DocumentJobStage.SECTIONIZE,
    DocumentJobStage.SECTIONIZE: DocumentJobStage.CHUNK,
    DocumentJobStage.CHUNK: DocumentJobStage.INDEX,
    DocumentJobStage.INDEX: DocumentJobStage.READY_CHECK,
    DocumentJobStage.READY_CHECK: None,
}


class DocumentLifecycleOrchestrator:
    """Own queued stage creation and next-stage sequencing."""

    def __init__(self, *, jobs: DocumentJobRepository) -> None:
        self._jobs = jobs

    def enqueue_stage(self, *, doc_id: str, target_stage: DocumentJobStage) -> DocumentJob | None:
        """Queue the next job when no active work already exists for the document."""

        if self._jobs.has_active_job(doc_id):
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
        return job

    def next_stage(self, target_stage: DocumentJobStage) -> DocumentJobStage | None:
        """Return the next queued stage for a successful job."""

        return _NEXT_STAGE[target_stage]
