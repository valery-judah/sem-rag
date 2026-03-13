"""Chunking stage for normalized and sectionized documents."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from doc_forge.app.logging import get_logger
from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.chunking import ChunkingService
from doc_forge.lifecycle import LifecycleEvent, LifecycleStage, ProcessingStatus
from doc_forge.persistence import (
    ChunkRepository,
    DocumentJob,
    DocumentJobStage,
    DocumentRepository,
    LifecycleEventRepository,
    SectionRepository,
)
from doc_forge.stages.base import StageExecutionError, StageLogger, StageRunner

logger = get_logger(__name__)


class ChunkDocumentStage(StageRunner):
    """Derive and persist chunks for a normalized document."""

    target_stage = DocumentJobStage.CHUNK

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        sections: SectionRepository,
        chunks: ChunkRepository,
        lifecycle_events: LifecycleEventRepository,
        artifact_store: FilesystemArtifactStore,
        service: ChunkingService,
        logger: StageLogger | None = None,
    ) -> None:
        self._documents = documents
        self._sections = sections
        self._chunks = chunks
        self._lifecycle_events = lifecycle_events
        self._artifact_store = artifact_store
        self._service = service
        self._logger = logger or StageLogger(get_logger(self.__class__.__name__))

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        started_at = perf_counter()
        self._logger.stage_started(
            stage_name="chunk",
            doc_id=job.doc_id,
            job_id=job.job_id,
        )
        document = self._documents.get(job.doc_id)
        if document is None:
            self._logger.stage_failed(
                stage_name="chunk",
                doc_id=job.doc_id,
                job_id=job.job_id,
                duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
                error_code="missing_document",
            )
            raise StageExecutionError(
                error_code="missing_document",
                error_detail=f"document {job.doc_id!r} was not found",
            )
        if document.ingest_status is not ProcessingStatus.NORMALIZED:
            self._logger.stage_failed(
                stage_name="chunk",
                doc_id=job.doc_id,
                job_id=job.job_id,
                duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
                error_code="invalid_document_status",
            )
            raise StageExecutionError(
                error_code="invalid_document_status",
                error_detail=(
                    f"chunk stage requires normalized document, got {document.ingest_status.value}"
                ),
            )
        sections = self._sections.list_for_document(document.doc_id)
        if not sections:
            self._logger.stage_failed(
                stage_name="chunk",
                doc_id=document.doc_id,
                job_id=job.job_id,
                duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
                error_code="missing_sections",
            )
            raise StageExecutionError(
                error_code="missing_sections",
                error_detail=f"document {document.doc_id!r} has no persisted sections",
            )
        artifact = self._artifact_store.read_normalized(
            workspace_id=document.workspace_id,
            doc_id=document.doc_id,
        )
        chunks = self._service.derive(document=document, artifact=artifact, sections=sections)
        if not chunks:
            self._logger.stage_failed(
                stage_name="chunk",
                doc_id=document.doc_id,
                job_id=job.job_id,
                duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
                error_code="empty_chunk_set",
                section_count=len(sections),
            )
            raise StageExecutionError(
                error_code="empty_chunk_set",
                error_detail=f"document {document.doc_id!r} produced no chunks",
            )
        completed_at = datetime.now(UTC)
        self._chunks.replace_for_document(document.doc_id, chunks)
        self._documents.update_status(
            doc_id=document.doc_id,
            status=ProcessingStatus.CHUNKED,
            updated_at=completed_at,
        )
        self._lifecycle_events.append(
            LifecycleEvent(
                event_id=f"event_{uuid4().hex}",
                doc_id=document.doc_id,
                stage=LifecycleStage.CHUNK,
                from_status=ProcessingStatus.NORMALIZED,
                to_status=ProcessingStatus.CHUNKED,
                occurred_at=completed_at,
                detail={"chunk_count": str(len(chunks))},
            )
        )
        self._logger.stage_completed(
            stage_name="chunk",
            doc_id=document.doc_id,
            job_id=job.job_id,
            duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
            section_count=len(sections),
            chunk_count=len(chunks),
        )
        return DocumentJobStage.INDEX
