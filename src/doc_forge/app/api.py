# ruff: noqa: B008
# pyright: reportUnusedFunction=false
"""FastAPI app for the local document lifecycle and query service."""

from __future__ import annotations

import hashlib
import importlib.metadata
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from time import perf_counter
from typing import Annotated
from uuid import uuid4

import sqlalchemy as sa
import structlog
from fastapi import (
    Body,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.engine import Engine
from structlog.contextvars import bind_contextvars, clear_contextvars

from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.identifiers import DocId, QueryId, WorkspaceId
from doc_forge.indexing.base import VectorStore
from doc_forge.lifecycle.service import (
    DocumentArtifactRefs,
    DocumentLifecycleService,
    DocumentNotFoundError,
    DocumentStatusResult,
    RetrievalQueryResult,
    RetryDocumentResult,
    RetryNotAllowedError,
    UnsupportedDocumentError,
    UploadDocumentResult,
)
from doc_forge.lifecycle.worker import DocumentLifecycleWorker
from doc_forge.query import (
    AnswerDraft,
    AnswerMode,
    CitationBundle,
    QueryRequest,
    QueryService,
    SupportState,
)
from doc_forge.query.errors import CorpusBoundaryUnavailableError, QueryExecutionFailedError
from doc_forge.query.review import (
    QueryCitationReview,
    QueryReviewService,
    QueryRunReviewSummary,
    QueryTraceReview,
)
from doc_forge.stages import DocumentRegistrationError

from .deps import (
    get_artifact_store,
    get_document_lifecycle_service,
    get_document_lifecycle_worker,
    get_engine,
    get_query_review_service,
    get_query_service,
    get_vector_store,
)
from .logging import configure_logging
from .logging import get_logger as get_app_logger


def get_logger() -> structlog.stdlib.BoundLogger:
    return get_app_logger(__name__)


class RetrievalQueryRequest(BaseModel):
    """Internal request payload for document-scoped retrieval smoke queries."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "doc_id": "doc_1234abcd",
                "query": "What are the scalability limits of the new database?",
                "k": 3,
            }
        },
    )

    doc_id: DocId = Field(..., description="The ID of the document to query.")
    query: str = Field(
        min_length=1, description="The textual query to run against the document's chunks."
    )
    k: int = Field(default=3, ge=1, description="The maximum number of chunks to return.")


class QueryAnswerResponse(BaseModel):
    """Clean public-facing answer payload for a completed query."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "query_id": "qry_1234abcd",
                "answer": {
                    "answer_text": "Supports up to 10,000 concurrent connections.",
                    "visible_limitations": [],
                    "should_render_citations": True,
                    "grounded_evidence_set_ids": ["es_9876xyz"],
                    "generator_version": "v1.0",
                },
                "support_state": "sufficient",
                "answer_mode": "direct_answer",
                "citations": {
                    "citations": [
                        {
                            "evidence_set_id": "es_9876xyz",
                            "source_reference": {
                                "doc_id": "doc_1234abcd",
                                "document_title": "Database Architecture",
                                "snippet": "Supports up to 10,000 concurrent connections.",
                                "section_id": "sec_1",
                                "heading_path": ["Scalability"],
                                "page_label": "42",
                                "chunk_id": "chk_5678",
                                "passage_anchor": None,
                            },
                            "support_role": "primary",
                        }
                    ],
                    "material_doc_ids": ["doc_1234abcd"],
                    "renderer_version": "v1.0",
                },
                "message": "query answer completed with grounded generation and rendered citations",
            }
        },
    )

    query_id: QueryId = Field(min_length=1, description="The unique query identifier.")
    answer: AnswerDraft = Field(description="The generated answer draft.")
    support_state: SupportState = Field(
        description="The assessed evidence support state (e.g., sufficient, partial, insufficient)."
    )
    answer_mode: AnswerMode = Field(
        description="The selected answer generation mode (e.g., direct_answer, full_abstention)."
    )
    citations: CitationBundle = Field(description="The assembled citations supporting the answer.")
    message: str = Field(min_length=1, description="Human-readable result message.")


class WorkerJobResult(BaseModel):
    """Payload representing a triggered worker job result."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"job_id": "job_9876xyz", "status": "completed"}},
    )

    job_id: str | None = Field(default=None, description="The job ID that was executed, if any.")
    status: str | None = Field(
        default=None, description="The terminal status of the executed job, if any."
    )


class ErrorResponse(BaseModel):
    """Standardized error response payload."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"detail": "The requested document was not found."}},
    )

    detail: str = Field(
        ...,
        description="A human-readable explanation of the error.",
        json_schema_extra={"example": "The requested document was not found."},
    )


class SystemStatusResponse(BaseModel):
    """Standardized system status response payload."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": "ok"}},
    )

    status: str = Field(..., description="The current status of the system component.")


class DocumentDetailResponse(BaseModel):
    """Detailed metadata response for a specific registered document."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "doc_id": "doc_1234abcd",
                "workspace_id": "workspace_alpha",
                "source_type": "pdf",
                "title": "Database Architecture Design",
                "filename": "database_architecture.pdf",
                "uploaded_at": "2024-03-10T15:30:00Z",
                "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "ingest_status": "completed",
                "failure_code": None,
                "failure_detail": None,
                "raw_storage_path": "workspaces/workspace_alpha/documents/doc_1234abcd/raw.pdf",
            }
        },
    )

    doc_id: str = Field(min_length=1, description="The unique identifier of the document.")
    workspace_id: str = Field(min_length=1, description="The workspace this document belongs to.")
    source_type: str = Field(
        min_length=1, description="The type of the source artifact (e.g., pdf, markdown)."
    )
    title: str = Field(min_length=1, description="The title of the document.")
    filename: str = Field(min_length=1, description="The original filename of the document.")
    uploaded_at: str = Field(min_length=1, description="ISO-8601 formatted upload timestamp.")
    checksum: str = Field(
        min_length=1, description="SHA-256 checksum of the original source content."
    )
    ingest_status: str = Field(min_length=1, description="Current ingestion lifecycle status.")
    failure_code: str | None = Field(
        default=None, description="Standardized error code if the ingest failed."
    )
    failure_detail: str | None = Field(
        default=None, description="Human-readable detail if the ingest failed."
    )
    raw_storage_path: str = Field(
        min_length=1, description="The logical path where the raw file is stored."
    )


def create_app() -> FastAPI:
    """Create the local FastAPI service app."""

    environment = os.environ.get("DOC_FORGE_ENVIRONMENT", "prod")
    configure_logging(
        service=os.environ.get("DOC_FORGE_SERVICE_NAME", "doc_forge-api"),
        environment=environment,
        level=os.environ.get("DOC_FORGE_LOG_LEVEL", "INFO"),
    )

    enable_swagger_env = os.environ.get("DOC_FORGE_ENABLE_SWAGGER", "false").lower() == "true"
    enable_swagger = environment == "dev" or enable_swagger_env

    try:
        app_version = importlib.metadata.version("doc_forge")
    except importlib.metadata.PackageNotFoundError:
        app_version = "0.0.0-dev"

    app = FastAPI(
        title="Doc Forge Local API",
        description="Stable localhost document lifecycle and query API.",
        version=app_version,
        docs_url="/docs" if enable_swagger else None,
        openapi_url="/openapi.json" if enable_swagger else None,
        redoc_url=None,
    )

    @app.middleware("http")
    async def request_logging_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = f"req-{uuid4().hex}"
        bind_contextvars(request_id=request_id)
        started_at = perf_counter()
        get_logger().info(
            "http.request.started",
            method=request.method,
            path=request.url.path,
        )

        unhandled_exception = False
        try:
            response = await call_next(request)
        except Exception:
            unhandled_exception = True
            duration_ms = int((perf_counter() - started_at) * 1000)
            get_logger().exception(
                "http.request.completed",
                method=request.method,
                path=request.url.path,
                http_status=500,
                status=500,
                duration_ms=duration_ms,
            )
            response = JSONResponse(
                status_code=500,
                content=ErrorResponse(detail="Internal server error").model_dump(),
            )

        duration_ms = int((perf_counter() - started_at) * 1000)
        response.headers["x-request-id"] = request_id

        if not unhandled_exception:
            get_logger().info(
                "http.request.completed",
                method=request.method,
                path=request.url.path,
                http_status=response.status_code,
                status=response.status_code,
                duration_ms=duration_ms,
            )

        clear_contextvars()
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler for unhandled exceptions."""
        get_logger().exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(detail="Internal server error").model_dump(),
        )

    @app.get(
        "/healthz",
        tags=["System"],
        response_model=SystemStatusResponse,
        summary="Health Check",
        description=(
            "Lightweight liveness probe that indicates whether the application process is running."
        ),
        responses={
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "model": ErrorResponse,
                "description": "Internal server error",
            },
        },
    )
    def healthz() -> SystemStatusResponse:
        return SystemStatusResponse(status="ok")

    @app.get(
        "/readyz",
        tags=["System"],
        response_model=SystemStatusResponse,
        summary="Readiness Check",
        description=(
            "Deep readiness probe that validates connections to the "
            "database, vector store, and artifact storage."
        ),
        responses={
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "model": ErrorResponse,
                "description": "Readiness check failed due to unreachable dependencies",
            },
        },
    )
    def readyz(
        engine: Annotated[Engine, Depends(get_engine)],
        artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
        vector_store: Annotated[VectorStore, Depends(get_vector_store)],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    ) -> SystemStatusResponse:
        logger.info("system.readyz.started")
        try:
            with engine.connect() as connection:
                connection.execute(sa.text("SELECT 1"))
            artifact_store.ensure_root_writable()
            vector_store.smoke_query(doc_id="healthcheck", text="healthcheck", k=1)
        except Exception:
            logger.exception(
                "system.readyz.failed",
                http_status=500,
                error_code="ready_check_failed",
            )
            raise
        logger.info("system.readyz.completed", http_status=200, status="ok")
        return SystemStatusResponse(status="ok")

    @app.post(
        "/documents",
        response_model=UploadDocumentResult,
        status_code=status.HTTP_201_CREATED,
        summary="Upload Document",
        tags=["Documents"],
        description=(
            "Upload a PDF or Markdown document to be processed and indexed "
            "into the vector store. This initiates a background lifecycle job.\n\n"
            "**State Transition:** Starts at `REGISTERED` and is queued for `EXTRACT`."
        ),
        responses={
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
                "model": ErrorResponse,
                "description": "Unsupported document type",
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "model": ErrorResponse,
                "description": "Document registration failed",
            },
        },
    )
    def upload_document(
        workspace_id: Annotated[
            WorkspaceId,
            Form(description="The workspace this document belongs to."),
        ],
        file: Annotated[UploadFile, File(description="The document file (PDF or Markdown).")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
        title: Annotated[
            str | None,
            Form(
                description="Optional custom title for the document. If omitted, uses the filename."
            ),
        ] = None,
    ) -> UploadDocumentResult:
        content = file.file.read()
        try:
            result = service.upload_document(
                workspace_id=workspace_id,
                title=title,
                filename=file.filename,
                content=content,
            )
            logger.info(
                "document.upload.accepted",
                workspace_id=workspace_id,
                doc_id=result.doc_id,
                source_type=result.source_type.value,
                filename_extension=_filename_extension(file.filename),
                size_bytes=len(content),
                checksum_sha256=result.checksum,
                http_status=status.HTTP_201_CREATED,
                status="accepted",
            )
            return result
        except UnsupportedDocumentError as exc:
            logger.warning(
                "document.upload.rejected",
                workspace_id=workspace_id,
                filename_extension=_filename_extension(file.filename),
                size_bytes=len(content),
                error_code=exc.error_code,
                http_status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                status="rejected",
            )
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(exc),
            ) from exc
        except DocumentRegistrationError as exc:
            logger.exception(
                "document.upload.rejected",
                workspace_id=workspace_id,
                filename_extension=_filename_extension(file.filename),
                size_bytes=len(content),
                error_code="document_registration_failed",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                status="rejected",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="document registration failed",
            ) from exc

    @app.delete(
        "/documents/{doc_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete Document",
        tags=["Documents"],
        description="Completely remove a document, its artifacts, and its indexing data.",
        responses={
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorResponse,
                "description": "Document not found",
            },
        },
    )
    def delete_document(
        doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    ) -> None:
        logger.info("document.delete.started", doc_id=doc_id)
        try:
            service.delete_document(doc_id=doc_id)
        except DocumentNotFoundError as exc:
            logger.warning(
                "document.delete.rejected",
                doc_id=doc_id,
                error_code="document_not_found",
                http_status=status.HTTP_404_NOT_FOUND,
                status="rejected",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        logger.info(
            "document.delete.completed",
            doc_id=doc_id,
            http_status=status.HTTP_204_NO_CONTENT,
            status="completed",
        )

    @app.get(
        "/documents/{doc_id}",
        response_model=DocumentDetailResponse,
        summary="Get Document",
        tags=["Documents"],
        description="Retrieve the core details of a registered document.",
        responses={
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorResponse,
                "description": "Document not found",
            },
        },
    )
    def get_document(
        doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
    ) -> DocumentDetailResponse:
        try:
            document = service.require_document(doc_id)
            return DocumentDetailResponse(
                doc_id=document.doc_id,
                workspace_id=document.workspace_id,
                source_type=document.source_type.value,
                title=document.title,
                filename=document.filename,
                uploaded_at=document.uploaded_at.isoformat(),
                checksum=document.checksum or "",
                ingest_status=document.ingest_status.value,
                failure_code=document.failure_code,
                failure_detail=document.failure_detail,
                raw_storage_path=document.raw_storage_path or "",
            )
        except DocumentNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get(
        "/documents/{doc_id}/status",
        response_model=DocumentStatusResult,
        summary="Get Document Status",
        tags=["Documents"],
        description=(
            "Check the current ingestion status and active job stage "
            "for a previously uploaded document."
        ),
        responses={
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorResponse,
                "description": "Document not found",
            },
        },
    )
    def get_document_status(
        doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    ) -> DocumentStatusResult:
        try:
            result = service.get_document_status(doc_id=doc_id)
            logger.info(
                "document.status.loaded",
                doc_id=doc_id,
                ingest_status=result.ingest_status.value,
                active_job_stage=(
                    None if result.active_job_stage is None else result.active_job_stage.value
                ),
                http_status=status.HTTP_200_OK,
                status="loaded",
            )
            return result
        except DocumentNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get(
        "/documents/{doc_id}/artifacts",
        response_model=DocumentArtifactRefs,
        summary="Get Document Artifact References",
        tags=["Documents"],
        description=(
            "Retrieve the filesystem paths where raw, extracted, "
            "and normalized artifacts are stored."
        ),
        responses={
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorResponse,
                "description": "Document not found",
            },
        },
    )
    def get_document_artifacts(
        doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    ) -> DocumentArtifactRefs:
        try:
            result = service.get_artifact_refs(doc_id=doc_id)
            logger.info(
                "document.artifacts.loaded",
                doc_id=doc_id,
                has_extracted=result.extracted_path is not None,
                has_normalized=result.normalized_path is not None,
                http_status=status.HTTP_200_OK,
                status="loaded",
            )
            return result
        except DocumentNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.post(
        "/documents/{doc_id}/retry",
        response_model=RetryDocumentResult,
        status_code=status.HTTP_202_ACCEPTED,
        summary="Retry Failed Document",
        tags=["Documents"],
        description=(
            "Queue a retry for a document that failed during its ingestion lifecycle.\n\n"
            "Idempotent: Re-queues the failed stage and resets downstream artifacts."
        ),
        responses={
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorResponse,
                "description": "Document not found",
            },
            status.HTTP_409_CONFLICT: {
                "model": ErrorResponse,
                "description": "Retry not allowed or already in progress",
            },
        },
    )
    def retry_document(
        doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    ) -> RetryDocumentResult:
        logger.info("document.retry.requested", doc_id=doc_id)
        try:
            result = service.retry_document(doc_id=doc_id)
            logger.info(
                "document.retry.queued",
                doc_id=doc_id,
                queued_stage=result.queued_stage.value,
                ingest_status=result.ingest_status.value,
                http_status=status.HTTP_202_ACCEPTED,
                status="queued",
            )
            return result
        except DocumentNotFoundError as exc:
            logger.warning(
                "document.retry.rejected",
                doc_id=doc_id,
                error_code="document_not_found",
                http_status=status.HTTP_404_NOT_FOUND,
                status="rejected",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except RetryNotAllowedError as exc:
            logger.warning(
                "document.retry.rejected",
                doc_id=doc_id,
                error_code=exc.error_code,
                http_status=status.HTTP_409_CONFLICT,
                status="rejected",
            )
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @app.post(
        "/retrieval/query",
        response_model=RetrievalQueryResult,
        status_code=status.HTTP_200_OK,
        summary="Smoke Query Document",
        tags=["Retrieval"],
        description=(
            "Perform a semantic search against the vector store "
            "for a specific document to retrieve the top-K chunks.\n\n"
            "Note: This is an internal smoke test endpoint for validating indexing."
        ),
        responses={
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorResponse,
                "description": "Document not found",
            },
        },
    )
    def retrieval_query(
        request: Annotated[RetrievalQueryRequest, Body(description="The query parameters.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    ) -> RetrievalQueryResult:
        logger.info(
            "retrieval.smoke.started",
            doc_id=request.doc_id,
            k=request.k,
            query_chars=len(request.query),
            query_sha256=_sha256_text(request.query),
        )
        try:
            result = service.query_document(
                doc_id=request.doc_id,
                text=request.query,
                k=request.k,
            )
            top_hit = result.hits[0] if result.hits else None
            logger.info(
                "retrieval.smoke.completed",
                doc_id=request.doc_id,
                k=request.k,
                hit_count=len(result.hits),
                top_hit_doc_id=None if top_hit is None else top_hit.doc_id,
                top_hit_chunk_id=None if top_hit is None else top_hit.chunk_id,
                http_status=status.HTTP_200_OK,
                status="completed",
            )
            return result
        except DocumentNotFoundError as exc:
            logger.warning(
                "retrieval.smoke.rejected",
                doc_id=request.doc_id,
                k=request.k,
                error_code="document_not_found",
                http_status=status.HTTP_404_NOT_FOUND,
                status="rejected",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.post(
        "/queries",
        response_model=QueryAnswerResponse,
        status_code=status.HTTP_200_OK,
        summary="Submit Query",
        tags=["Queries"],
        description=(
            "Execute a query against the document corpus and return a grounded answer "
            "with citations."
        ),
        responses={
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "model": ErrorResponse,
                "description": "Query execution failed or returned incomplete state",
            },
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "model": ErrorResponse,
                "description": "Corpus boundary unavailable",
            },
        },
    )
    def submit_query(
        request: Annotated[QueryRequest, Body(description="The query request payload.")],
        service: Annotated[QueryService, Depends(get_query_service)],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    ) -> QueryAnswerResponse:
        question_sha256 = _sha256_text(request.question)
        logger.info(
            "query.api.started",
            workspace_id=request.workspace_id,
            question_chars=len(request.question),
            question_sha256=question_sha256,
        )
        try:
            state = service.execute_until_answer(request)
        except CorpusBoundaryUnavailableError as exc:
            logger.warning(
                "query.api.rejected",
                workspace_id=request.workspace_id,
                question_sha256=question_sha256,
                error_code="corpus_boundary_unavailable",
                http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
                status="rejected",
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except QueryExecutionFailedError as exc:
            logger.exception(
                "query.api.rejected",
                workspace_id=request.workspace_id,
                query_id=exc.query_id,
                question_sha256=question_sha256,
                error_code=exc.terminal_failure.error_code,
                stage_name=(
                    None
                    if exc.terminal_failure.stage_name is None
                    else exc.terminal_failure.stage_name.value
                ),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                status="rejected",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="query execution failed",
            ) from exc
        if (
            state.snapshot is None
            or state.interpreted_query is None
            or state.context_manifest is None
            or state.support_assessment is None
            or state.answer_mode_decision is None
            or state.answer_draft is None
            or state.citation_bundle is None
        ):
            logger.error(
                "query.api.rejected",
                workspace_id=request.workspace_id,
                query_id=state.run.query_id,
                question_sha256=question_sha256,
                error_code="incomplete_query_state",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                status="rejected",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="query execution returned incomplete stage state",
            )
        response = QueryAnswerResponse(
            query_id=state.run.query_id,
            answer=state.answer_draft,
            support_state=state.support_assessment.support_state,
            answer_mode=state.answer_mode_decision.answer_mode,
            citations=state.citation_bundle,
            message="query answer completed with grounded generation and rendered citations",
        )
        logger.info(
            "query.api.completed",
            workspace_id=request.workspace_id,
            query_id=response.query_id,
            support_state=response.support_state.value,
            answer_mode=response.answer_mode.value,
            citation_count=len(response.citations.citations),
            http_status=status.HTTP_200_OK,
            status="completed",
        )
        return response

    @app.get(
        "/queries/{query_id}",
        response_model=QueryRunReviewSummary,
        status_code=status.HTTP_200_OK,
        summary="Get Query Summary",
        tags=["Queries"],
        description="Load a summary view for a single persisted query run.",
        responses={
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorResponse,
                "description": "Query run not found",
            },
        },
    )
    def get_query_summary(
        query_id: Annotated[QueryId, Field(..., description="The unique query identifier.")],
        review_service: Annotated[QueryReviewService, Depends(get_query_review_service)],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    ) -> QueryRunReviewSummary:
        try:
            result = review_service.get_query_summary(query_id)
            logger.info(
                "review.summary.loaded",
                query_id=query_id,
                trace_count=result.trace_summary.trace_count,
                has_answer=result.has_answer,
                http_status=status.HTTP_200_OK,
                status="loaded",
            )
            return result
        except LookupError as exc:
            logger.warning(
                "query.review.lookup_failed",
                query_id=query_id,
                review_type="summary",
                error_code="query_run_not_found",
                http_status=status.HTTP_404_NOT_FOUND,
                status="rejected",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get(
        "/queries/{query_id}/trace",
        response_model=QueryTraceReview,
        status_code=status.HTTP_200_OK,
        summary="Get Query Trace Review",
        tags=["Queries"],
        description="Load the full stage-by-stage persisted trace chain for a given query run.",
        responses={
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorResponse,
                "description": "Query run not found",
            },
        },
    )
    def get_query_trace(
        query_id: Annotated[QueryId, Field(..., description="The unique query identifier.")],
        review_service: Annotated[QueryReviewService, Depends(get_query_review_service)],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    ) -> QueryTraceReview:
        try:
            result = review_service.get_query_trace_review(query_id)
            logger.info(
                "review.trace.loaded",
                query_id=query_id,
                trace_count=len(result.trace_bundle.stage_traces),
                has_answer=result.final_artifacts is not None,
                http_status=status.HTTP_200_OK,
                status="loaded",
            )
            return result
        except LookupError as exc:
            logger.warning(
                "query.review.lookup_failed",
                query_id=query_id,
                review_type="trace",
                error_code="query_run_not_found",
                http_status=status.HTTP_404_NOT_FOUND,
                status="rejected",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get(
        "/queries/{query_id}/citations",
        response_model=QueryCitationReview,
        status_code=status.HTTP_200_OK,
        summary="Get Query Citations",
        tags=["Queries"],
        description="Load only the persisted citation artifacts for a completed query run.",
        responses={
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorResponse,
                "description": "Query run or citations not found",
            },
        },
    )
    def get_query_citations(
        query_id: Annotated[QueryId, Field(..., description="The unique query identifier.")],
        review_service: Annotated[QueryReviewService, Depends(get_query_review_service)],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    ) -> QueryCitationReview:
        try:
            result = review_service.get_query_citations(query_id)
            logger.info(
                "review.citations.loaded",
                query_id=query_id,
                citation_count=len(result.citations.citations),
                support_state=result.support_state.value,
                answer_mode=result.answer_mode.value,
                http_status=status.HTTP_200_OK,
                status="loaded",
            )
            return result
        except LookupError as exc:
            logger.warning(
                "query.review.lookup_failed",
                query_id=query_id,
                review_type="citations",
                error_code="query_answer_not_found",
                http_status=status.HTTP_404_NOT_FOUND,
                status="rejected",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.post(
        "/internal/run-next-job",
        response_model=WorkerJobResult,
        status_code=status.HTTP_200_OK,
        summary="Run Next Job (Internal)",
        description=(
            "Trigger the internal background worker to process the next job in the "
            "document lifecycle queue."
        ),
        tags=["Internal Operator"],
    )
    def run_next_job(
        worker: Annotated[DocumentLifecycleWorker, Depends(get_document_lifecycle_worker)],
        logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    ) -> WorkerJobResult:
        logger.info("worker.run_next.invoked")
        job = worker.run_next()
        if job is None:
            logger.info(
                "worker.run_next.idle",
                http_status=status.HTTP_200_OK,
                status="idle",
            )
        else:
            logger.info(
                "worker.run_next.completed",
                doc_id=job.doc_id,
                job_id=job.job_id,
                stage_name=job.target_stage.value,
                http_status=status.HTTP_200_OK,
                status=job.status.value,
            )
        return WorkerJobResult(
            job_id=None if job is None else job.job_id,
            status=None if job is None else job.status.value,
        )

    return app


app = create_app()


def _filename_extension(filename: str | None) -> str | None:
    if not filename:
        return None
    suffix = Path(filename).suffix.lower()
    return suffix or None


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
