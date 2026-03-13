from __future__ import annotations

from dataclasses import dataclass

from doc_forge.query.review import QueryCitationReview, QueryRunReviewSummary, QueryTraceReview
from e2e.support import QueryAnswerResponse, SystemDriver


@dataclass(frozen=True)
class ExecutedQueryRun:
    workspace_id: str
    question: str
    response: QueryAnswerResponse
    summary: QueryRunReviewSummary
    trace: QueryTraceReview
    citations_review: QueryCitationReview

    @property
    def query_id(self) -> str:
        return self.response.query_id


def execute_query_run(
    *,
    driver: SystemDriver,
    workspace_id: str,
    question: str,
) -> ExecutedQueryRun:
    response = driver.submit_query(question=question, workspace_id=workspace_id)
    summary = driver.get_query_summary(response.query_id)
    trace = driver.get_query_trace(response.query_id)
    citations_review = driver.get_query_citations(response.query_id)
    return ExecutedQueryRun(
        workspace_id=workspace_id,
        question=question,
        response=response,
        summary=summary,
        trace=trace,
        citations_review=citations_review,
    )
