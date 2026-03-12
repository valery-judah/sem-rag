"""Committed deterministic evaluation cases for the MVP regression harness."""

from __future__ import annotations

from parity._contracts import AnswerStatus

from .fixtures import INSUFFICIENT_EVIDENCE_QUESTION, SUPPORTED_QUESTION
from .models import EvaluationCase, ProvenanceExpectation

BASELINE_EVALUATION_CASES: list[EvaluationCase] = [
    EvaluationCase(
        case_id="supported-cross-document",
        scenario_name="supported cross-document answer",
        question=SUPPORTED_QUESTION,
        expected_status=AnswerStatus.SUPPORTED,
        expected_retrieved_doc_ids=("doc-1", "doc-2"),
        expected_retrieved_chunk_ids=("chunk-1", "chunk-2"),
        expected_supporting_doc_ids=("doc-1", "doc-2"),
        expected_supporting_chunk_ids=("chunk-1", "chunk-2"),
        provenance=ProvenanceExpectation(
            require_source_references=True,
            require_snippet=True,
            require_heading_path=True,
            require_passage_anchor=True,
        ),
    ),
    EvaluationCase(
        case_id="insufficient-evidence",
        scenario_name="honest insufficient evidence answer",
        question=INSUFFICIENT_EVIDENCE_QUESTION,
        expected_status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        expected_retrieved_doc_ids=(),
        expected_retrieved_chunk_ids=(),
        expected_supporting_doc_ids=(),
        expected_supporting_chunk_ids=(),
    ),
    EvaluationCase(
        case_id="provenance-completeness",
        scenario_name="inspectable provenance across mixed source types",
        question=SUPPORTED_QUESTION,
        expected_status=AnswerStatus.SUPPORTED,
        expected_supporting_doc_ids=("doc-1", "doc-2"),
        expected_supporting_chunk_ids=("chunk-1", "chunk-2"),
        provenance=ProvenanceExpectation(
            require_source_references=True,
            require_snippet=True,
            require_heading_path=True,
            require_passage_anchor=True,
            expected_page_labels_by_doc_id={"doc-1": "p. 14", "doc-2": None},
        ),
    ),
]
