"""Repository seams for the staged query subsystem."""

from __future__ import annotations

from typing import Protocol

from .contracts import AnswerDraft, CitationBundle, QueryRun, QueryRunStatus
from .trace import QueryStageTrace


class QueryRunStore(Protocol):
    """Persistence interface for query run records."""

    def create_query_run(self, run: QueryRun) -> QueryRun:
        """Persist a newly created query run."""

    def update_query_run_status(
        self,
        query_id: str,
        status: QueryRunStatus,
    ) -> QueryRun:
        """Update the lifecycle status for an existing query run."""


class QueryTraceStore(Protocol):
    """Persistence interface for structured stage traces."""

    def append_stage_trace(self, trace: QueryStageTrace) -> None:
        """Persist a stage trace for a query run."""


class QueryAnswerStore(Protocol):
    """Persistence interface for final query answer artifacts."""

    def save_answer_artifacts(
        self,
        query_id: str,
        answer: AnswerDraft,
        citations: CitationBundle,
    ) -> None:
        """Persist final answer and citation artifacts for a query run."""
