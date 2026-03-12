from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import pytest
from pydantic import ValidationError

from doc_forge._contracts import (
    Answer,
    AnswerStatus,
    Chunk,
    Document,
    ProcessingStatus,
    RetrievalHit,
    Section,
    SourceReference,
    SourceType,
)

pytestmark = pytest.mark.contract


def make_source_reference(**overrides: Any) -> SourceReference:
    return SourceReference(
        doc_id="doc-1",
        document_title="Doc 1",
        snippet="Relevant supporting passage.",
        **overrides,
    )


def test_document_requires_minimal_fields() -> None:
    document = Document(
        doc_id="doc-1",
        workspace_id="workspace-1",
        source_type=SourceType.PDF,
        title="Book",
        filename="book.pdf",
        uploaded_at=datetime(2026, 3, 8, tzinfo=UTC),
        ingest_status=ProcessingStatus.UPLOADED,
        storage_ref="s3://bucket/book.pdf",
    )

    assert document.doc_id == "doc-1"


def test_document_rejects_invalid_source_type() -> None:
    with pytest.raises(ValidationError, match="source_type"):
        Document(
            doc_id="doc-1",
            workspace_id="workspace-1",
            source_type=cast(Any, "txt"),
            title="Book",
            filename="book.txt",
            uploaded_at=datetime(2026, 3, 8, tzinfo=UTC),
            ingest_status=ProcessingStatus.UPLOADED,
            storage_ref="s3://bucket/book.txt",
        )


def test_document_rejects_invalid_ingest_status() -> None:
    with pytest.raises(ValidationError, match="ingest_status"):
        Document(
            doc_id="doc-1",
            workspace_id="workspace-1",
            source_type=SourceType.MARKDOWN,
            title="Notes",
            filename="notes.md",
            uploaded_at=datetime(2026, 3, 8, tzinfo=UTC),
            ingest_status=cast(Any, "queued"),
            storage_ref="file:///notes.md",
        )


def test_section_requires_heading_path_and_valid_ranges() -> None:
    section = Section(
        section_id="section-1",
        doc_id="doc-1",
        heading_path=["Chapter 1", "Overview"],
        depth=1,
        page_start=1,
        page_end=2,
    )

    assert section.heading_path == ["Chapter 1", "Overview"]

    with pytest.raises(ValidationError, match="heading_path"):
        Section(
            section_id="section-1",
            doc_id="doc-1",
            heading_path=[],
            depth=0,
        )

    with pytest.raises(
        ValidationError,
        match="page_end must be greater than or equal to page_start",
    ):
        Section(
            section_id="section-1",
            doc_id="doc-1",
            heading_path=["Only"],
            depth=0,
            page_start=3,
            page_end=2,
        )


def test_chunk_requires_minimal_fields_and_validates_offsets() -> None:
    chunk = Chunk(
        chunk_id="chunk-1",
        doc_id="doc-1",
        text="chunk text",
        ordinal=0,
        heading_path=["Chapter 1"],
        source_start_offset=0,
        source_end_offset=10,
    )

    assert chunk.ordinal == 0

    with pytest.raises(
        ValidationError,
        match="source_end_offset must be greater than or equal to source_start_offset",
    ):
        Chunk(
            chunk_id="chunk-1",
            doc_id="doc-1",
            text="chunk text",
            ordinal=0,
            heading_path=["Chapter 1"],
            source_start_offset=10,
            source_end_offset=5,
        )


def test_source_reference_can_omit_heading_and_page_but_not_document_identity() -> None:
    reference = make_source_reference()

    assert reference.heading_path is None
    assert reference.page_label is None
    assert reference.passage_anchor is None

    degraded = make_source_reference(
        heading_path=None,
        page_label=None,
        passage_anchor="doc-1#chunk-1",
    )

    assert degraded.snippet == "Relevant supporting passage."

    with pytest.raises(ValidationError, match="doc_id"):
        SourceReference.model_validate(
            {
                "document_title": "Doc 1",
                "snippet": "Relevant supporting passage.",
            }
        )

    with pytest.raises(ValidationError, match="heading_path"):
        make_source_reference(heading_path=[])


def test_retrieval_hit_requires_nested_source_reference() -> None:
    hit = RetrievalHit(
        chunk_id="chunk-1",
        doc_id="doc-1",
        score=0.9,
        source_reference=make_source_reference(
            chunk_id="chunk-1",
            passage_anchor="doc-1#chunk-1",
        ),
    )

    assert hit.source_reference.doc_id == "doc-1"
    assert hit.source_reference.passage_anchor == "doc-1#chunk-1"


def test_answer_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError, match="status"):
        Answer(
            status=cast(Any, "partial"),
            answer_text="Maybe.",
            source_references=[],
        )


def test_supported_answer_requires_source_reference() -> None:
    with pytest.raises(
        ValidationError,
        match="supported answers must include at least one source reference",
    ):
        Answer(
            status=AnswerStatus.SUPPORTED,
            answer_text="The answer is supported.",
            source_references=[],
        )


def test_insufficient_evidence_answer_requires_note() -> None:
    with pytest.raises(
        ValidationError,
        match="insufficient_evidence answers must include an insufficiency_note",
    ):
        Answer(
            status=AnswerStatus.INSUFFICIENT_EVIDENCE,
            answer_text="I do not have enough evidence.",
            source_references=[],
        )


def test_supported_answer_rejects_insufficiency_note() -> None:
    with pytest.raises(
        ValidationError,
        match="supported answers must not include an insufficiency_note",
    ):
        Answer(
            status=AnswerStatus.SUPPORTED,
            answer_text="The answer is supported.",
            source_references=[make_source_reference()],
            insufficiency_note="This should not appear on supported answers.",
        )


def test_insufficient_evidence_answer_requires_explicit_empty_source_references() -> None:
    with pytest.raises(
        ValidationError,
        match="insufficient_evidence answers must use an explicit empty source_references list",
    ):
        Answer(
            status=AnswerStatus.INSUFFICIENT_EVIDENCE,
            answer_text="I do not have enough evidence.",
            source_references=[make_source_reference()],
            insufficiency_note="No directly supporting passage was retrieved.",
        )


def test_answer_accepts_locked_status_semantics() -> None:
    supported = Answer(
        status=AnswerStatus.SUPPORTED,
        answer_text="The notes define vector search as semantic retrieval over embeddings.",
        source_references=[make_source_reference()],
    )
    insufficient = Answer(
        status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        answer_text="I could not find enough support in the corpus.",
        source_references=[],
        insufficiency_note="No retrieved passage directly answered the question.",
    )

    assert supported.status is AnswerStatus.SUPPORTED
    assert insufficient.status is AnswerStatus.INSUFFICIENT_EVIDENCE
