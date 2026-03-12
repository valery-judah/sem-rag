"""Deterministic pytest-first evaluation runner."""

from __future__ import annotations

from doc_forge._contracts import SourceReference

from .models import CaseResult, EvaluationCase, SystemUnderTest


def evaluate_case(case: EvaluationCase, system: SystemUnderTest) -> CaseResult:
    """Evaluate one deterministic case against the provided system."""

    output = system(case)
    actual_retrieved_doc_ids = tuple(hit.doc_id for hit in output.retrieval_hits)
    actual_retrieved_chunk_ids = tuple(hit.chunk_id for hit in output.retrieval_hits)
    actual_supporting_doc_ids = tuple(
        reference.doc_id for reference in output.answer.source_references
    )
    actual_supporting_chunk_ids = tuple(
        reference.chunk_id for reference in output.answer.source_references
    )

    failures: list[str] = []
    if output.answer.status is not case.expected_status:
        failures.append(
            _failure(
                case.case_id,
                "expected answer status "
                f"{case.expected_status.value}, got {output.answer.status.value}",
            )
        )

    if case.expected_retrieved_doc_ids is not None:
        _expect_equal(
            failures,
            case.case_id,
            "retrieved doc ids",
            case.expected_retrieved_doc_ids,
            actual_retrieved_doc_ids,
        )
        _expect_equal(
            failures,
            case.case_id,
            "retrieved chunk ids",
            case.expected_retrieved_chunk_ids,
            actual_retrieved_chunk_ids,
        )

    _expect_equal(
        failures,
        case.case_id,
        "supporting doc ids",
        case.expected_supporting_doc_ids,
        actual_supporting_doc_ids,
    )
    _expect_equal(
        failures,
        case.case_id,
        "supporting chunk ids",
        case.expected_supporting_chunk_ids,
        actual_supporting_chunk_ids,
    )

    _check_provenance(case, output.answer.source_references, failures)

    return CaseResult(
        case_id=case.case_id,
        passed=not failures,
        failures=tuple(failures),
        actual_answer_status=output.answer.status,
        actual_retrieved_doc_ids=actual_retrieved_doc_ids,
        actual_retrieved_chunk_ids=actual_retrieved_chunk_ids,
        actual_supporting_doc_ids=actual_supporting_doc_ids,
        actual_supporting_chunk_ids=actual_supporting_chunk_ids,
    )


def evaluate_cases(cases: list[EvaluationCase], system: SystemUnderTest) -> list[CaseResult]:
    """Evaluate multiple deterministic cases against one system."""

    return [evaluate_case(case, system) for case in cases]


def _check_provenance(
    case: EvaluationCase,
    references: list[SourceReference],
    failures: list[str],
) -> None:
    provenance = case.provenance
    if provenance.require_source_references and not references:
        failures.append(_failure(case.case_id, "expected at least one source reference"))

    for index, reference in enumerate(references, start=1):
        if provenance.require_snippet and not reference.snippet.strip():
            failures.append(
                _failure(case.case_id, f"source reference {index} is missing a snippet")
            )
        if provenance.require_heading_path and reference.heading_path is None:
            failures.append(
                _failure(case.case_id, f"source reference {index} is missing heading_path")
            )
        if provenance.require_passage_anchor and reference.passage_anchor is None:
            failures.append(
                _failure(case.case_id, f"source reference {index} is missing passage_anchor")
            )

    for doc_id, expected_page_label in provenance.expected_page_labels_by_doc_id.items():
        matching_references = [reference for reference in references if reference.doc_id == doc_id]
        if not matching_references:
            failures.append(_failure(case.case_id, f"missing source reference for doc_id {doc_id}"))
            continue

        actual_page_labels = {reference.page_label for reference in matching_references}
        expected_page_labels = {expected_page_label}
        if actual_page_labels != expected_page_labels:
            failures.append(
                _failure(
                    case.case_id,
                    "expected page labels "
                    f"{expected_page_labels} for doc_id {doc_id}, got {actual_page_labels}",
                )
            )


def _expect_equal(
    failures: list[str],
    case_id: str,
    label: str,
    expected: tuple[str, ...] | tuple[str | None, ...] | None,
    actual: tuple[str, ...] | tuple[str | None, ...],
) -> None:
    if expected != actual:
        failures.append(_failure(case_id, f"expected {label} {expected}, got {actual}"))


def _failure(case_id: str, message: str) -> str:
    return f"[{case_id}] {message}"
