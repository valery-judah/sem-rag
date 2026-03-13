"""Extraction stage for registered documents."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

import structlog
from sqlalchemy.engine import Engine

from doc_forge.app.logging import get_logger
from doc_forge.artifacts import ExtractedArtifact, FilesystemArtifactStore, RawArtifactRef
from doc_forge.extractors import ExtractorRegistry
from doc_forge.identifiers import DocId
from doc_forge.lifecycle import (
    LifecycleEvent,
    LifecycleInvariantError,
    LifecycleStage,
    ProcessingStatus,
)
from doc_forge.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentRepository,
    LifecycleEventRepository,
    PersistedDocument,
)
from doc_forge.stages.base import StageExecutionError, StageRunner

logger = get_logger(__name__)


class DocumentExtractionError(RuntimeError):
    """Raised when extraction cannot durably complete."""


class ExtractDocumentStage:
    """Persist an extracted artifact and advance the document to EXTRACTING."""

    def __init__(
        self,
        *,
        engine: Engine,
        documents: DocumentRepository,
        lifecycle_events: LifecycleEventRepository,
        artifact_store: FilesystemArtifactStore,
        extractors: ExtractorRegistry,
        logger: structlog.stdlib.BoundLogger | None = None,
    ) -> None:
        self._engine = engine
        self._documents = documents
        self._lifecycle_events = lifecycle_events
        self._artifact_store = artifact_store
        self._extractors = extractors
        self._logger = logger or get_logger(self.__class__.__name__)

    def run(self, doc_id: DocId, *, job_id: str | None = None) -> ExtractedArtifact:
        started_at = perf_counter()
        self._logger.info(
            "lifecycle.stage.started",
            stage_name="extract",
            doc_id=doc_id,
            job_id=job_id,
        )
        document = self._require_document(doc_id)
        if document.ingest_status is not ProcessingStatus.REGISTERED:
            raise LifecycleInvariantError(
                f"document {doc_id!r} must be REGISTERED before extraction",
            )

        raw_ref = RawArtifactRef(
            workspace_id=document.workspace_id,
            doc_id=document.doc_id,
            source_type=document.source_type,
            relative_path=document.raw_storage_path or "",
        )
        try:
            raw_content = self._artifact_store.read_raw(raw_ref)
            artifact = self._extractors.extract(
                doc_id=document.doc_id,
                source_type=document.source_type,
                raw_content=raw_content,
            )
            event = LifecycleEvent(
                event_id=f"event_{uuid4().hex}",
                doc_id=document.doc_id,
                stage=LifecycleStage.EXTRACT,
                from_status=ProcessingStatus.REGISTERED,
                to_status=ProcessingStatus.EXTRACTING,
                occurred_at=datetime.now(UTC),
                detail={"extractor_version": artifact.extractor_version},
            )
            self._artifact_store.write_extracted(
                workspace_id=document.workspace_id,
                artifact=artifact,
            )
            self._documents.update_status(
                doc_id=document.doc_id,
                status=ProcessingStatus.EXTRACTING,
                updated_at=event.occurred_at,
            )
            self._lifecycle_events.append(event)
        except Exception as exc:
            self._artifact_store.delete_extracted(
                workspace_id=document.workspace_id,
                doc_id=document.doc_id,
            )
            self._logger.warning(
                "lifecycle.stage.failed",
                stage_name="extract",
                doc_id=document.doc_id,
                job_id=job_id,
                duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
                error_code="extract_failed",
            )
            raise DocumentExtractionError(
                f"failed to extract document {document.doc_id!r}: {exc}",
            ) from exc

        self._logger.info(
            "lifecycle.stage.completed",
            stage_name="extract",
            doc_id=document.doc_id,
            job_id=job_id,
            duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
            extractor_version=artifact.extractor_version,
        )
        return artifact

    def _require_document(self, doc_id: DocId) -> PersistedDocument:
        document = self._documents.get(doc_id)
        if document is None:
            raise LookupError(f"document {doc_id!r} was not found")
        return document


class ExtractDocumentJobStage(StageRunner):
    """Worker-facing adapter for the extraction stage."""

    target_stage = DocumentJobStage.EXTRACT

    def __init__(self, *, stage: ExtractDocumentStage) -> None:
        self._stage = stage

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        try:
            self._stage.run(job.doc_id, job_id=job.job_id)
        except DocumentExtractionError as exc:
            raise StageExecutionError(
                error_code="extract_failed",
                error_detail=str(exc),
            ) from exc
        except LookupError as exc:
            raise StageExecutionError(
                error_code="missing_document",
                error_detail=str(exc),
            ) from exc
        except LifecycleInvariantError as exc:
            raise StageExecutionError(
                error_code="invalid_document_status",
                error_detail=str(exc),
            ) from exc
        return DocumentJobStage.NORMALIZE
