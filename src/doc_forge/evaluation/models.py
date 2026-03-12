"""Internal types for deterministic evaluation harnesses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from doc_forge._contracts import Answer, AnswerStatus, RetrievalHit


@dataclass(frozen=True)
class ProvenanceExpectation:
    """Assertions about inspectable provenance returned by a system under test."""

    require_source_references: bool = False
    require_snippet: bool = False
    require_heading_path: bool = False
    require_passage_anchor: bool = False
    expected_page_labels_by_doc_id: dict[str, str | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for doc_id in self.expected_page_labels_by_doc_id:
            if not doc_id:
                raise ValueError("expected_page_labels_by_doc_id keys must not be empty")


@dataclass(frozen=True)
class EvaluationCase:
    """One deterministic evaluation scenario and its expected outcomes."""

    case_id: str
    scenario_name: str
    question: str
    expected_status: AnswerStatus
    expected_retrieved_doc_ids: tuple[str, ...] | None = None
    expected_retrieved_chunk_ids: tuple[str, ...] | None = None
    expected_supporting_doc_ids: tuple[str, ...] | None = None
    expected_supporting_chunk_ids: tuple[str, ...] | None = None
    provenance: ProvenanceExpectation = field(default_factory=ProvenanceExpectation)

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id must not be empty")
        if not self.scenario_name:
            raise ValueError("scenario_name must not be empty")
        if not self.question:
            raise ValueError("question must not be empty")

        self._validate_id_pair(
            "expected_retrieved",
            self.expected_retrieved_doc_ids,
            self.expected_retrieved_chunk_ids,
        )
        self._validate_id_pair(
            "expected_supporting",
            self.expected_supporting_doc_ids,
            self.expected_supporting_chunk_ids,
        )

        if self.expected_status is AnswerStatus.SUPPORTED:
            if not self.expected_supporting_doc_ids or not self.expected_supporting_chunk_ids:
                raise ValueError(
                    "supported cases must declare expected supporting doc and chunk ids"
                )
        else:
            if self.expected_supporting_doc_ids != () or self.expected_supporting_chunk_ids != ():
                raise ValueError(
                    "insufficient_evidence cases must use explicit empty supporting "
                    "doc and chunk ids"
                )

    @staticmethod
    def _validate_id_pair(
        prefix: str,
        doc_ids: tuple[str, ...] | None,
        chunk_ids: tuple[str, ...] | None,
    ) -> None:
        if (doc_ids is None) != (chunk_ids is None):
            raise ValueError(
                f"{prefix}_doc_ids and {prefix}_chunk_ids must both be set or both be None"
            )
        if doc_ids is not None:
            assert chunk_ids is not None
            if len(doc_ids) != len(chunk_ids):
                raise ValueError(
                    f"{prefix}_doc_ids and {prefix}_chunk_ids must have the same length"
                )


@dataclass(frozen=True)
class EvaluationOutput:
    """Observed answer and retrieval trace produced for one evaluation case."""

    retrieval_hits: list[RetrievalHit]
    answer: Answer


@dataclass(frozen=True)
class CaseResult:
    """Pass/fail result for one deterministic evaluation case."""

    case_id: str
    passed: bool
    failures: tuple[str, ...]
    actual_answer_status: AnswerStatus
    actual_retrieved_doc_ids: tuple[str, ...]
    actual_retrieved_chunk_ids: tuple[str, ...]
    actual_supporting_doc_ids: tuple[str, ...]
    actual_supporting_chunk_ids: tuple[str | None, ...]


class SystemUnderTest(Protocol):
    """Deterministic execution surface for one evaluation case."""

    def __call__(self, case: EvaluationCase) -> EvaluationOutput:
        """Execute one case and return retrieval hits plus the answer payload."""
        ...
