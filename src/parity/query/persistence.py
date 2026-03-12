"""Repository seams and SQL stores for the staged query subsystem."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol, cast

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from .contracts import (
    AnswerDraft,
    AnswerMode,
    CitationBundle,
    CorpusSnapshot,
    FinalQueryArtifacts,
    QueryRun,
    QueryRunStatus,
    QueryTerminalFailure,
    SupportQualifierReason,
    SupportState,
    TrustFailureLabel,
)
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
    sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("terminal_failure_json", sa.JSON(), nullable=True),
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

query_stage_traces_table = sa.Table(
    "query_stage_traces",
    query_metadata,
    sa.Column("trace_id", sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column(
        "query_id",
        sa.Text(),
        sa.ForeignKey("query_runs.query_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column("stage_name", sa.Text(), nullable=False),
    sa.Column("stage_status", sa.Text(), nullable=False),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("payload_json", sa.JSON(), nullable=False),
)

query_answers_table = sa.Table(
    "query_answers",
    query_metadata,
    sa.Column(
        "query_id",
        sa.Text(),
        sa.ForeignKey("query_runs.query_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column("answer_text", sa.Text(), nullable=False),
    sa.Column("visible_limitations_json", sa.JSON(), nullable=False),
    sa.Column("should_render_citations", sa.Boolean(), nullable=False),
    sa.Column("grounded_evidence_set_ids_json", sa.JSON(), nullable=False),
    sa.Column("support_state", sa.Text(), nullable=False),
    sa.Column("qualifying_reason_codes_json", sa.JSON(), nullable=False),
    sa.Column("answer_mode", sa.Text(), nullable=False),
    sa.Column("citations_json", sa.JSON(), nullable=False),
    sa.Column("trust_failure_labels_json", sa.JSON(), nullable=False),
    sa.Column("generator_version", sa.Text(), nullable=False),
    sa.Column("renderer_version", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
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
        *,
        completed_at: datetime | None = None,
        terminal_failure: QueryTerminalFailure | None = None,
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

    def list_stage_traces(self, query_id: str) -> list[QueryStageTrace]:
        """Load stage traces for a query run in execution order."""


class QueryAnswerStore(Protocol):
    """Persistence interface for final query answer artifacts."""

    def save_answer_artifacts(
        self,
        query_id: str,
        artifacts: FinalQueryArtifacts,
    ) -> None:
        """Persist final answer and citation artifacts for a query run."""

    def get_answer_artifacts(self, query_id: str) -> FinalQueryArtifacts | None:
        """Load persisted final answer artifacts for a query run."""


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
        *,
        completed_at: datetime | None = None,
        terminal_failure: QueryTerminalFailure | None = None,
    ) -> QueryRun:
        values: dict[str, object | None] = {
            "status": status.value,
            "completed_at": completed_at,
            "terminal_failure_json": (
                None if terminal_failure is None else terminal_failure.model_dump(mode="json")
            ),
        }
        stmt = (
            sa.update(query_runs_table)
            .where(query_runs_table.c.query_id == query_id)
            .values(values)
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


class SqlQueryTraceStore:
    """SQLAlchemy-backed repository for structured query stage traces."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def append_stage_trace(self, trace: QueryStageTrace) -> None:
        with self._engine.begin() as conn:
            conn.execute(sa.insert(query_stage_traces_table), [_stage_trace_to_row(trace)])

    def list_stage_traces(self, query_id: str) -> list[QueryStageTrace]:
        stmt = (
            sa.select(query_stage_traces_table)
            .where(query_stage_traces_table.c.query_id == query_id)
            .order_by(
                query_stage_traces_table.c.started_at.asc(),
                query_stage_traces_table.c.trace_id.asc(),
            )
        )
        with self._engine.begin() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [_row_to_stage_trace(dict(row)) for row in rows]


class SqlQueryAnswerStore:
    """SQLAlchemy-backed repository for final answer artifacts."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_answer_artifacts(
        self,
        query_id: str,
        artifacts: FinalQueryArtifacts,
    ) -> None:
        row = _answer_artifacts_to_row(query_id, artifacts)
        with self._engine.begin() as conn:
            conn.execute(
                sa.delete(query_answers_table).where(query_answers_table.c.query_id == query_id)
            )
            conn.execute(sa.insert(query_answers_table), [row])

    def get_answer_artifacts(self, query_id: str) -> FinalQueryArtifacts | None:
        stmt = sa.select(query_answers_table).where(query_answers_table.c.query_id == query_id)
        with self._engine.begin() as conn:
            row = conn.execute(stmt).mappings().first()
        if row is None:
            return None
        return _row_to_answer_artifacts(dict(row))


def _query_run_to_row(run: QueryRun) -> dict[str, object]:
    payload = run.model_dump(mode="python")
    payload["status"] = run.status.value
    payload["policy_snapshot_json"] = payload.pop("policy_snapshot")
    payload["terminal_failure_json"] = (
        None if run.terminal_failure is None else run.terminal_failure.model_dump(mode="json")
    )
    del payload["terminal_failure"]
    return payload


def _row_to_query_run(row: Mapping[str, object]) -> QueryRun:
    payload = dict(row)
    payload["policy_snapshot"] = payload.pop("policy_snapshot_json")
    payload["submitted_at"] = _coerce_datetime(payload["submitted_at"])
    if payload["completed_at"] is not None:
        payload["completed_at"] = _coerce_datetime(payload["completed_at"])
    payload["terminal_failure"] = payload.pop("terminal_failure_json")
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


def _stage_trace_to_row(trace: QueryStageTrace) -> dict[str, object]:
    payload = trace.model_dump(mode="python")
    payload["stage_name"] = trace.stage_name.value
    payload["stage_status"] = trace.stage_status.value
    payload["payload_json"] = payload.pop("payload")
    return payload


def _row_to_stage_trace(row: Mapping[str, object]) -> QueryStageTrace:
    payload = dict(row)
    del payload["trace_id"]
    payload["payload"] = payload.pop("payload_json")
    payload["started_at"] = _coerce_datetime(payload["started_at"])
    if payload["finished_at"] is not None:
        payload["finished_at"] = _coerce_datetime(payload["finished_at"])
    return QueryStageTrace.model_validate(payload)


def _answer_artifacts_to_row(
    query_id: str,
    artifacts: FinalQueryArtifacts,
) -> dict[str, object]:
    return {
        "query_id": query_id,
        "answer_text": artifacts.answer.answer_text,
        "visible_limitations_json": artifacts.answer.visible_limitations,
        "should_render_citations": artifacts.answer.should_render_citations,
        "grounded_evidence_set_ids_json": artifacts.answer.grounded_evidence_set_ids,
        "support_state": artifacts.support_state.value,
        "qualifying_reason_codes_json": [
            reason.value for reason in artifacts.qualifying_reason_codes
        ],
        "answer_mode": artifacts.answer_mode.value,
        "citations_json": artifacts.citations.model_dump(mode="json"),
        "trust_failure_labels_json": [label.value for label in artifacts.trust_failure_labels],
        "generator_version": artifacts.answer.generator_version,
        "renderer_version": artifacts.citations.renderer_version,
        "created_at": artifacts.created_at,
    }


def _row_to_answer_artifacts(row: Mapping[str, object]) -> FinalQueryArtifacts:
    payload = dict(row)
    visible_limitations = cast(list[str], payload["visible_limitations_json"])
    grounded_evidence_set_ids = cast(list[str], payload["grounded_evidence_set_ids_json"])
    qualifying_reason_codes = cast(list[str], payload["qualifying_reason_codes_json"])
    trust_failure_labels = cast(list[str], payload["trust_failure_labels_json"])
    answer = AnswerDraft(
        answer_text=str(payload["answer_text"]),
        visible_limitations=visible_limitations,
        should_render_citations=bool(payload["should_render_citations"]),
        grounded_evidence_set_ids=grounded_evidence_set_ids,
        generator_version=str(payload["generator_version"]),
    )
    citations = CitationBundle.model_validate(payload["citations_json"])
    return FinalQueryArtifacts(
        answer=answer,
        citations=citations,
        support_state=SupportState(str(payload["support_state"])),
        qualifying_reason_codes=[
            SupportQualifierReason(str(reason)) for reason in qualifying_reason_codes
        ],
        answer_mode=AnswerMode(str(payload["answer_mode"])),
        trust_failure_labels=[TrustFailureLabel(str(label)) for label in trust_failure_labels],
        created_at=_coerce_datetime(payload["created_at"]),
    )


def _coerce_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    raise TypeError(f"expected datetime, got {type(value).__name__}")
