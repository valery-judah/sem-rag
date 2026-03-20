# ruff: noqa: B008
# pyright: reportUnusedFunction=false
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, status
from pydantic import Field

from doc_forge.app.services.queries import QueriesAppService
from doc_forge.identifiers import QueryId

from ..deps import get_queries_app_service
from ..schemas import (
    ErrorResponse,
    QueryAnswerResponse,
    QueryCitationReviewResponse,
    QueryRunSummaryResponse,
    QueryTraceReviewResponse,
    SubmitQueryRequest,
)

router = APIRouter(tags=["Queries"])


@router.post(
    "/queries",
    response_model=QueryAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Query",
    description=(
        "Execute a query against the document corpus and return a grounded answer with citations."
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
    request: Annotated[SubmitQueryRequest, Body(description="The query request payload.")],
    service: Annotated[QueriesAppService, Depends(get_queries_app_service)],
) -> QueryAnswerResponse:
    return service.submit_query(request)


@router.get(
    "/queries/{query_id}",
    response_model=QueryRunSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Query Summary",
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
    service: Annotated[QueriesAppService, Depends(get_queries_app_service)],
) -> QueryRunSummaryResponse:
    return service.get_query_summary(query_id)


@router.get(
    "/queries/{query_id}/trace",
    response_model=QueryTraceReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Query Trace Review",
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
    service: Annotated[QueriesAppService, Depends(get_queries_app_service)],
) -> QueryTraceReviewResponse:
    return service.get_query_trace(query_id)


@router.get(
    "/queries/{query_id}/citations",
    response_model=QueryCitationReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Query Citations",
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
    service: Annotated[QueriesAppService, Depends(get_queries_app_service)],
) -> QueryCitationReviewResponse:
    return service.get_query_citations(query_id)
