"""Normalization stage for extracted document artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from sqlalchemy.engine import Engine

from doc_forge.app.logging import get_logger
from doc_forge.artifacts import FilesystemArtifactStore, NormalizedArtifact
from doc_forge.identifiers import DocId
from doc_forge.lifecycle import (
    LifecycleEvent,
    LifecycleInvariantError,
    LifecycleStage,
    ProcessingStatus,
)
from doc_forge.normalizers import NormalizerRegistry
from doc_forge.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentRepository,
    LifecycleEventRepository,
    PersistedDocument,
)
from doc_forge.stages.base import StageExecutionError, StageLogger, StageRunner

logger = get_logger(__name__)


class DocumentNormalizationError(RuntimeError):
    """Raised when normalization cannot durably complete."""


class NormalizeDocumentStage:
    """Persist a normalized artifact and advance the document to NORMALIZED."""

    def __init__(
        self,
        *,
        engine: Engine,
        documents: DocumentRepository,
        lifecycle_events: LifecycleEventRepository,
        artifact_store: FilesystemArtifactStore,
        normalizers: NormalizerRegistry,
        logger: StageLogger | None = None,
    ) -> None:
        self._engine = engine
        self._documents = documents
        self._lifecycle_events = lifecycle_events
        self._artifact_store = artifact_store
        self._normalizers = normalizers
        self._logger = logger or StageLogger(get_logger(self.__class__.__name__))

    def run(self, doc_id: DocId, *, job_id: str | None = None) -> NormalizedArtifact:
        started_at = perf_counter()
        self._logger.stage_started(
            stage_name="normalize",
            doc_id=doc_id,
            job_id=job_id,
        )
        document = self._require_document(doc_id)
        if document.ingest_status is not ProcessingStatus.EXTRACTING:
            raise LifecycleInvariantError(
                f"document {doc_id!r} must be EXTRACTING before normalization",
            )

        extracted = self._artifact_store.read_extracted(
            workspace_id=document.workspace_id,
            doc_id=document.doc_id,
        )
        artifact = self._normalizers.normalize(
            source_type=document.source_type,
            extracted=extracted,
        )
        event = LifecycleEvent(
            event_id=f"event_{uuid4().hex}",
            doc_id=document.doc_id,
            stage=LifecycleStage.NORMALIZE,
            from_status=ProcessingStatus.EXTRACTING,
            to_status=ProcessingStatus.NORMALIZED,
            occurred_at=datetime.now(UTC),
            detail={"normalizer_version": artifact.normalizer_version},
        )

        try:
            self._artifact_store.write_normalized(
                workspace_id=document.workspace_id,
                artifact=artifact,
            )
            self._documents.update_status(
                doc_id=document.doc_id,
                status=ProcessingStatus.NORMALIZED,
                updated_at=event.occurred_at,
            )
            self._lifecycle_events.append(event)
        except Exception as exc:
            self._artifact_store.delete_normalized(
                workspace_id=document.workspace_id,
                doc_id=document.doc_id,
            )
            self._logger.stage_failed(
                stage_name="normalize",
                doc_id=document.doc_id,
                job_id=job_id,
                duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
                error_code="normalize_failed",
            )
            raise DocumentNormalizationError(
                f"failed to normalize document {document.doc_id!r}: {exc}",
            ) from exc

        self._logger.stage_completed(
            stage_name="normalize",
            doc_id=document.doc_id,
            job_id=job_id,
            duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
            normalizer_version=artifact.normalizer_version,
        )
        return artifact

    def _require_document(self, doc_id: DocId) -> PersistedDocument:
        document = self._documents.get(doc_id)
        if document is None:
            raise LookupError(f"document {doc_id!r} was not found")
        return document


class NormalizeDocumentJobStage(StageRunner):
    """Worker-facing adapter for the normalization stage."""

    target_stage = DocumentJobStage.NORMALIZE

    def __init__(self, *, stage: NormalizeDocumentStage) -> None:
        self._stage = stage

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        try:
            self._stage.run(job.doc_id, job_id=job.job_id)
        except DocumentNormalizationError as exc:
            raise StageExecutionError(
                error_code="normalize_failed",
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
        return DocumentJobStage.SECTIONIZE
