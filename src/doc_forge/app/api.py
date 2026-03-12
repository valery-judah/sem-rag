"""FastAPI app for the local document lifecycle and query service."""

from __future__ import annotations

import importlib.metadata
import os
from time import perf_counter
from typing import Annotated
from uuid import uuid4

import sqlalchemy as sa
import structlog
from fastapi import Body, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.engine import Engine
from structlog.contextvars import bind_contextvars, clear_contextvars

from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.identifiers import DocId, WorkspaceId
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
    AnswerMode,
    CitationBundle,
    QueryRequest,
    QueryRunStatus,
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


def _logger() -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(__name__)  # type: ignore


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

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(min_length=1, description="The unique query identifier.")
    answer_text: str = Field(min_length=1, description="The generated grounded answer text.")
    support_state: SupportState = Field(
        description="The assessed evidence support state (e.g., sufficient, partial, insufficient)."
    )
    answer_mode: AnswerMode = Field(
        description="The selected answer generation mode (e.g., direct_answer, full_abstention)."
    )
    visible_limitations: list[str] = Field(
        default_factory=list, description="Disclaimers regarding answer quality."
    )
    citations: CitationBundle = Field(description="The assembled citations supporting the answer.")
    message: str = Field(min_length=1, description="Human-readable result message.")


class QuerySubmissionFailureResult(BaseModel):
    """Internal error payload for failed query submissions."""

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(min_length=1, description="The unique query identifier.")
    status: QueryRunStatus = Field(description="The terminal status of the query (failed).")
    terminal_failure: dict[str, object] = Field(description="Detailed error tracing information.")


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

    model_config = ConfigDict(extra="forbid")

    detail: str = Field(
        ...,
        description="A human-readable explanation of the error.",
        json_schema_extra={"example": "The requested document was not found."},
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
    async def request_logging_middleware(request: Request, call_next):  # type: ignore
        request_id = f"req-{uuid4().hex}"
        bind_contextvars(request_id=request_id)
        started_at = perf_counter()
        _logger().info(
            "http.request.started",
            method=request.method,
            path=request.url.path,
        )
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((perf_counter() - started_at) * 1000)
            _logger().exception(
                "http.request.completed",
                method=request.method,
                path=request.url.path,
                status=500,
                duration_ms=duration_ms,
            )
            clear_contextvars()
            raise
        duration_ms = int((perf_counter() - started_at) * 1000)
        response.headers["x-request-id"] = request_id
        _logger().info(
            "http.request.completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        clear_contextvars()
        return response

    @app.get("/healthz", tags=["System"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["System"])
    async def readyz(
        engine: Annotated[Engine, Depends(get_engine)],
        artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
        vector_store: Annotated[VectorStore, Depends(get_vector_store)],
    ) -> dict[str, str]:
        with engine.connect() as connection:
            connection.execute(sa.text("SELECT 1"))
        artifact_store.ensure_root_writable()
        vector_store.smoke_query(doc_id="healthcheck", text="healthcheck", k=1)
        return {"status": "ok"}

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
    async def upload_document(
        workspace_id: Annotated[
            WorkspaceId,
            Form(description="The workspace this document belongs to."),
        ],
        file: Annotated[UploadFile, File(description="The document file (PDF or Markdown).")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
        title: Annotated[
            str | None,
            Form(
                description="Optional custom title for the document. If omitted, uses the filename."
            ),
        ] = None,
    ) -> UploadDocumentResult:
        content = await file.read()
        try:
            return service.upload_document(
                workspace_id=workspace_id,
                title=title,
                filename=file.filename,
                content=content,
            )
        except UnsupportedDocumentError as exc:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(exc),
            ) from exc
        except DocumentRegistrationError as exc:
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
    async def delete_document(
        doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
    ) -> None:
        try:
            service.delete_document(doc_id=doc_id)
        except DocumentNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get(
        "/documents/{doc_id}",
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
    async def get_document(
        doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
    ) -> dict[str, object]:
        try:
            document = service._require_document(doc_id)
            return {
                "doc_id": document.doc_id,
                "workspace_id": document.workspace_id,
                "source_type": document.source_type.value,
                "title": document.title,
                "filename": document.filename,
                "uploaded_at": document.uploaded_at.isoformat(),
                "checksum": document.checksum,
                "ingest_status": document.ingest_status.value,
                "failure_code": document.failure_code,
                "failure_detail": document.failure_detail,
                "raw_storage_path": document.raw_storage_path,
            }
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
    async def get_document_status(
        doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
    ) -> DocumentStatusResult:
        try:
            return service.get_document_status(doc_id=doc_id)
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
    async def get_document_artifacts(
        doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
    ) -> DocumentArtifactRefs:
        try:
            return service.get_artifact_refs(doc_id=doc_id)
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
    async def retry_document(
        doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
    ) -> RetryDocumentResult:
        try:
            return service.retry_document(doc_id=doc_id)
        except DocumentNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except RetryNotAllowedError as exc:
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
    async def retrieval_query(
        request: Annotated[RetrievalQueryRequest, Body(description="The query parameters.")],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
    ) -> RetrievalQueryResult:
        try:
            return service.query_document(
                doc_id=request.doc_id,
                text=request.query,
                k=request.k,
            )
        except DocumentNotFoundError as exc:
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
    async def submit_query(
        request: Annotated[QueryRequest, Body(description="The query request payload.")],
        service: Annotated[QueryService, Depends(get_query_service)],
    ) -> QueryAnswerResponse:
        try:
            state = service.execute_until_answer(request)
        except CorpusBoundaryUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except QueryExecutionFailedError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=QuerySubmissionFailureResult(
                    query_id=exc.query_id,
                    status=QueryRunStatus.FAILED,
                    terminal_failure=exc.terminal_failure.model_dump(mode="json"),
                ).model_dump(mode="json"),
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="query execution returned incomplete stage state",
            )
        return QueryAnswerResponse(
            query_id=state.run.query_id,
            answer_text=state.answer_draft.answer_text,
            support_state=state.support_assessment.support_state,
            answer_mode=state.answer_mode_decision.answer_mode,
            visible_limitations=state.answer_draft.visible_limitations,
            citations=state.citation_bundle,
            message="query answer completed with grounded generation and rendered citations",
        )

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
    async def get_query_summary(
        query_id: Annotated[str, Field(..., description="The unique query identifier.")],
        review_service: Annotated[QueryReviewService, Depends(get_query_review_service)],
    ) -> QueryRunReviewSummary:
        try:
            return review_service.get_query_summary(query_id)
        except LookupError as exc:
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
    async def get_query_trace(
        query_id: Annotated[str, Field(..., description="The unique query identifier.")],
        review_service: Annotated[QueryReviewService, Depends(get_query_review_service)],
    ) -> QueryTraceReview:
        try:
            return review_service.get_query_trace_review(query_id)
        except LookupError as exc:
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
    async def get_query_citations(
        query_id: Annotated[str, Field(..., description="The unique query identifier.")],
        review_service: Annotated[QueryReviewService, Depends(get_query_review_service)],
    ) -> QueryCitationReview:
        try:
            return review_service.get_query_citations(query_id)
        except LookupError as exc:
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
    async def run_next_job(
        worker: Annotated[DocumentLifecycleWorker, Depends(get_document_lifecycle_worker)],
    ) -> WorkerJobResult:
        job = worker.run_next()
        return WorkerJobResult(
            job_id=None if job is None else job.job_id,
            status=None if job is None else job.status.value,
        )

    return app


app = create_app()
