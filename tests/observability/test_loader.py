from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import sqlalchemy as sa

from doc_forge.evaluation.answer_layer import (
    AnswerLayerCriterionResult,
    AnswerLayerRunResult,
    CriterionName,
    CriterionVerdict,
    TrustOutcome,
)
from doc_forge.observability.loader import EvalOpsLoader
from doc_forge.observability.persistence import (
    eval_case_results_table,
    log_sources_table,
    query_context_assets_table,
    query_context_runs_table,
)
from doc_forge.query import (
    QueryContextAssetPaths,
    QueryContextLogAsset,
    QueryContextManifest,
    QueryContextSourceKind,
)


def test_loader_indexes_query_bundle_and_eval_result(tmp_path: Path) -> None:
    context_root = tmp_path / "data" / "context" / "queries"
    bundle_root = context_root / "qry-1"
    bundle_root.mkdir(parents=True)
    _write_manifest(
        bundle_root=bundle_root,
        manifest=QueryContextManifest(
            query_id="qry-1",
            workspace_id="ws-1",
            question="What is the answer?",
            submitted_at=datetime(2026, 3, 13, 10, 0, tzinfo=UTC),
            completed_at=datetime(2026, 3, 13, 10, 1, tzinfo=UTC),
            collected_at=datetime(2026, 3, 13, 10, 2, tzinfo=UTC),
            environment="prod",
            source_kind=QueryContextSourceKind.EVAL,
            case_id="case-1",
            test_id="e2e::test_case_1",
            run_id="run-1",
            support_state="sufficient",
            answer_mode="direct_answer",
            evaluator_outcome="trustworthy",
            assets=QueryContextAssetPaths(
                summary="summary.json",
                citations="citations.json",
                trace="trace.json",
                replay="replay.json",
                query_response="query-response.json",
                eval_result="eval-result.json",
                execution_metadata="execution-metadata.json",
                query_events="logs/query-events.jsonl",
            ),
            log_assets=[
                QueryContextLogAsset(
                    service="api",
                    source_path="/repo/data/logs/e2e/runs/run-1/test-1/api.jsonl",
                    bundle_path="logs/api.jsonl",
                    matched_line_count=12,
                ),
                QueryContextLogAsset(
                    service="worker",
                    source_path="/repo/data/logs/e2e/runs/run-1/test-1/worker.jsonl",
                    bundle_path="logs/worker.jsonl",
                    matched_line_count=0,
                ),
            ],
        ),
    )
    _write_eval_result(bundle_root / "eval-result.json", case_id="case-1")

    database_url = f"sqlite+pysqlite:///{tmp_path / 'observability.db'}"
    loader = EvalOpsLoader.from_database_url(
        database_url=database_url,
        context_root=context_root,
        repo_root=tmp_path,
    )

    stats = loader.scan_once()

    assert stats.scanned_bundles == 1
    assert stats.indexed_bundles == 1

    engine = sa.create_engine(database_url)
    with engine.connect() as connection:
        run_row = connection.execute(sa.select(query_context_runs_table)).mappings().one()
        assert run_row["query_id"] == "qry-1"
        assert run_row["bundle_root"] == "data/context/queries/qry-1"
        assert run_row["case_id"] == "case-1"
        assert run_row["source_kind"] == "eval"

        asset_rows = (
            connection.execute(
                sa.select(query_context_assets_table).order_by(
                    query_context_assets_table.c.asset_kind
                )
            )
            .mappings()
            .all()
        )
        asset_kinds = {row["asset_kind"] for row in asset_rows}
        assert "query_response" in asset_kinds
        assert "eval_result" in asset_kinds
        assert "api_log" in asset_kinds
        assert "worker_log" in asset_kinds

        eval_row = connection.execute(sa.select(eval_case_results_table)).mappings().one()
        assert eval_row["case_id"] == "case-1"
        assert eval_row["trust_outcome"] == "trustworthy"
        assert eval_row["support_alignment_verdict"] == "pass"

        log_rows = connection.execute(sa.select(log_sources_table)).mappings().all()
        assert len(log_rows) == 2
        assert {row["service"] for row in log_rows} == {"api", "worker"}
    engine.dispose()


def test_loader_indexes_missing_assets_without_eval_result(tmp_path: Path) -> None:
    context_root = tmp_path / "context"
    bundle_root = context_root / "qry-2"
    bundle_root.mkdir(parents=True)
    _write_manifest(
        bundle_root=bundle_root,
        manifest=QueryContextManifest(
            query_id="qry-2",
            workspace_id="ws-2",
            question="Need more evidence?",
            submitted_at=datetime(2026, 3, 13, 11, 0, tzinfo=UTC),
            completed_at=datetime(2026, 3, 13, 11, 1, tzinfo=UTC),
            collected_at=datetime(2026, 3, 13, 11, 2, tzinfo=UTC),
            environment="prod",
            source_kind=QueryContextSourceKind.E2E,
            run_id="run-2",
            test_id="e2e::test_case_2",
            support_state="insufficient",
            answer_mode="full_abstention",
            assets=QueryContextAssetPaths(
                summary="summary.json",
                citations="citations.json",
                trace="trace.json",
                replay="replay.json",
                query_events="logs/query-events.jsonl",
            ),
            missing_assets=["query_response", "eval_result", "execution_metadata"],
            log_assets=[
                QueryContextLogAsset(
                    service="api",
                    source_path="/repo/data/logs/compose/runs/run-2/api.jsonl",
                    bundle_path="logs/api.jsonl",
                    matched_line_count=5,
                )
            ],
        ),
    )

    database_url = f"sqlite+pysqlite:///{tmp_path / 'observability.db'}"
    loader = EvalOpsLoader.from_database_url(
        database_url=database_url,
        context_root=context_root,
        repo_root=tmp_path,
    )
    loader.scan_once()

    engine = sa.create_engine(database_url)
    with engine.connect() as connection:
        missing_row = (
            connection.execute(
                sa.select(query_context_assets_table).where(
                    query_context_assets_table.c.asset_kind == "query_response"
                )
            )
            .mappings()
            .one()
        )
        assert missing_row["present"] is False
        assert missing_row["missing_reason"] == "manifest_missing"

        eval_rows = connection.execute(sa.select(eval_case_results_table)).mappings().all()
        assert eval_rows == []
    engine.dispose()


def _write_manifest(*, bundle_root: Path, manifest: QueryContextManifest) -> None:
    (bundle_root / "manifest.json").write_text(
        manifest.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )


def _write_eval_result(path: Path, *, case_id: str) -> None:
    result = AnswerLayerRunResult(
        case_id=case_id,
        support_alignment=AnswerLayerCriterionResult(
            criterion=CriterionName.SUPPORT_ALIGNMENT,
            verdict=CriterionVerdict.PASS,
            rationale="supported",
        ),
        scope_control=AnswerLayerCriterionResult(
            criterion=CriterionName.SCOPE_CONTROL,
            verdict=CriterionVerdict.PASS,
            rationale="scoped",
        ),
        provenance_quality=AnswerLayerCriterionResult(
            criterion=CriterionName.PROVENANCE_QUALITY,
            verdict=CriterionVerdict.PASS,
            rationale="provenance present",
        ),
        abstention_behavior=AnswerLayerCriterionResult(
            criterion=CriterionName.ABSTENTION_BEHAVIOR,
            verdict=CriterionVerdict.PASS,
            rationale="correct",
        ),
        overall_trust_result=AnswerLayerCriterionResult(
            criterion=CriterionName.OVERALL_TRUST_OUTCOME,
            verdict=CriterionVerdict.PASS,
            rationale="trustworthy",
        ),
        overall_trust_outcome=TrustOutcome.TRUSTWORTHY,
        derived_trust_outcome=True,
    )
    path.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
