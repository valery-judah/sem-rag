from __future__ import annotations

import pytest

from doc_forge._contracts import AnswerStatus
from doc_forge.evaluation.dataset import BASELINE_EVALUATION_CASES
from doc_forge.evaluation.fixtures import build_insufficient_evidence_corpus_question_seam
from doc_forge.evaluation.models import EvaluationCase, EvaluationOutput
from doc_forge.evaluation.runner import evaluate_case, evaluate_cases
from doc_forge.evaluation.systems import DeterministicSeamSystem
from tests.support.contract_seam import build_supported_corpus_question_seam


def test_supported_cases_require_explicit_support_ids() -> None:
    with pytest.raises(
        ValueError, match="supported cases must declare expected supporting doc and chunk ids"
    ):
        EvaluationCase(
            case_id="missing-support",
            scenario_name="missing support ids",
            question="What supports this answer?",
            expected_status=AnswerStatus.SUPPORTED,
        )


def test_insufficient_cases_require_explicit_empty_support_ids() -> None:
    with pytest.raises(
        ValueError,
        match="insufficient_evidence cases must use explicit empty supporting doc and chunk ids",
    ):
        EvaluationCase(
            case_id="bad-insufficient",
            scenario_name="bad insufficient case",
            question="What is unsupported?",
            expected_status=AnswerStatus.INSUFFICIENT_EVIDENCE,
            expected_supporting_doc_ids=("doc-1",),
            expected_supporting_chunk_ids=("chunk-1",),
        )


def test_runner_records_clear_failures() -> None:
    eval_case = _case_by_id("supported-cross-document")

    def system(case: EvaluationCase) -> EvaluationOutput:
        seam = build_insufficient_evidence_corpus_question_seam()
        return EvaluationOutput(retrieval_hits=seam.retrieval_hits, answer=seam.answer)

    result = evaluate_case(eval_case, system)

    assert not result.passed
    assert any(
        failure
        == "[supported-cross-document] expected answer status supported, got insufficient_evidence"
        for failure in result.failures
    )
    assert any("retrieved doc ids" in failure for failure in result.failures)
    assert any("supporting chunk ids" in failure for failure in result.failures)


def test_runner_reports_ordering_mismatch_with_case_id() -> None:
    eval_case = _case_by_id("supported-cross-document")

    def system(case: EvaluationCase) -> EvaluationOutput:
        seam = build_supported_corpus_question_seam()
        return EvaluationOutput(
            retrieval_hits=list(reversed(seam.retrieval_hits)),
            answer=seam.answer,
        )

    result = evaluate_case(eval_case, system)

    assert not result.passed
    assert any(
        failure
        == (
            "[supported-cross-document] expected retrieved doc ids ('doc-1', 'doc-2'), "
            "got ('doc-2', 'doc-1')"
        )
        for failure in result.failures
    )
    assert any(
        failure
        == (
            "[supported-cross-document] expected retrieved chunk ids ('chunk-1', 'chunk-2'), "
            "got ('chunk-2', 'chunk-1')"
        )
        for failure in result.failures
    )


def test_runner_reports_provenance_mismatch_with_case_id() -> None:
    eval_case = _case_by_id("provenance-completeness")

    def system(case: EvaluationCase) -> EvaluationOutput:
        seam = build_supported_corpus_question_seam()
        broken_reference = seam.answer.source_references[0].model_copy(
            update={"page_label": None, "passage_anchor": None}
        )
        answer = seam.answer.model_copy(
            update={
                "source_references": [broken_reference, seam.answer.source_references[1]],
            }
        )
        return EvaluationOutput(retrieval_hits=seam.retrieval_hits, answer=answer)

    result = evaluate_case(eval_case, system)

    assert not result.passed
    assert any(
        failure == "[provenance-completeness] source reference 1 is missing passage_anchor"
        for failure in result.failures
    )
    assert any(
        failure
        == ("[provenance-completeness] expected page labels {'p. 14'} for doc_id doc-1, got {None}")
        for failure in result.failures
    )


def test_baseline_cases_pass_against_deterministic_seam_system() -> None:
    results = evaluate_cases(BASELINE_EVALUATION_CASES, DeterministicSeamSystem())

    failures = [failure for result in results for failure in result.failures]

    assert len(results) == 3
    assert all(result.passed for result in results), failures


def _case_by_id(case_id: str) -> EvaluationCase:
    for case in BASELINE_EVALUATION_CASES:
        if case.case_id == case_id:
            return case
    raise AssertionError(f"unknown test case id: {case_id}")
