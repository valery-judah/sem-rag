"""Repository seams and SQL stores for the staged query subsystem."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from .contracts import AnswerDraft, CitationBundle, CorpusSnapshot, QueryRun, QueryRunStatus
from .trace import QueryStageTrace

query_metadata = sa.MetaData()

query_runs_table = sa.Table(
    "query_runs",
    query_metadata,
    sa.Column("query_id", sa.Text(), primary_key=True),
    sa.Column("workspace_id", sa.Text(), nullable=False, index=True),
    sa.Column("question", sa.Text(), nullable=False),
    sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("status", sa.Text(), nullable=False),
    sa.Column("policy_snapshot_json", sa.JSON(), nullable=False),
)

query_snapshots_table = sa.Table(
    "query_snapshots",
    query_metadata,
    sa.Column(
        "query_id",
        sa.Text(),
        sa.ForeignKey("query_runs.query_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column("workspace_id", sa.Text(), nullable=False, index=True),
    sa.Column("query_started_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("eligible_doc_ids_json", sa.JSON(), nullable=False),
    sa.Column("retrieval_index_version", sa.Text(), nullable=True),
    sa.Column("readiness_version", sa.Text(), nullable=True),
)


class QueryRunStore(Protocol):
    """Persistence interface for query run records."""

    def get_query_run(self, query_id: str) -> QueryRun | None:
        """Load one persisted query run."""

    def create_query_run(self, run: QueryRun) -> QueryRun:
        """Persist a newly created query run."""

    def update_query_run_status(
        self,
        query_id: str,
        status: QueryRunStatus,
    ) -> QueryRun:
        """Update the lifecycle status for an existing query run."""


class QuerySnapshotStore(Protocol):
    """Persistence interface for captured corpus snapshots."""

    def save_snapshot(self, query_id: str, snapshot: CorpusSnapshot) -> None:
        """Persist the captured corpus snapshot for a query run."""

    def get_snapshot(self, query_id: str) -> CorpusSnapshot | None:
        """Load the captured corpus snapshot for a query run."""


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


class SqlQueryRunStore:
    """SQLAlchemy-backed repository for persisted query runs."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_query_run(self, query_id: str) -> QueryRun | None:
        stmt = sa.select(query_runs_table).where(query_runs_table.c.query_id == query_id)
        with self._engine.begin() as conn:
            row = conn.execute(stmt).mappings().first()
        if row is None:
            return None
        return _row_to_query_run(dict(row))

    def create_query_run(self, run: QueryRun) -> QueryRun:
        with self._engine.begin() as conn:
            conn.execute(sa.insert(query_runs_table), [_query_run_to_row(run)])
        return run

    def update_query_run_status(
        self,
        query_id: str,
        status: QueryRunStatus,
    ) -> QueryRun:
        stmt = (
            sa.update(query_runs_table)
            .where(query_runs_table.c.query_id == query_id)
            .values(status=status.value)
        )
        with self._engine.begin() as conn:
            result = conn.execute(stmt)
        if result.rowcount != 1:
            raise LookupError(f"query run {query_id!r} was not found")
        updated = self.get_query_run(query_id)
        if updated is None:
            raise LookupError(f"query run {query_id!r} was not found after update")
        return updated


class SqlQuerySnapshotStore:
    """SQLAlchemy-backed repository for captured corpus snapshots."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_snapshot(self, query_id: str, snapshot: CorpusSnapshot) -> None:
        row = _snapshot_to_row(query_id, snapshot)
        with self._engine.begin() as conn:
            conn.execute(
                sa.delete(query_snapshots_table).where(query_snapshots_table.c.query_id == query_id)
            )
            conn.execute(sa.insert(query_snapshots_table), [row])

    def get_snapshot(self, query_id: str) -> CorpusSnapshot | None:
        stmt = sa.select(query_snapshots_table).where(query_snapshots_table.c.query_id == query_id)
        with self._engine.begin() as conn:
            row = conn.execute(stmt).mappings().first()
        if row is None:
            return None
        return _row_to_snapshot(dict(row))


def _query_run_to_row(run: QueryRun) -> dict[str, object]:
    payload = run.model_dump(mode="python")
    payload["status"] = run.status.value
    payload["policy_snapshot_json"] = payload.pop("policy_snapshot")
    return payload


def _row_to_query_run(row: Mapping[str, object]) -> QueryRun:
    payload = dict(row)
    payload["policy_snapshot"] = payload.pop("policy_snapshot_json")
    payload["submitted_at"] = _coerce_datetime(payload["submitted_at"])
    return QueryRun.model_validate(payload)


def _snapshot_to_row(query_id: str, snapshot: CorpusSnapshot) -> dict[str, object]:
    payload = snapshot.model_dump(mode="python")
    payload["query_id"] = query_id
    payload["eligible_doc_ids_json"] = payload.pop("eligible_doc_ids")
    return payload


def _row_to_snapshot(row: Mapping[str, object]) -> CorpusSnapshot:
    payload = dict(row)
    del payload["query_id"]
    payload["eligible_doc_ids"] = payload.pop("eligible_doc_ids_json")
    payload["query_started_at"] = _coerce_datetime(payload["query_started_at"])
    return CorpusSnapshot.model_validate(payload)


def _coerce_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    raise TypeError(f"expected datetime, got {type(value).__name__}")
