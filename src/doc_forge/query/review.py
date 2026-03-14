"""Read-side review models and service for persisted query runs."""

from __future__ import annotations

from datetime import datetime

import structlog
from pydantic import BaseModel, ConfigDict, Field

from doc_forge.app.log_events import LogEvent
from doc_forge.app.logging import get_logger
from doc_forge.identifiers import DocId, QueryId, WorkspaceId

from .contracts import (
    AnswerMode,
    CitationBundle,
    CorpusSnapshot,
    FinalQueryArtifacts,
    QueryRun,
    QueryRunStatus,
    QueryTerminalFailure,
    SupportState,
    TrustFailureLabel,
)
from .persistence import QueryAnswerStore, QueryRunStore, QuerySnapshotStore, QueryTraceStore
from .trace import QueryStageTrace, QueryTraceBundle

logger = get_logger(__name__)


class QuerySnapshotSummary(BaseModel):
    """Compact summary of the persisted corpus snapshot for review views."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: WorkspaceId = Field(min_length=1, description="The workspace scope.")
    query_started_at: datetime = Field(description="When the query snapshot was taken.")
    eligible_doc_ids: list[DocId] = Field(
        default_factory=lambda: [], description="Document IDs included in the corpus snapshot."
    )
    retrieval_index_version: str | None = Field(
        default=None, description="The vector index version used."
    )
    readiness_version: str | None = Field(
        default=None, description="The readiness model version used."
    )


class QueryStageTimingSummary(BaseModel):
    """Timing summary for one persisted query stage."""

    model_config = ConfigDict(extra="forbid")

    stage_name: str = Field(min_length=1, description="Name of the stage.")
    stage_status: str = Field(min_length=1, description="Terminal status of the stage.")
    started_at: datetime = Field(description="When the stage execution began.")
    finished_at: datetime | None = Field(
        default=None, description="When the stage execution completed."
    )
    duration_ms: int | None = Field(
        default=None, ge=0, description="Execution duration in milliseconds."
    )


class QueryTraceTimingSummary(BaseModel):
    """Aggregate timing summary for a query run."""

    model_config = ConfigDict(extra="forbid")

    trace_count: int = Field(ge=0, description="Number of recorded stage traces.")
    total_duration_ms: int | None = Field(
        default=None, ge=0, description="Total duration across all stages."
    )
    stages: list[QueryStageTimingSummary] = Field(
        default_factory=lambda: [], description="Timing breakdown per stage."
    )


class QueryRunReviewSummary(BaseModel):
    """Summary view over one persisted query run."""

    model_config = ConfigDict(extra="forbid")

    query_id: QueryId = Field(min_length=1, description="The unique query identifier.")
    workspace_id: WorkspaceId = Field(
        min_length=1,
        description="The workspace this query was executed in.",
    )
    question: str = Field(min_length=1, description="The user's original question.")
    status: QueryRunStatus = Field(description="Terminal status of the overall query run.")
    submitted_at: datetime = Field(description="When the query was submitted.")
    completed_at: datetime | None = Field(
        default=None, description="When the query finished executing."
    )
    policy_snapshot: dict[str, object] = Field(
        description="The applied policy configuration for this run."
    )
    snapshot_summary: QuerySnapshotSummary | None = Field(
        default=None, description="Snapshot of the corpus used."
    )
    support_state: SupportState | None = Field(
        default=None, description="The assessed evidence support state."
    )
    answer_mode: AnswerMode | None = Field(
        default=None, description="The selected answer generation mode."
    )
    trust_failure_labels: list[TrustFailureLabel] = Field(
        default_factory=lambda: [], description="Identified trust failure signals."
    )
    visible_limitations: list[str] = Field(
        default_factory=lambda: [], description="Disclaimers regarding answer quality."
    )
    has_answer: bool = Field(
        default=False, description="Whether a final answer was successfully generated."
    )
    terminal_failure: QueryTerminalFailure | None = Field(
        default=None, description="Details if the query failed execution."
    )
    trace_summary: QueryTraceTimingSummary = Field(description="Aggregated stage timing details.")


class QueryTraceReview(BaseModel):
    """Detailed persisted trace review payload."""

    model_config = ConfigDict(extra="forbid")

    summary: QueryRunReviewSummary = Field(description="Overall query run summary.")
    snapshot: CorpusSnapshot | None = Field(
        default=None, description="The corpus snapshot captured at query time."
    )
    trace_bundle: QueryTraceBundle = Field(description="The full stage-by-stage execution trace.")
    final_artifacts: FinalQueryArtifacts | None = Field(
        default=None,
        description="The final answer and citation artifacts, if generation succeeded.",
    )


class QueryCitationReview(BaseModel):
    """Citation-only review payload."""

    model_config = ConfigDict(extra="forbid")

    query_id: QueryId = Field(min_length=1, description="The unique query identifier.")
    support_state: SupportState = Field(description="The assessed evidence support state.")
    answer_mode: AnswerMode = Field(description="The selected answer generation mode.")
    trust_failure_labels: list[TrustFailureLabel] = Field(
        default_factory=lambda: [], description="Identified trust failure signals."
    )
    citations: CitationBundle = Field(description="The assembled citations for the answer.")


class QueryReviewLogger:
    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._logger = logger

    def query_loaded(
        self, query_id: QueryId, status: str, trace_count: int, has_answer: bool
    ) -> None:
        self._logger.info(
            LogEvent.REVIEW_QUERY_LOADED,
            query_id=query_id,
            status=status,
            trace_count=trace_count,
            has_answer=has_answer,
        )

    def trace_loaded(self, query_id: QueryId, trace_count: int, has_answer: bool) -> None:
        self._logger.info(
            LogEvent.REVIEW_TRACE_LOADED,
            query_id=query_id,
            trace_count=trace_count,
            has_answer=has_answer,
        )

    def citations_loaded(
        self, query_id: QueryId, citation_count: int, support_state: str, answer_mode: str
    ) -> None:
        self._logger.info(
            LogEvent.REVIEW_CITATIONS_LOADED,
            query_id=query_id,
            citation_count=citation_count,
            support_state=support_state,
            answer_mode=answer_mode,
        )


class QueryReviewService:
    """Read-only review service over persisted query artifacts."""

    def __init__(
        self,
        *,
        run_store: QueryRunStore,
        snapshot_store: QuerySnapshotStore,
        trace_store: QueryTraceStore,
        answer_store: QueryAnswerStore,
        logger: QueryReviewLogger | None = None,
    ) -> None:
        self._run_store = run_store
        self._snapshot_store = snapshot_store
        self._trace_store = trace_store
        self._answer_store = answer_store
        self._logger = logger or QueryReviewLogger(get_logger(self.__class__.__name__))

    def get_query_summary(self, query_id: QueryId) -> QueryRunReviewSummary:
        """Load a summary view for one persisted query run."""

        run = self._get_run(query_id)
        snapshot = self._snapshot_store.get_snapshot(query_id)
        traces = self._trace_store.list_stage_traces(query_id)
        answer = self._answer_store.get_answer_artifacts(query_id)
        summary = _build_summary(run=run, snapshot=snapshot, traces=traces, answer=answer)
        self._logger.query_loaded(
            query_id=query_id,
            status=summary.status.value,
            trace_count=summary.trace_summary.trace_count,
            has_answer=summary.has_answer,
        )
        return summary

    def get_query_trace_review(self, query_id: QueryId) -> QueryTraceReview:
        """Load the persisted trace chain for one query run."""

        run = self._get_run(query_id)
        snapshot = self._snapshot_store.get_snapshot(query_id)
        traces = self._trace_store.list_stage_traces(query_id)
        answer = self._answer_store.get_answer_artifacts(query_id)
        summary = _build_summary(run=run, snapshot=snapshot, traces=traces, answer=answer)
        self._logger.trace_loaded(
            query_id=query_id, trace_count=len(traces), has_answer=answer is not None
        )
        return QueryTraceReview(
            summary=summary,
            snapshot=snapshot,
            trace_bundle=QueryTraceBundle(
                query_id=query_id,
                run_status=run.status,
                stage_traces=traces,
            ),
            final_artifacts=answer,
        )

    def get_query_citations(self, query_id: QueryId) -> QueryCitationReview:
        """Load persisted citation artifacts for one completed query run."""

        self._get_run(query_id)
        answer = self._answer_store.get_answer_artifacts(query_id)
        if answer is None:
            raise LookupError(f"query answer for {query_id!r} was not found")
        self._logger.citations_loaded(
            query_id=query_id,
            citation_count=len(answer.citations.citations),
            support_state=answer.support_state.value,
            answer_mode=answer.answer_mode.value,
        )
        return QueryCitationReview(
            query_id=query_id,
            support_state=answer.support_state,
            answer_mode=answer.answer_mode,
            trust_failure_labels=answer.trust_failure_labels,
            citations=answer.citations,
        )

    def _get_run(self, query_id: QueryId) -> QueryRun:
        run = self._run_store.get_query_run(query_id)
        if run is None:
            raise LookupError(f"query run {query_id!r} was not found")
        return run


def _build_summary(
    *,
    run: QueryRun,
    snapshot: CorpusSnapshot | None,
    traces: list[QueryStageTrace],
    answer: FinalQueryArtifacts | None,
) -> QueryRunReviewSummary:
    trace_summary = _build_trace_timing_summary(traces)
    return QueryRunReviewSummary(
        query_id=run.query_id,
        workspace_id=run.workspace_id,
        question=run.question,
        status=run.status,
        submitted_at=run.submitted_at,
        completed_at=run.completed_at,
        policy_snapshot=run.policy_snapshot,
        snapshot_summary=(
            None
            if snapshot is None
            else QuerySnapshotSummary(
                workspace_id=snapshot.workspace_id,
                query_started_at=snapshot.query_started_at,
                eligible_doc_ids=snapshot.eligible_doc_ids,
                retrieval_index_version=snapshot.retrieval_index_version,
                readiness_version=snapshot.readiness_version,
            )
        ),
        support_state=None if answer is None else answer.support_state,
        answer_mode=None if answer is None else answer.answer_mode,
        trust_failure_labels=(
            run.terminal_failure.trust_failure_labels
            if run.terminal_failure is not None
            else ([] if answer is None else answer.trust_failure_labels)
        ),
        visible_limitations=[] if answer is None else answer.answer.visible_limitations,
        has_answer=answer is not None,
        terminal_failure=run.terminal_failure,
        trace_summary=trace_summary,
    )


def _build_trace_timing_summary(traces: list[QueryStageTrace]) -> QueryTraceTimingSummary:
    stage_summaries = [
        QueryStageTimingSummary(
            stage_name=trace.stage_name.value,
            stage_status=trace.stage_status.value,
            started_at=trace.started_at,
            finished_at=trace.finished_at,
            duration_ms=_duration_ms(trace.started_at, trace.finished_at),
        )
        for trace in traces
    ]
    durations = [
        summary.duration_ms for summary in stage_summaries if summary.duration_ms is not None
    ]
    return QueryTraceTimingSummary(
        trace_count=len(traces),
        total_duration_ms=None if not durations else sum(durations),
        stages=stage_summaries,
    )


def _duration_ms(started_at: datetime, finished_at: datetime | None) -> int | None:
    if finished_at is None:
        return None
    delta = finished_at - started_at
    return max(int(delta.total_seconds() * 1000), 0)
