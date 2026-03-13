"""Sectionization stage for normalized documents."""

from __future__ import annotations

from time import perf_counter

from doc_forge.app.logging import get_logger
from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentRepository,
    SectionRepository,
)
from doc_forge.stages.base import StageExecutionError, StageLogger, StageRunner
from doc_forge.structure import SectionDerivationService

logger = get_logger(__name__)


class SectionizeDocumentStage(StageRunner):
    """Recover and persist sections for a normalized document."""

    target_stage = DocumentJobStage.SECTIONIZE

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        sections: SectionRepository,
        artifact_store: FilesystemArtifactStore,
        service: SectionDerivationService,
        logger: StageLogger | None = None,
    ) -> None:
        self._documents = documents
        self._sections = sections
        self._artifact_store = artifact_store
        self._service = service
        self._logger = logger or StageLogger(get_logger(self.__class__.__name__))

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        started_at = perf_counter()
        self._logger.stage_started(
            stage_name="sectionize",
            doc_id=job.doc_id,
            job_id=job.job_id,
        )
        document = self._documents.get(job.doc_id)
        if document is None:
            self._logger.stage_failed(
                stage_name="sectionize",
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
                stage_name="sectionize",
                doc_id=job.doc_id,
                job_id=job.job_id,
                duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
                error_code="invalid_document_status",
            )
            raise StageExecutionError(
                error_code="invalid_document_status",
                error_detail=(
                    f"sectionize stage requires normalized document, got "
                    f"{document.ingest_status.value}"
                ),
            )
        try:
            artifact = self._artifact_store.read_normalized(
                workspace_id=document.workspace_id,
                doc_id=document.doc_id,
            )
        except FileNotFoundError as exc:
            self._logger.stage_failed(
                stage_name="sectionize",
                doc_id=document.doc_id,
                job_id=job.job_id,
                duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
                error_code="missing_normalized_artifact",
            )
            raise StageExecutionError(
                error_code="missing_normalized_artifact",
                error_detail=str(exc),
            ) from exc
        sections = self._service.derive(document=document, artifact=artifact)
        self._sections.replace_for_document(document.doc_id, sections)
        self._logger.stage_completed(
            stage_name="sectionize",
            doc_id=document.doc_id,
            job_id=job.job_id,
            duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
            section_count=len(sections),
        )
        return DocumentJobStage.CHUNK
