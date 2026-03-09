"""Compatibility re-export for deterministic seam fixtures used in tests."""

from parity.evaluation.fixtures import (
    INSUFFICIENT_EVIDENCE_QUESTION,
    SUPPORTED_QUESTION,
    InsufficientEvidenceCorpusQuestionSeam,
    SupportedCorpusQuestionSeam,
    build_insufficient_evidence_corpus_question_seam,
    build_supported_corpus_question_seam,
    locked_lifecycle_path,
    make_chunks,
    make_documents,
    make_retrieval_hit,
    make_sections,
    make_source_reference,
)

__all__ = [
    "INSUFFICIENT_EVIDENCE_QUESTION",
    "SUPPORTED_QUESTION",
    "InsufficientEvidenceCorpusQuestionSeam",
    "SupportedCorpusQuestionSeam",
    "build_insufficient_evidence_corpus_question_seam",
    "build_supported_corpus_question_seam",
    "locked_lifecycle_path",
    "make_chunks",
    "make_documents",
    "make_retrieval_hit",
    "make_sections",
    "make_source_reference",
]
