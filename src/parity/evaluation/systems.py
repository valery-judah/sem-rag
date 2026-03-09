"""Deterministic systems-under-test for the evaluation harness."""

from __future__ import annotations

from typing import Protocol

from parity._contracts import Answer, RetrievalHit

from .fixtures import (
    build_insufficient_evidence_corpus_question_seam,
    build_supported_corpus_question_seam,
)
from .models import EvaluationCase, EvaluationOutput


class SeamResult(Protocol):
    """Common attributes exposed by deterministic seam fixtures."""

    @property
    def retrieval_hits(self) -> list[RetrievalHit]:
        """Deterministic retrieval trace for the seam."""

    @property
    def answer(self) -> Answer:
        """Deterministic answer payload for the seam."""


class DeterministicSeamSystem:
    """Route evaluation cases to deterministic seam fixtures."""

    def __call__(self, case: EvaluationCase) -> EvaluationOutput:
        if case.case_id == "supported-cross-document":
            seam: SeamResult = build_supported_corpus_question_seam(case.question)
        elif case.case_id == "insufficient-evidence":
            seam = build_insufficient_evidence_corpus_question_seam(case.question)
        elif case.case_id == "provenance-completeness":
            seam = build_supported_corpus_question_seam(case.question)
        else:
            raise ValueError(f"unknown evaluation case: {case.case_id}")

        return EvaluationOutput(retrieval_hits=seam.retrieval_hits, answer=seam.answer)
