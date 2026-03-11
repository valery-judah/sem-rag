"""Internal FastAPI app for document lifecycle runtime and operator actions."""

from __future__ import annotations

from typing import Annotated

from fastapi import Body, Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field

from parity.lifecycle.service import (
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
from parity.lifecycle.worker import DocumentLifecycleWorker
from parity.query import (
    CorpusSnapshot,
    InterpretedQuery,
    QueryRequest,
    QueryRunStatus,
    QueryService,
    RetrievedCandidate,
)
from parity.query.errors import CorpusBoundaryUnavailableError
from parity.stages import DocumentRegistrationError

from .deps import (
    get_document_lifecycle_service,
    get_document_lifecycle_worker,
    get_query_service,
)


class RetrievalQueryRequest(BaseModel):
    """Internal request payload for document-scoped retrieval smoke queries."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    query: str = Field(min_length=1)
    k: int = Field(default=3, ge=1)


class QuerySubmissionResult(BaseModel):
    """Internal response payload for Stage 3 retrieval execution."""

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    status: QueryRunStatus
    snapshot: CorpusSnapshot
    interpreted_query: InterpretedQuery
    retrieved_candidates: list[RetrievedCandidate] = Field(default_factory=list)
    message: str = Field(min_length=1)


def create_app() -> FastAPI:
    """Create the internal lifecycle app."""

    app = FastAPI()

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz(
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
    ) -> dict[str, str]:
        del service
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
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def submit_query(
        request: Annotated[QueryRequest, Body()],
        service: Annotated[QueryService, Depends(get_query_service)],
    ) -> QuerySubmissionResult:
        try:
            state = service.execute_until_retrieval(request)
        except CorpusBoundaryUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        if state.snapshot is None or state.interpreted_query is None:
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
            message="query retrieval completed; downstream stages are not implemented yet",
        )

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
