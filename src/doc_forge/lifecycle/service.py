"""Transport-thin lifecycle coordination for intake and registration."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import NoReturn
from uuid import uuid4

import structlog
from pydantic import BaseModel, ConfigDict, Field

from doc_forge.app.log_events import LogEvent
from doc_forge.app.logging import get_logger
from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.corpus import Chunk, Section, SourceType
from doc_forge.identifiers import DocId, WorkspaceId
from doc_forge.indexing import ChunkEmbedding, IndexEntry, VectorSearchHit, VectorStore
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.persistence import (
    ChunkEmbeddingRepository,
    ChunkRepository,
    DocumentJobRepository,
    DocumentJobStage,
    DocumentRepository,
    IndexEntryRepository,
    LifecycleEventRepository,
    PersistedDocument,
    SectionRepository,
)
from doc_forge.stages import RegisterDocumentRequest, RegisterDocumentStage

from .orchestrator import DocumentLifecycleOrchestrator

logger = get_logger(__name__)


class UnsupportedDocumentError(ValueError):
    """Raised when an upload falls outside the MVP-supported source types."""

    def __init__(self, message: str, *, error_code: str) -> None:
        self.error_code = error_code
        super().__init__(message)


class DocumentNotFoundError(LookupError):
    """Raised when a document-scoped lifecycle operation cannot find the document."""


class RetryNotAllowedError(ValueError):
    """Raised when retry cannot be safely queued for the current document state."""

    def __init__(self, message: str, *, error_code: str) -> None:
        self.error_code = error_code
        super().__init__(message)


class UploadDocumentResult(BaseModel):
    """Internal response payload for successful document uploads."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId = Field(
        ...,
        description="Unique identifier for the registered document.",
        json_schema_extra={"example": "doc_1234abcd"},
    )
    ingest_status: ProcessingStatus = Field(
        ...,
        description="The current processing status of the document.",
        json_schema_extra={"example": "registered"},
    )
    source_type: SourceType = Field(
        ...,
        description="The detected source type of the document.",
        json_schema_extra={"example": "pdf"},
    )
    filename: str = Field(
        ...,
        description="The original filename of the uploaded document.",
        json_schema_extra={"example": "report.pdf"},
    )
    title: str = Field(
        ...,
        description="The resolved title of the document.",
        json_schema_extra={"example": "Q3 Financial Report"},
    )
    uploaded_at: datetime = Field(
        ..., description="The UTC timestamp when the document was uploaded."
    )
    checksum: str = Field(
        ...,
        description="The SHA-256 checksum of the uploaded file content.",
        json_schema_extra={
            "example": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        },
    )


class DocumentStatusResult(BaseModel):
    """Internal status payload for one persisted document."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId = Field(
        ...,
        description="The unique identifier of the document.",
        json_schema_extra={"example": "doc_1234abcd"},
    )
    ingest_status: ProcessingStatus = Field(
        ...,
        description="The current ingestion status of the document.",
        json_schema_extra={"example": "indexed"},
    )
    source_type: SourceType = Field(
        ..., description="The source type of the document.", json_schema_extra={"example": "pdf"}
    )
    title: str = Field(
        ...,
        description="The title of the document.",
        json_schema_extra={"example": "Q3 Financial Report"},
    )
    filename: str = Field(
        ...,
        description="The original filename of the document.",
        json_schema_extra={"example": "report.pdf"},
    )
    failure_code: str | None = Field(
        default=None,
        description="A machine-readable code if the document processing failed.",
        json_schema_extra={"example": "extraction_failed"},
    )
    failure_detail: str | None = Field(
        default=None,
        description="A human-readable explanation if the document processing failed.",
        json_schema_extra={"example": "Failed to extract text from page 3"},
    )
    active_job_stage: DocumentJobStage | None = Field(
        default=None,
        description="The currently active processing job stage, if any.",
        json_schema_extra={"example": "chunk"},
    )


class RetryDocumentResult(BaseModel):
    """Internal response payload for a queued retry."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId = Field(
        ...,
        description="The unique identifier of the document.",
        json_schema_extra={"example": "doc_1234abcd"},
    )
    ingest_status: ProcessingStatus = Field(
        ...,
        description="The new status of the document after queuing for retry.",
        json_schema_extra={"example": "registered"},
    )
    queued_stage: DocumentJobStage = Field(
        ...,
        description="The specific processing stage that has been queued for execution.",
        json_schema_extra={"example": "extract"},
    )


class RetrievalQueryResult(BaseModel):
    """Internal retrieval smoke-query payload."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId = Field(
        ...,
        description="The unique identifier of the document searched against.",
        json_schema_extra={"example": "doc_1234abcd"},
    )
    hits: list[VectorSearchHit] = Field(
        default_factory=list,
        description="The list of vector search hits (chunks) returned from the vector store.",
    )


class DocumentArtifactRefs(BaseModel):
    """Internal artifact-inspection response payload."""

    model_config = ConfigDict(extra="forbid")

    doc_id: DocId = Field(
        ...,
        description="The unique identifier of the document.",
        json_schema_extra={"example": "doc_1234abcd"},
    )
    raw_path: str = Field(
        ...,
        description="The filesystem path to the original raw uploaded file.",
        json_schema_extra={"example": "/data/artifacts/doc_1234abcd/raw.pdf"},
    )
    extracted_path: str | None = Field(
        default=None,
        description="The filesystem path to the extracted text artifact.",
        json_schema_extra={"example": "/data/artifacts/doc_1234abcd/extracted.json"},
    )
    normalized_path: str | None = Field(
        default=None,
        description="The filesystem path to the normalized text artifact.",
        json_schema_extra={"example": "/data/artifacts/doc_1234abcd/normalized.json"},
    )


class LifecycleServiceLogger:
    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._logger = logger

    def upload_validated(
        self,
        workspace_id: str,
        filename_extension: str | None,
        source_type: str,
        size_bytes: int,
        checksum_sha256: str,
    ) -> None:
        self._logger.info(
            LogEvent.DOCUMENT_UPLOAD_VALIDATED,
            workspace_id=workspace_id,
            filename_extension=filename_extension,
            source_type=source_type,
            size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
        )

    def upload_registered(
        self, workspace_id: str, doc_id: str, ingest_status: str, source_type: str, duration_ms: int
    ) -> None:
        self._logger.info(
            LogEvent.DOCUMENT_UPLOAD_REGISTERED,
            workspace_id=workspace_id,
            doc_id=doc_id,
            ingest_status=ingest_status,
            source_type=source_type,
            duration_ms=duration_ms,
        )

    def smoke_executed(
        self,
        doc_id: str,
        k: int,
        query_chars: int,
        query_sha256: str,
        hit_count: int,
        top_hit_doc_id: str | None,
        top_hit_chunk_id: str | None,
    ) -> None:
        self._logger.info(
            LogEvent.RETRIEVAL_SMOKE_EXECUTED,
            doc_id=doc_id,
            k=k,
            query_chars=query_chars,
            query_sha256=query_sha256,
            hit_count=hit_count,
            top_hit_doc_id=top_hit_doc_id,
            top_hit_chunk_id=top_hit_chunk_id,
        )

    def delete_performed(
        self,
        workspace_id: str,
        doc_id: str,
        vector_store_deleted: bool,
        raw_deleted: bool,
        extracted_deleted: bool,
        normalized_deleted: bool,
        document_row_deleted: bool,
    ) -> None:
        self._logger.info(
            LogEvent.DOCUMENT_DELETE_PERFORMED,
            workspace_id=workspace_id,
            doc_id=doc_id,
            vector_store_deleted=vector_store_deleted,
            raw_deleted=raw_deleted,
            extracted_deleted=extracted_deleted,
            normalized_deleted=normalized_deleted,
            document_row_deleted=document_row_deleted,
        )

    def retry_eligibility_checked(self, doc_id: str, workspace_id: str, ingest_status: str) -> None:
        self._logger.info(
            LogEvent.DOCUMENT_RETRY_ELIGIBILITY_CHECKED,
            doc_id=doc_id,
            workspace_id=workspace_id,
            ingest_status=ingest_status,
        )

    def retry_queued_internal(
        self,
        doc_id: str,
        workspace_id: str,
        failed_stage: str,
        queued_stage: str,
        job_id: str,
        ingest_status: str,
    ) -> None:
        self._logger.info(
            LogEvent.DOCUMENT_RETRY_QUEUED_INTERNAL,
            doc_id=doc_id,
            workspace_id=workspace_id,
            failed_stage=failed_stage,
            queued_stage=queued_stage,
            job_id=job_id,
            ingest_status=ingest_status,
        )

    def retry_eligibility_rejected(
        self,
        doc_id: str,
        workspace_id: str,
        ingest_status: str,
        failed_stage: str | None,
        error_code: str,
    ) -> None:
        self._logger.warning(
            LogEvent.DOCUMENT_RETRY_ELIGIBILITY_REJECTED,
            doc_id=doc_id,
            workspace_id=workspace_id,
            ingest_status=ingest_status,
            failed_stage=failed_stage,
            error_code=error_code,
        )


class DocumentLifecycleService:
    """Coordinate upload intake and durable registration."""

    def __init__(
        self,
        *,
        register_stage: RegisterDocumentStage,
        orchestrator: DocumentLifecycleOrchestrator | None = None,
        documents: DocumentRepository | None = None,
        jobs: DocumentJobRepository | None = None,
        lifecycle_events: LifecycleEventRepository | None = None,
        artifact_store: FilesystemArtifactStore | None = None,
        sections: SectionRepository | None = None,
        chunks: ChunkRepository | None = None,
        index_entries: IndexEntryRepository | None = None,
        chunk_embeddings: ChunkEmbeddingRepository | None = None,
        vector_store: VectorStore | None = None,
        logger: LifecycleServiceLogger | None = None,
    ) -> None:
        self._register_stage = register_stage
        self._orchestrator = orchestrator
        self._documents = documents
        self._jobs = jobs
        self._lifecycle_events = lifecycle_events
        self._artifact_store = artifact_store
        self._sections = sections
        self._chunks = chunks
        self._index_entries = index_entries
        self._chunk_embeddings = chunk_embeddings
        self._vector_store = vector_store
        self._logger = logger or LifecycleServiceLogger(get_logger(self.__class__.__name__))

    def upload_document(
        self,
        *,
        workspace_id: WorkspaceId,
        title: str | None,
        filename: str | None,
        content: bytes,
    ) -> UploadDocumentResult:
        """Validate an upload and durably register it."""

        started_at = perf_counter()
        normalized_filename = self._require_filename(filename)
        source_type = self._detect_source_type(
            filename=normalized_filename,
            content=content,
        )
        uploaded_at = datetime.now(UTC)
        resolved_title = self._resolve_title(title=title, filename=normalized_filename)
        checksum = self._checksum(content)
        self._logger.upload_validated(
            workspace_id=workspace_id,
            filename_extension=_filename_extension(normalized_filename),
            source_type=source_type.value,
            size_bytes=len(content),
            checksum_sha256=checksum,
        )
        request = RegisterDocumentRequest(
            doc_id=f"doc_{uuid4().hex}",
            workspace_id=workspace_id,
            source_type=source_type,
            title=resolved_title,
            filename=normalized_filename,
            uploaded_at=uploaded_at,
            checksum=checksum,
            content=content,
        )
        document = self._register_stage.run(request)
        if self._orchestrator is not None:
            self._orchestrator.enqueue_stage(
                doc_id=document.doc_id,
                target_stage=DocumentJobStage.EXTRACT,
            )
        self._logger.upload_registered(
            workspace_id=workspace_id,
            doc_id=document.doc_id,
            ingest_status=document.ingest_status.value,
            source_type=document.source_type.value,
            duration_ms=max(int((perf_counter() - started_at) * 1000), 0),
        )
        return UploadDocumentResult(
            doc_id=document.doc_id,
            ingest_status=document.ingest_status,
            source_type=document.source_type,
            filename=document.filename,
            title=document.title,
            uploaded_at=document.uploaded_at,
            checksum=document.checksum or checksum,
        )

    def get_document_status(self, *, doc_id: DocId) -> DocumentStatusResult:
        """Load the current persisted status plus any active queued work."""

        document = self._require_document(doc_id)
        active_job_stage = None
        if self._jobs is not None:
            for job in self._jobs.list_for_document(doc_id):
                if job.status.value in {"queued", "running"}:
                    active_job_stage = job.target_stage
                    break
        return DocumentStatusResult(
            doc_id=document.doc_id,
            ingest_status=document.ingest_status,
            source_type=document.source_type,
            title=document.title,
            filename=document.filename,
            failure_code=document.failure_code,
            failure_detail=document.failure_detail,
            active_job_stage=active_job_stage,
        )

    def query_document(self, *, doc_id: DocId, text: str, k: int = 3) -> RetrievalQueryResult:
        """Run a document-scoped smoke query against the internal vector store."""

        self._require_document(doc_id)
        if self._vector_store is None:
            raise RuntimeError("vector store is not configured")
        hits = self._vector_store.smoke_query(doc_id=doc_id, text=text, k=k)
        top_hit = hits[0] if hits else None
        self._logger.smoke_executed(
            doc_id=doc_id,
            k=k,
            query_chars=len(text),
            query_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            hit_count=len(hits),
            top_hit_doc_id=None if top_hit is None else top_hit.doc_id,
            top_hit_chunk_id=None if top_hit is None else top_hit.chunk_id,
        )
        return RetrievalQueryResult(
            doc_id=doc_id,
            hits=hits,
        )

    def delete_document(self, *, doc_id: DocId) -> None:
        """Completely remove a document, its artifacts, vectors, and lifecycle history."""
        document = self._require_document(doc_id)
        vector_store_deleted = False
        raw_deleted = False
        extracted_deleted = False
        normalized_deleted = False

        if self._vector_store is not None:
            self._vector_store.delete_document(doc_id=doc_id)
            vector_store_deleted = True

        if self._artifact_store is not None:
            self._artifact_store.delete_raw_by_id(
                workspace_id=document.workspace_id,
                doc_id=doc_id,
                source_type=document.source_type,
            )
            raw_deleted = True
            self._artifact_store.delete_extracted(
                workspace_id=document.workspace_id,
                doc_id=doc_id,
            )
            extracted_deleted = True
            self._artifact_store.delete_normalized(
                workspace_id=document.workspace_id,
                doc_id=doc_id,
            )
            normalized_deleted = True

        if self._documents is not None:
            self._documents.delete(doc_id=doc_id)
        self._logger.delete_performed(
            workspace_id=document.workspace_id,
            doc_id=doc_id,
            vector_store_deleted=vector_store_deleted,
            raw_deleted=raw_deleted,
            extracted_deleted=extracted_deleted,
            normalized_deleted=normalized_deleted,
            document_row_deleted=self._documents is not None,
        )

    def retry_document(self, *, doc_id: DocId) -> RetryDocumentResult:
        """Queue a retry for the latest failed lifecycle stage."""

        document = self._require_document(doc_id)
        self._logger.retry_eligibility_checked(
            doc_id=doc_id,
            workspace_id=document.workspace_id,
            ingest_status=document.ingest_status.value,
        )
        if document.ingest_status is ProcessingStatus.READY:
            self._raise_retry_not_allowed(
                message="ready documents cannot be retried",
                error_code="ready_document",
                document=document,
            )
        if self._jobs is None or self._orchestrator is None or self._lifecycle_events is None:
            raise RuntimeError("retry dependencies are not configured")
        if self._jobs.has_active_job(doc_id):
            self._raise_retry_not_allowed(
                message="document already has queued or running work",
                error_code="active_job_exists",
                document=document,
            )
        if document.ingest_status is not ProcessingStatus.FAILED:
            self._raise_retry_not_allowed(
                message="retry is only supported for failed documents",
                error_code="document_not_failed",
                document=document,
            )

        failed_event = next(
            (
                event
                for event in reversed(self._lifecycle_events.list_for_document(doc_id))
                if event.to_status is ProcessingStatus.FAILED
            ),
            None,
        )
        if failed_event is None:
            self._raise_retry_not_allowed(
                message="document has no failed lifecycle event to retry",
                error_code="missing_failed_event",
                document=document,
            )

        job_stage_name = failed_event.detail.get("job_stage")
        if not job_stage_name:
            self._raise_retry_not_allowed(
                message="failed lifecycle event does not identify a retry stage",
                error_code="missing_retry_stage",
                document=document,
            )
        target_stage = DocumentJobStage(job_stage_name)
        reset_status = self._reset_status_for_stage(target_stage)

        self._cleanup_downstream(document.doc_id, stage=target_stage)
        documents = self._documents
        if documents is None:
            raise RuntimeError("document repository is not configured")
        documents.update_status(doc_id=document.doc_id, status=reset_status)
        queued = self._orchestrator.enqueue_stage(doc_id=document.doc_id, target_stage=target_stage)
        if queued is None:
            self._raise_retry_not_allowed(
                message="document already has queued or running work",
                error_code="active_job_exists",
                document=document,
                failed_stage=target_stage,
            )
        self._logger.retry_queued_internal(
            doc_id=document.doc_id,
            workspace_id=document.workspace_id,
            failed_stage=target_stage.value,
            queued_stage=queued.target_stage.value,
            job_id=queued.job_id,
            ingest_status=reset_status.value,
        )
        return RetryDocumentResult(
            doc_id=document.doc_id,
            ingest_status=reset_status,
            queued_stage=target_stage,
        )

    def get_artifact_refs(self, *, doc_id: DocId) -> DocumentArtifactRefs:
        """Return current managed artifact paths for debugging."""

        document = self._require_document(doc_id)
        if self._artifact_store is None:
            raise RuntimeError("artifact store is not configured")
        raw_path = self._artifact_store.raw_path(
            workspace_id=document.workspace_id,
            doc_id=document.doc_id,
            source_type=document.source_type,
        )
        extracted_path = self._artifact_store.extracted_path(
            workspace_id=document.workspace_id,
            doc_id=document.doc_id,
        )
        normalized_path = self._artifact_store.normalized_path(
            workspace_id=document.workspace_id,
            doc_id=document.doc_id,
        )
        return DocumentArtifactRefs(
            doc_id=document.doc_id,
            raw_path=str(raw_path),
            extracted_path=str(extracted_path) if extracted_path.exists() else None,
            normalized_path=str(normalized_path) if normalized_path.exists() else None,
        )

    def _require_document(self, doc_id: DocId) -> PersistedDocument:
        if self._documents is None:
            raise RuntimeError("document repository is not configured")
        document = self._documents.get(doc_id)
        if document is None:
            raise DocumentNotFoundError(f"document {doc_id!r} was not found")
        return document

    def _reset_status_for_stage(self, stage: DocumentJobStage) -> ProcessingStatus:
        if stage is DocumentJobStage.EXTRACT:
            return ProcessingStatus.REGISTERED
        if stage is DocumentJobStage.NORMALIZE:
            return ProcessingStatus.EXTRACTING
        if stage in {DocumentJobStage.SECTIONIZE, DocumentJobStage.CHUNK}:
            return ProcessingStatus.NORMALIZED
        if stage is DocumentJobStage.INDEX:
            return ProcessingStatus.CHUNKED
        if stage is DocumentJobStage.READY_CHECK:
            return ProcessingStatus.INDEXED
        raise RetryNotAllowedError(
            f"unsupported retry stage {stage.value}",
            error_code="unsupported_retry_stage",
        )

    def _cleanup_downstream(self, doc_id: DocId, *, stage: DocumentJobStage) -> None:
        if self._artifact_store is None or self._documents is None:
            return
        document = self._documents.get(doc_id)
        if document is None:
            return
        if stage is DocumentJobStage.EXTRACT:
            self._delete_extracted(document)
            self._delete_normalized(document)
            self._replace_sections(doc_id, [])
            self._replace_chunks(doc_id, [])
            self._replace_index_entries(doc_id, [])
            self._replace_chunk_embeddings(doc_id, [])
            return
        if stage is DocumentJobStage.NORMALIZE:
            self._delete_normalized(document)
            self._replace_sections(doc_id, [])
            self._replace_chunks(doc_id, [])
            self._replace_index_entries(doc_id, [])
            self._replace_chunk_embeddings(doc_id, [])
            return
        if stage is DocumentJobStage.SECTIONIZE:
            self._replace_sections(doc_id, [])
            self._replace_chunks(doc_id, [])
            self._replace_index_entries(doc_id, [])
            self._replace_chunk_embeddings(doc_id, [])
            return
        if stage is DocumentJobStage.CHUNK:
            self._replace_chunks(doc_id, [])
            self._replace_index_entries(doc_id, [])
            self._replace_chunk_embeddings(doc_id, [])
            return
        if stage is DocumentJobStage.INDEX:
            self._replace_index_entries(doc_id, [])
            self._replace_chunk_embeddings(doc_id, [])

    def _delete_extracted(self, document: PersistedDocument) -> None:
        if self._artifact_store is None:
            return
        self._artifact_store.delete_extracted(
            workspace_id=document.workspace_id,
            doc_id=document.doc_id,
        )

    def _delete_normalized(self, document: PersistedDocument) -> None:
        if self._artifact_store is None:
            return
        self._artifact_store.delete_normalized(
            workspace_id=document.workspace_id,
            doc_id=document.doc_id,
        )

    def _replace_sections(self, doc_id: DocId, sections: list[Section]) -> None:
        if self._sections is not None:
            self._sections.replace_for_document(doc_id, sections)

    def _replace_chunks(self, doc_id: DocId, chunks: list[Chunk]) -> None:
        if self._chunks is not None:
            self._chunks.replace_for_document(doc_id, chunks)

    def _replace_index_entries(self, doc_id: DocId, entries: list[IndexEntry]) -> None:
        if self._index_entries is not None:
            self._index_entries.replace_for_document(doc_id, entries)

    def _replace_chunk_embeddings(
        self,
        doc_id: DocId,
        embeddings: list[ChunkEmbedding],
    ) -> None:
        if self._chunk_embeddings is not None:
            self._chunk_embeddings.replace_for_document(doc_id, embeddings)

    def _require_filename(self, filename: str | None) -> str:
        normalized = (filename or "").strip()
        if not normalized:
            raise UnsupportedDocumentError(
                "uploaded file must include a filename",
                error_code="missing_filename",
            )
        return normalized

    def _detect_source_type(self, *, filename: str, content: bytes) -> SourceType:
        suffix = Path(filename).suffix.lower()

        if suffix == ".pdf":
            if not content.startswith(b"%PDF-"):
                raise UnsupportedDocumentError(
                    "uploaded .pdf files must include recognizable PDF header bytes",
                    error_code="invalid_pdf_header",
                )
            return SourceType.PDF

        if suffix in {".md", ".markdown"}:
            try:
                content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise UnsupportedDocumentError(
                    "uploaded markdown files must be valid UTF-8 text",
                    error_code="markdown_not_utf8",
                ) from exc
            return SourceType.MARKDOWN

        raise UnsupportedDocumentError(
            "supported uploads are limited to text-based PDF and Markdown files",
            error_code="unsupported_source_type",
        )

    def _resolve_title(self, *, title: str | None, filename: str) -> str:
        normalized_title = (title or "").strip()
        if normalized_title:
            return normalized_title
        return Path(filename).stem

    def _checksum(self, content: bytes) -> str:
        digest = hashlib.sha256(content).hexdigest()
        return f"sha256:{digest}"

    def _raise_retry_not_allowed(
        self,
        *,
        message: str,
        error_code: str,
        document: PersistedDocument,
        failed_stage: DocumentJobStage | None = None,
    ) -> NoReturn:
        self._logger.retry_eligibility_rejected(
            doc_id=document.doc_id,
            workspace_id=document.workspace_id,
            ingest_status=document.ingest_status.value,
            failed_stage=None if failed_stage is None else failed_stage.value,
            error_code=error_code,
        )
        raise RetryNotAllowedError(message, error_code=error_code)


def _filename_extension(filename: str | None) -> str | None:
    if not filename:
        return None
    suffix = Path(filename).suffix.lower()
    return suffix or None
