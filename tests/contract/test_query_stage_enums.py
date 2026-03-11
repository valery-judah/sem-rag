from __future__ import annotations

import pytest

from parity.query import QueryStageName, QueryStageTraceStatus
from parity.query.stages import (
    ASSESS_SUPPORT_STAGE,
    CONTEXT_STAGE,
    DECIDE_ANSWER_MODE_STAGE,
    EVIDENCE_SETS_STAGE,
    GENERATE_STAGE,
    INTERPRET_STAGE,
    RENDER_CITATIONS_STAGE,
    RETRIEVE_STAGE,
    SELECT_STAGE,
)

pytestmark = pytest.mark.contract


def test_query_stage_enum_values_follow_runtime_backbone() -> None:
    assert [stage.value for stage in QueryStageName] == [
        "interpret",
        "retrieve",
        "select",
        "assemble_context",
        "assess_support",
        "decide_answer_mode",
        "generate",
        "render_citations",
    ]


def test_stage_placeholders_export_expected_stage_names() -> None:
    assert INTERPRET_STAGE is QueryStageName.INTERPRET
    assert RETRIEVE_STAGE is QueryStageName.RETRIEVE
    assert SELECT_STAGE is QueryStageName.SELECT
    assert EVIDENCE_SETS_STAGE is QueryStageName.SELECT
    assert CONTEXT_STAGE is QueryStageName.ASSEMBLE_CONTEXT
    assert ASSESS_SUPPORT_STAGE is QueryStageName.ASSESS_SUPPORT
    assert DECIDE_ANSWER_MODE_STAGE is QueryStageName.DECIDE_ANSWER_MODE
    assert GENERATE_STAGE is QueryStageName.GENERATE
    assert RENDER_CITATIONS_STAGE is QueryStageName.RENDER_CITATIONS


def test_stage_trace_status_values_remain_stable() -> None:
    assert [status.value for status in QueryStageTraceStatus] == [
        "pending",
        "succeeded",
        "failed",
        "skipped",
    ]
