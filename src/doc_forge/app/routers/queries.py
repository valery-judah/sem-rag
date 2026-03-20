# ruff: noqa: B008
# pyright: reportUnusedFunction=false
from __future__ import annotations

import hashlib
from typing import Annotated

import structlog
from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import Field

from doc_forge.identifiers import QueryId
from doc_forge.query import (
    QueryRequest,
    QueryService,
)
from doc_forge.query.errors import CorpusBoundaryUnavailableError, QueryExecutionFailedError
from doc_forge.query.review import (
    QueryCitationReview,
    QueryReviewService,
    QueryRunReviewSummary,
    QueryTraceReview,
)

from ..deps import get_query_review_service, get_query_service
from ..logging import get_logger as get_app_logger
from ..schemas import ErrorResponse, QueryAnswerResponse


def get_logger() -> structlog.stdlib.BoundLogger:
    return get_app_logger(__name__)


router = APIRouter(tags=["Queries"])


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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


@router.get(
    "/queries/{query_id}",
    response_model=QueryRunReviewSummary,
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


@router.get(
    "/queries/{query_id}/trace",
    response_model=QueryTraceReview,
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


@router.get(
    "/queries/{query_id}/citations",
    response_model=QueryCitationReview,
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
