"""Sectionization stage for normalized documents."""

from __future__ import annotations

from parity.artifacts import FilesystemArtifactStore
from parity.lifecycle import ProcessingStatus
from parity.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentRepository,
    SectionRepository,
)
from parity.stages.base import StageExecutionError, StageRunner
from parity.structure import SectionDerivationService


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
    ) -> None:
        self._documents = documents
        self._sections = sections
        self._artifact_store = artifact_store
        self._service = service

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        document = self._documents.get(job.doc_id)
        if document is None:
            raise StageExecutionError(
                error_code="missing_document",
                error_detail=f"document {job.doc_id!r} was not found",
            )
        if document.ingest_status is not ProcessingStatus.NORMALIZED:
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
            raise StageExecutionError(
                error_code="missing_normalized_artifact",
                error_detail=str(exc),
            ) from exc
        sections = self._service.derive(document=document, artifact=artifact)
        self._sections.replace_for_document(document.doc_id, sections)
        return DocumentJobStage.CHUNK
