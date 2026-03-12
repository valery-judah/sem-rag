"""Internal FastAPI app for document lifecycle runtime and operator actions."""

from __future__ import annotations

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
    AnswerModeDecision,
    CitationBundle,
    ContextManifest,
    CorpusSnapshot,
    EvidenceSet,
    InterpretedQuery,
    QueryRequest,
    QueryRunStatus,
    QueryService,
    RetrievedCandidate,
    SupportAssessment,
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
)
from .logging import configure_logging


def _logger() -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(__name__)


class RetrievalQueryRequest(BaseModel):
    """Internal request payload for document-scoped retrieval smoke queries."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    query: str = Field(min_length=1)
    k: int = Field(default=3, ge=1)


class QuerySubmissionResult(BaseModel):
    """Internal response payload for Stage 7 end-to-end query execution."""

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    status: QueryRunStatus
    snapshot: CorpusSnapshot
    interpreted_query: InterpretedQuery
    retrieved_candidates: list[RetrievedCandidate] = Field(default_factory=list)
    selected_candidates: list[RetrievedCandidate] = Field(default_factory=list)
    evidence_sets: list[EvidenceSet] = Field(default_factory=list)
    context_manifest: ContextManifest
    support_assessment: SupportAssessment
    answer_mode_decision: AnswerModeDecision
    answer: AnswerDraft
    support_state: SupportState
    answer_mode: AnswerMode
    visible_limitations: list[str] = Field(default_factory=list)
    citations: CitationBundle
    message: str = Field(min_length=1)


class QuerySubmissionFailureResult(BaseModel):
    """Internal error payload for failed query submissions."""

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(min_length=1)
    status: QueryRunStatus
    terminal_failure: dict[str, object]


def create_app() -> FastAPI:
    """Create the internal lifecycle app."""

    configure_logging(
        service=os.environ.get("DOC_FORGE_SERVICE_NAME", "doc_forge-api"),
        environment=os.environ.get("DOC_FORGE_ENVIRONMENT", "dev"),
        level=os.environ.get("DOC_FORGE_LOG_LEVEL", "INFO"),
    )
    app = FastAPI()

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
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

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz(
        engine: Annotated[Engine, Depends(get_engine)],
        artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
    ) -> dict[str, str]:
        with engine.connect() as connection:
            connection.execute(sa.text("SELECT 1"))
        artifact_store.ensure_root_writable()
        return {"status": "ok"}

    @app.post(
        "/documents",
        response_model=UploadDocumentResult,
        status_code=status.HTTP_201_CREATED,
    )
    async def upload_document(
        workspace_id: Annotated[str, Form(min_length=1)],
        file: Annotated[UploadFile, File()],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
        title: Annotated[str | None, Form()] = None,
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

    @app.get("/documents/{doc_id}/status", response_model=DocumentStatusResult)
    async def get_document_status(
        doc_id: str,
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
    ) -> DocumentStatusResult:
        try:
            return service.get_document_status(doc_id=doc_id)
        except DocumentNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/documents/{doc_id}/artifacts", response_model=DocumentArtifactRefs)
    async def get_document_artifacts(
        doc_id: str,
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
    )
    async def retry_document(
        doc_id: str,
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
    )
    async def retrieval_query(
        request: Annotated[RetrievalQueryRequest, Body()],
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
        response_model=QuerySubmissionResult,
        status_code=status.HTTP_200_OK,
    )
    async def submit_query(
        request: Annotated[QueryRequest, Body()],
        service: Annotated[QueryService, Depends(get_query_service)],
    ) -> QuerySubmissionResult:
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
        return QuerySubmissionResult(
            query_id=state.run.query_id,
            workspace_id=state.run.workspace_id,
            status=state.run.status,
            snapshot=state.snapshot,
            interpreted_query=state.interpreted_query,
            retrieved_candidates=state.retrieved_candidates,
            selected_candidates=state.selected_candidates,
            evidence_sets=state.evidence_sets,
            context_manifest=state.context_manifest,
            support_assessment=state.support_assessment,
            answer_mode_decision=state.answer_mode_decision,
            answer=state.answer_draft,
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
    )
    async def get_query_summary(
        query_id: str,
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
    )
    async def get_query_trace(
        query_id: str,
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
    )
    async def get_query_citations(
        query_id: str,
        review_service: Annotated[QueryReviewService, Depends(get_query_review_service)],
    ) -> QueryCitationReview:
        try:
            return review_service.get_query_citations(query_id)
        except LookupError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.post("/internal/run-next-job")
    async def run_next_job(
        worker: Annotated[DocumentLifecycleWorker, Depends(get_document_lifecycle_worker)],
    ) -> dict[str, str | None]:
        job = worker.run_next()
        return {
            "job_id": None if job is None else job.job_id,
            "status": None if job is None else job.status.value,
        }

    return app


app = create_app()
