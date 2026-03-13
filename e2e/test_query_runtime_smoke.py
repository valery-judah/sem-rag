from __future__ import annotations

import pytest

from doc_forge.query import AnswerMode, SupportState

from e2e.query_support import execute_query_run
from e2e.support import SystemDriver


pytestmark = pytest.mark.e2e


def test_query_runtime_returns_answer_and_review_artifacts_for_ready_markdown(e2e_stack) -> None:
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
