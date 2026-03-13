from __future__ import annotations

import pytest

from doc_forge.evaluation import CriterionVerdict, TrustOutcome
from doc_forge.query import AnswerMode, SupportState

from e2e.eval_support import EvalCaseExecutor, SMOKE_CASE_IDS
from e2e.support import SystemDriver


pytestmark = pytest.mark.e2e


KNOWN_RUNTIME_GAP_CASES = (
    "lookup_rn1_001",
    "unsup_rn2_001",
    "uqt_rn2_007",
    "conflict_rn2_001",
    "istruct_rn3_006",
)


@pytest.mark.parametrize("case_id", SMOKE_CASE_IDS)
def test_authored_answer_layer_smoke_cases_execute_over_real_stack(e2e_stack, case_id: str) -> None:
    driver = SystemDriver(e2e_stack)
    executor = EvalCaseExecutor()

    executed = executor.execute_case(driver=driver, case_id=case_id)

    assert executed.query_id
    assert executed.workspace_id == f"ws-eval-{case_id}"
    assert executed.answer_text
    assert executed.summary_payload.query_id == executed.query_id
    assert executed.trace_payload.summary.query_id == executed.query_id
    assert executed.citations_payload.query_id == executed.query_id
    assert executed.query_response.response.support_state in {
        SupportState.SUFFICIENT,
        SupportState.PARTIAL,
        SupportState.INSUFFICIENT,
    }
    assert executed.query_response.response.answer_mode in {
        AnswerMode.DIRECT_ANSWER,
        AnswerMode.NARROWED_ANSWER,
        AnswerMode.QUALIFIED_ANSWER,
        AnswerMode.QUALIFIED_UNCERTAINTY,
        AnswerMode.SCOPED_ABSTENTION,
        AnswerMode.FULL_ABSTENTION,
    }

    assert executed.evaluation_result.case_id == case_id
    assert executed.evaluation_result.overall_trust_outcome in {
        TrustOutcome.TRUSTWORTHY,
        TrustOutcome.BORDERLINE,
        TrustOutcome.NOT_TRUSTWORTHY,
    }


@pytest.mark.parametrize("case_id", KNOWN_RUNTIME_GAP_CASES)
def test_authored_answer_layer_smoke_cases_produce_expected_current_profiles(
    e2e_stack, case_id: str
) -> None:
    driver = SystemDriver(e2e_stack)
    executor = EvalCaseExecutor()

    executed = executor.execute_case(driver=driver, case_id=case_id)
    result = executed.evaluation_result

    assert result.overall_trust_result.verdict is CriterionVerdict.FAIL
    assert result.overall_trust_outcome is TrustOutcome.NOT_TRUSTWORTHY
