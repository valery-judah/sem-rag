from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from ..deps import get_internal_app_service
from ..schemas import ErrorResponse, RetrievalQueryRequest, RetrievalQueryResponse, WorkerJobResult
from ..services.internal import InternalAppService

router = APIRouter()


@router.post(
    "/retrieval/query",
    response_model=RetrievalQueryResponse,
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
    service: Annotated[InternalAppService, Depends(get_internal_app_service)],
) -> RetrievalQueryResponse:
    return service.retrieval_query(request)


@router.post(
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
    service: Annotated[InternalAppService, Depends(get_internal_app_service)],
) -> WorkerJobResult:
    return service.run_next_job()
