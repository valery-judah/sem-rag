from __future__ import annotations

import hashlib

from fastapi import HTTPException, status

from doc_forge.identifiers import QueryId
from doc_forge.query import (
    QueryRequest,
    QueryService,
)
from doc_forge.query.errors import CorpusBoundaryUnavailableError, QueryExecutionFailedError
from doc_forge.query.review import (
    QueryReviewService,
)

from ..logging import get_logger as get_app_logger
from ..schemas import (
    AnswerDraft,
    AnswerMode,
    CitationBundle,
    QueryAnswerResponse,
    QueryCitationReviewResponse,
    QueryRunSummaryResponse,
    QueryTraceReviewResponse,
    SubmitQueryRequest,
    SupportState,
)

logger = get_app_logger(__name__)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class QueriesAppService:
    """Orchestrates query submission, logging, exception mapping, and response shaping."""

    def __init__(
        self,
        query_service: QueryService,
        review_service: QueryReviewService,
    ) -> None:
        self._query_service = query_service
        self._review_service = review_service

    def submit_query(self, request: SubmitQueryRequest) -> QueryAnswerResponse:
        question_sha256 = _sha256_text(request.question)
        logger.info(
            "query.api.started",
            workspace_id=request.workspace_id,
            question_chars=len(request.question),
            question_sha256=question_sha256,
        )
        try:
            internal_request = QueryRequest.model_validate(request, from_attributes=True)
            state = self._query_service.execute_until_answer(internal_request)
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
            answer=AnswerDraft.model_validate(state.answer_draft, from_attributes=True),
            support_state=SupportState(state.support_assessment.support_state.value),
            answer_mode=AnswerMode(state.answer_mode_decision.answer_mode.value),
            citations=CitationBundle.model_validate(state.citation_bundle, from_attributes=True),
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

    def get_query_summary(self, query_id: QueryId) -> QueryRunSummaryResponse:
        try:
            result = self._review_service.get_query_summary(query_id)
            logger.info(
                "review.summary.loaded",
                query_id=query_id,
                trace_count=result.trace_summary.trace_count,
                has_answer=result.has_answer,
                http_status=status.HTTP_200_OK,
                status="loaded",
            )
            return QueryRunSummaryResponse.model_validate(result, from_attributes=True)
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

    def get_query_trace(self, query_id: QueryId) -> QueryTraceReviewResponse:
        try:
            result = self._review_service.get_query_trace_review(query_id)
            logger.info(
                "review.trace.loaded",
                query_id=query_id,
                trace_count=len(result.trace_bundle.stage_traces),
                has_answer=result.final_artifacts is not None,
                http_status=status.HTTP_200_OK,
                status="loaded",
            )
            return QueryTraceReviewResponse.model_validate(result, from_attributes=True)
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

    def get_query_citations(self, query_id: QueryId) -> QueryCitationReviewResponse:
        try:
            result = self._review_service.get_query_citations(query_id)
            logger.info(
                "review.citations.loaded",
                query_id=query_id,
                citation_count=len(result.citations.citations),
                support_state=result.support_state.value,
                answer_mode=result.answer_mode.value,
                http_status=status.HTTP_200_OK,
                status="loaded",
            )
            return QueryCitationReviewResponse.model_validate(result, from_attributes=True)
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
