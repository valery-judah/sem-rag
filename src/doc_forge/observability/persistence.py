"""Persistence helpers for the central eval/log observability store."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.engine import Engine

metadata = sa.MetaData()

query_context_runs_table = sa.Table(
    "query_context_runs",
    metadata,
    sa.Column("query_id", sa.Text(), primary_key=True),
    sa.Column("workspace_id", sa.Text(), nullable=True, index=True),
    sa.Column("question", sa.Text(), nullable=True),
    sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, index=True),
    sa.Column("source_kind", sa.Text(), nullable=False, index=True),
    sa.Column("run_id", sa.Text(), nullable=True, index=True),
    sa.Column("test_id", sa.Text(), nullable=True, index=True),
    sa.Column("case_id", sa.Text(), nullable=True, index=True),
    sa.Column("support_state", sa.Text(), nullable=True),
    sa.Column("answer_mode", sa.Text(), nullable=True),
    sa.Column("evaluator_outcome", sa.Text(), nullable=True, index=True),
    sa.Column("bundle_root", sa.Text(), nullable=False),
    sa.Column("environment", sa.Text(), nullable=True),
)

query_context_assets_table = sa.Table(
    "query_context_assets",
    metadata,
    sa.Column("query_id", sa.Text(), nullable=False),
    sa.Column("asset_kind", sa.Text(), nullable=False),
    sa.Column("relative_path", sa.Text(), nullable=True),
    sa.Column("present", sa.Boolean(), nullable=False),
    sa.Column("missing_reason", sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(["query_id"], ["query_context_runs.query_id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("query_id", "asset_kind"),
)

eval_case_results_table = sa.Table(
    "eval_case_results",
    metadata,
    sa.Column("query_id", sa.Text(), nullable=False),
    sa.Column("case_id", sa.Text(), nullable=False),
    sa.Column("workspace_id", sa.Text(), nullable=True, index=True),
    sa.Column("run_id", sa.Text(), nullable=True, index=True),
    sa.Column("test_id", sa.Text(), nullable=True, index=True),
    sa.Column("trust_outcome", sa.Text(), nullable=False, index=True),
    sa.Column("support_alignment_verdict", sa.Text(), nullable=True),
    sa.Column("scope_control_verdict", sa.Text(), nullable=True),
    sa.Column("provenance_quality_verdict", sa.Text(), nullable=True),
    sa.Column("abstention_behavior_verdict", sa.Text(), nullable=True),
    sa.Column("overall_trust_verdict", sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(["query_id"], ["query_context_runs.query_id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("query_id", "case_id"),
)

log_sources_table = sa.Table(
    "log_sources",
    metadata,
    sa.Column("query_id", sa.Text(), nullable=False),
    sa.Column("service", sa.Text(), nullable=False, index=True),
    sa.Column("source_path", sa.Text(), nullable=False),
    sa.Column("matched_line_count", sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(["query_id"], ["query_context_runs.query_id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("query_id", "service", "source_path"),
)


@dataclass(frozen=True)
class QueryContextRunRecord:
    query_id: str
    workspace_id: str | None
    question: str | None
    submitted_at: datetime | None
    completed_at: datetime | None
    collected_at: datetime
    source_kind: str
    run_id: str | None
    test_id: str | None
    case_id: str | None
    support_state: str | None
    answer_mode: str | None
    evaluator_outcome: str | None
    bundle_root: str
    environment: str | None


@dataclass(frozen=True)
class QueryContextAssetRecord:
    query_id: str
    asset_kind: str
    relative_path: str | None
    present: bool
    missing_reason: str | None


@dataclass(frozen=True)
class EvalCaseResultRecord:
    query_id: str
    case_id: str
    workspace_id: str | None
    run_id: str | None
    test_id: str | None
    trust_outcome: str
    support_alignment_verdict: str | None
    scope_control_verdict: str | None
    provenance_quality_verdict: str | None
    abstention_behavior_verdict: str | None
    overall_trust_verdict: str | None


@dataclass(frozen=True)
class LogSourceRecord:
    query_id: str
    service: str
    source_path: str
    matched_line_count: int


class ObservabilityStore:
    """Small relational store for query/eval metadata and log source indexes."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_schema(self) -> None:
        metadata.create_all(self._engine)

    def replace_query_context(
        self,
        *,
        run_record: QueryContextRunRecord,
        asset_records: list[QueryContextAssetRecord],
        log_records: list[LogSourceRecord],
        eval_record: EvalCaseResultRecord | None,
    ) -> None:
        self.create_schema()
        with self._engine.begin() as connection:
            connection.execute(
                sa.delete(eval_case_results_table).where(
                    eval_case_results_table.c.query_id == run_record.query_id
                )
            )
            connection.execute(
                sa.delete(log_sources_table).where(
                    log_sources_table.c.query_id == run_record.query_id
                )
            )
            connection.execute(
                sa.delete(query_context_assets_table).where(
                    query_context_assets_table.c.query_id == run_record.query_id
                )
            )
            connection.execute(
                sa.delete(query_context_runs_table).where(
                    query_context_runs_table.c.query_id == run_record.query_id
                )
            )
            connection.execute(
                query_context_runs_table.insert().values(_run_record_payload(run_record))
            )
            if asset_records:
                connection.execute(
                    query_context_assets_table.insert(),
                    [_asset_record_payload(record) for record in asset_records],
                )
            if log_records:
                connection.execute(
                    log_sources_table.insert(),
                    [_log_record_payload(record) for record in log_records],
                )
            if eval_record is not None:
                connection.execute(
                    eval_case_results_table.insert().values(_eval_record_payload(eval_record))
                )

    def count_rows(self, table_name: str) -> int:
        table = {
            "query_context_runs": query_context_runs_table,
            "query_context_assets": query_context_assets_table,
            "eval_case_results": eval_case_results_table,
            "log_sources": log_sources_table,
        }[table_name]
        with self._engine.connect() as connection:
            count = connection.scalar(sa.select(sa.func.count()).select_from(table))
        return int(count or 0)


def _run_record_payload(record: QueryContextRunRecord) -> dict[str, object]:
    return {
        "query_id": record.query_id,
        "workspace_id": record.workspace_id,
        "question": record.question,
        "submitted_at": record.submitted_at,
        "completed_at": record.completed_at,
        "collected_at": record.collected_at,
        "source_kind": record.source_kind,
        "run_id": record.run_id,
        "test_id": record.test_id,
        "case_id": record.case_id,
        "support_state": record.support_state,
        "answer_mode": record.answer_mode,
        "evaluator_outcome": record.evaluator_outcome,
        "bundle_root": record.bundle_root,
        "environment": record.environment,
    }


def _asset_record_payload(record: QueryContextAssetRecord) -> dict[str, object]:
    return {
        "query_id": record.query_id,
        "asset_kind": record.asset_kind,
        "relative_path": record.relative_path,
        "present": record.present,
        "missing_reason": record.missing_reason,
    }


def _eval_record_payload(record: EvalCaseResultRecord) -> dict[str, object]:
    return {
        "query_id": record.query_id,
        "case_id": record.case_id,
        "workspace_id": record.workspace_id,
        "run_id": record.run_id,
        "test_id": record.test_id,
        "trust_outcome": record.trust_outcome,
        "support_alignment_verdict": record.support_alignment_verdict,
        "scope_control_verdict": record.scope_control_verdict,
        "provenance_quality_verdict": record.provenance_quality_verdict,
        "abstention_behavior_verdict": record.abstention_behavior_verdict,
        "overall_trust_verdict": record.overall_trust_verdict,
    }


def _log_record_payload(record: LogSourceRecord) -> dict[str, object]:
    return {
        "query_id": record.query_id,
        "service": record.service,
        "source_path": record.source_path,
        "matched_line_count": record.matched_line_count,
    }
