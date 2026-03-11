"""Registration stage for accepted raw document uploads."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy.engine import Engine

from parity._contracts import Document, ProcessingStatus, SourceType
from parity.artifacts import FilesystemArtifactStore, RawArtifactRef
from parity.lifecycle import (
    LifecycleEvent,
    LifecycleInvariantError,
    LifecycleStage,
    require_processing_status_transition,
)
from parity.persistence import (
    DocumentRepository,
    LifecycleEventRepository,
    PersistedDocument,
)


class DocumentRegistrationError(RuntimeError):
    """Raised when registration cannot durably complete."""


class RegisterDocumentRequest(BaseModel):
    """Transport-independent input for the registration stage."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    workspace_id: str
    source_type: SourceType
    title: str
    filename: str
    uploaded_at: datetime
    checksum: str
    content: bytes


class RegisterDocumentStage:
    """Turn an accepted upload into a durable registered document."""

    def __init__(
        self,
        *,
        engine: Engine,
        documents: DocumentRepository,
        lifecycle_events: LifecycleEventRepository,
        artifact_store: FilesystemArtifactStore,
    ) -> None:
        self._engine = engine
        self._documents = documents
        self._lifecycle_events = lifecycle_events
        self._artifact_store = artifact_store

    def run(self, request: RegisterDocumentRequest) -> PersistedDocument:
        """Persist the raw artifact and register the durable document identity."""

        require_processing_status_transition(
            ProcessingStatus.UPLOADED,
            ProcessingStatus.REGISTERED,
        )

        existing = self._documents.get(request.doc_id)
        if existing is not None:
            return self._require_matching_existing_document(existing, request)

        raw_ref = self._artifact_store.write_raw(
            workspace_id=request.workspace_id,
            doc_id=request.doc_id,
            source_type=request.source_type,
            content=request.content,
        )
        document = self._build_persisted_document(request=request, raw_ref=raw_ref)
        event = self._build_lifecycle_event(request.doc_id, request.uploaded_at)

        try:
            with self._engine.begin() as connection:
                self._documents.create(document, connection=connection)
                self._lifecycle_events.append(event, connection=connection)
        except Exception as exc:
            existing = self._documents.get(request.doc_id)
            if existing is not None:
                return self._require_matching_existing_document(existing, request)
            self._cleanup_raw_artifact(raw_ref)
            raise DocumentRegistrationError(
                f"failed to register document {request.doc_id!r}",
            ) from exc

        return document

    def _build_persisted_document(
        self,
        *,
        request: RegisterDocumentRequest,
        raw_ref: RawArtifactRef,
    ) -> PersistedDocument:
        raw_path = self._artifact_store.raw_path(
            workspace_id=request.workspace_id,
            doc_id=request.doc_id,
            source_type=request.source_type,
        )
        document = Document(
            doc_id=request.doc_id,
            workspace_id=request.workspace_id,
            source_type=request.source_type,
            title=request.title,
            filename=request.filename,
            uploaded_at=request.uploaded_at,
            ingest_status=ProcessingStatus.REGISTERED,
            storage_ref=raw_path.as_uri(),
        )
        return PersistedDocument.from_contract(
            document,
            checksum=request.checksum,
            raw_storage_path=raw_ref.relative_path,
            created_at=request.uploaded_at,
            updated_at=request.uploaded_at,
        )

    def _build_lifecycle_event(self, doc_id: str, occurred_at: datetime) -> LifecycleEvent:
        return LifecycleEvent(
            event_id=f"event_{uuid4().hex}",
            doc_id=doc_id,
            stage=LifecycleStage.REGISTER,
            from_status=ProcessingStatus.UPLOADED,
            to_status=ProcessingStatus.REGISTERED,
            occurred_at=occurred_at,
        )

    def _require_matching_existing_document(
        self,
        existing: PersistedDocument,
        request: RegisterDocumentRequest,
    ) -> PersistedDocument:
        expected_raw_path = self._artifact_store.raw_path(
            workspace_id=request.workspace_id,
            doc_id=request.doc_id,
            source_type=request.source_type,
        )
        mismatches: list[str] = []
        if existing.workspace_id != request.workspace_id:
            mismatches.append("workspace_id")
        if existing.source_type is not request.source_type:
            mismatches.append("source_type")
        if existing.title != request.title:
            mismatches.append("title")
        if existing.filename != request.filename:
            mismatches.append("filename")
        if existing.uploaded_at != request.uploaded_at:
            mismatches.append("uploaded_at")
        if existing.storage_ref != expected_raw_path.as_uri():
            mismatches.append("storage_ref")
        if existing.checksum != request.checksum:
            mismatches.append("checksum")
        if existing.raw_storage_path != self._expected_relative_raw_path(request):
            mismatches.append("raw_storage_path")

        if mismatches:
            mismatch_summary = ", ".join(sorted(mismatches))
            raise LifecycleInvariantError(
                f"existing document does not match the intake context: {mismatch_summary}",
            )

        return existing

    def _expected_relative_raw_path(self, request: RegisterDocumentRequest) -> str:
        return self._artifact_store.raw_relative_path(
            workspace_id=request.workspace_id,
            doc_id=request.doc_id,
            source_type=request.source_type,
        )

    def _cleanup_raw_artifact(self, raw_ref: RawArtifactRef) -> None:
        try:
            self._artifact_store.delete_raw(raw_ref)
        except Exception:
            return
