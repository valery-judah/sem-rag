from __future__ import annotations

import json

import pytest

from doc_forge.query import AnswerMode, QueryContextCollector, SupportState
from e2e.query_support import execute_query_run
from e2e.support import SystemDriver

pytestmark = pytest.mark.e2e


def test_query_runtime_returns_answer_and_review_artifacts_for_ready_markdown(
    e2e_stack,
    request: pytest.FixtureRequest,
) -> None:
    driver = SystemDriver(e2e_stack)
    workspace_id = "ws-query-runtime-supported"
    uploaded = driver.ingest_document(
        path="evals/corpus/research-notes-1.md",
        title="Research Notes 1",
        workspace_id=workspace_id,
    )

    executed = execute_query_run(
        driver=driver,
        workspace_id=workspace_id,
        question="What citation format is preferred for Markdown sources?",
    )

    assert executed.response.query_id
    assert executed.response.answer.answer_text
    assert executed.response.support_state is SupportState.SUFFICIENT
    assert executed.response.answer_mode is not AnswerMode.FULL_ABSTENTION
    assert executed.response.citations.citations
    assert uploaded.doc_id in executed.response.citations.material_doc_ids

    assert executed.summary.query_id == executed.query_id
    assert executed.summary.workspace_id == workspace_id
    assert executed.summary.has_answer is True
    assert executed.summary.support_state is SupportState.SUFFICIENT
    assert executed.summary.answer_mode == executed.response.answer_mode

    assert executed.trace.summary.query_id == executed.query_id
    assert executed.trace.final_artifacts is not None
    assert executed.trace.final_artifacts.answer.answer_text == executed.response.answer.answer_text

    assert executed.citations_review.query_id == executed.query_id
    assert executed.citations_review.citations.material_doc_ids == [uploaded.doc_id]

    archived_logs = e2e_stack.archive_scenario_logs(test_id=request.node.nodeid)
    assert set(archived_logs) == {"api", "worker"}

    api_lines = archived_logs["api"].read_text(encoding="utf-8").splitlines()
    assert api_lines
    parsed_api_logs = [json.loads(line) for line in api_lines]
    assert any(log["event"] == "http.request.started" for log in parsed_api_logs)
    assert any(log["event"] == "query.run.completed" for log in parsed_api_logs)

    latest_api_log = (
        e2e_stack.log_root
        / "e2e"
        / "latest"
        / (
            "e2e_test_query_runtime_smoke.py_"
            "test_query_runtime_returns_answer_and_review_artifacts_for_ready_markdown"
        )
        / "api.jsonl"
    )
    assert latest_api_log.is_symlink()
    assert latest_api_log.resolve() == archived_logs["api"].resolve()

    collector = QueryContextCollector.from_database_url(database_url=e2e_stack.database_url)
    collected = collector.collect(executed.query_id)
    manifest = collected.manifest
    e2e_stack.record_query_context_artifact(
        collected.bundle_root.relative_to(e2e_stack.log_root.parents[1]).as_posix()
    )

    assert collected.manifest_path.exists()
    assert manifest.query_id == executed.query_id
    assert manifest.assets.summary == "summary.json"
    assert manifest.assets.trace == "trace.json"
    assert manifest.assets.citations == "citations.json"
    assert manifest.assets.replay == "replay.json"
    assert manifest.assets.query_events == "logs/query-events.jsonl"
    assert any(asset.service == "api" for asset in manifest.log_assets)
    assert any(asset.service == "worker" for asset in manifest.log_assets)
    assert (collected.bundle_root / "logs" / "api.jsonl").is_symlink()
    assert (collected.bundle_root / "logs" / "worker.jsonl").is_symlink()


def test_query_runtime_empty_workspace_returns_insufficient_support(e2e_stack) -> None:
    driver = SystemDriver(e2e_stack)
    workspace_id = "ws-query-runtime-empty"

    executed = execute_query_run(
        driver=driver,
        workspace_id=workspace_id,
        question="What citation format is preferred for Markdown sources?",
    )

    assert executed.response.support_state is SupportState.INSUFFICIENT
    assert executed.response.answer_mode is AnswerMode.FULL_ABSTENTION
    assert executed.response.answer.answer_text
    assert executed.response.citations.citations == []

    assert executed.summary.query_id == executed.query_id
    assert executed.summary.workspace_id == workspace_id
    assert executed.summary.has_answer is True
    assert executed.summary.support_state is SupportState.INSUFFICIENT

    assert executed.citations_review.query_id == executed.query_id
    assert executed.citations_review.citations.citations == []
