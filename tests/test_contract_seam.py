from __future__ import annotations

from itertools import pairwise

from parity._contracts import (
    AnswerStatus,
    ProcessingStatus,
    can_transition_processing_status,
)
from tests.support.contract_seam import (
    build_insufficient_evidence_corpus_question_seam,
    build_supported_corpus_question_seam,
    locked_lifecycle_path,
)


def test_supported_corpus_question_seam_returns_cross_document_answer() -> None:
    seam = build_supported_corpus_question_seam()

    assert len(seam.documents) == 4
    assert len({document.workspace_id for document in seam.documents}) == 1
    assert seam.answer.status is AnswerStatus.SUPPORTED
    assert len(seam.answer.source_references) == 2
    assert len({reference.doc_id for reference in seam.answer.source_references}) == 2


def test_supported_corpus_question_seam_preserves_retrieval_trace() -> None:
    seam = build_supported_corpus_question_seam()

    assert len(seam.retrieval_hits) == 2

    answer_references = {
        (
            reference.doc_id,
            reference.chunk_id,
            reference.document_title,
            reference.snippet,
            reference.passage_anchor,
        )
        for reference in seam.answer.source_references
    }

    for hit in seam.retrieval_hits:
        reference = hit.source_reference
        assert (
            reference.doc_id,
            reference.chunk_id,
            reference.document_title,
            reference.snippet,
            reference.passage_anchor,
        ) in answer_references

    assert seam.retrieval_hits[0].source_reference.page_label == "p. 14"
    assert seam.retrieval_hits[1].source_reference.page_label is None


def test_supported_corpus_question_seam_uses_ready_documents() -> None:
    seam = build_supported_corpus_question_seam()

    valid_doc_ids = {document.doc_id for document in seam.documents}

    assert all(document.ingest_status is ProcessingStatus.READY for document in seam.documents)
    assert all(section.doc_id in valid_doc_ids for section in seam.sections)
    assert all(chunk.doc_id in valid_doc_ids for chunk in seam.chunks)


def test_insufficient_evidence_corpus_question_seam_returns_honest_failure() -> None:
    seam = build_insufficient_evidence_corpus_question_seam()

    assert len(seam.documents) == 4
    assert seam.answer.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert seam.answer.answer_text == "I could not find enough support in the uploaded corpus."
    assert (
        seam.answer.insufficiency_note
        == "None of the retrieved corpus material answered the latency-budget question."
    )
    assert seam.answer.source_references == []
    assert seam.retrieval_hits == []


def test_contract_seam_helper_keeps_cross_document_links_consistent() -> None:
    seam = build_supported_corpus_question_seam()

    valid_doc_ids = {document.doc_id for document in seam.documents}
    section_by_id = {section.section_id: section for section in seam.sections}
    chunk_by_id = {chunk.chunk_id: chunk for chunk in seam.chunks}

    assert all(section.doc_id in valid_doc_ids for section in seam.sections)
    assert all(
        section.parent_section_id is None or section.parent_section_id in section_by_id
        for section in seam.sections
    )
    assert all(chunk.doc_id in valid_doc_ids for chunk in seam.chunks)
    assert all(
        chunk.section_id in section_by_id for chunk in seam.chunks if chunk.section_id is not None
    )
    assert all(hit.chunk_id in chunk_by_id for hit in seam.retrieval_hits)


def test_lifecycle_contract_seam() -> None:
    linear_path = locked_lifecycle_path()

    for current, new in pairwise(linear_path):
        assert can_transition_processing_status(current, new)

    assert can_transition_processing_status(ProcessingStatus.CHUNKED, ProcessingStatus.FAILED)
    assert not can_transition_processing_status(ProcessingStatus.READY, ProcessingStatus.FAILED)
    assert not can_transition_processing_status(ProcessingStatus.FAILED, ProcessingStatus.READY)
