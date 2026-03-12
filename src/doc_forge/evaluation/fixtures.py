"""Deterministic synthetic corpus fixtures for MVP evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

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

SUPPORTED_QUESTION = "How do leader election and quorum overlap make Raft resilient?"
INSUFFICIENT_EVIDENCE_QUESTION = "What deployment latency budget is recommended for GPU clusters?"


@dataclass(frozen=True)
class SupportedCorpusQuestionSeam:
    """Cross-document supported answer built over a ready corpus."""

    question: str
    documents: list[Document]
    sections: list[Section]
    chunks: list[Chunk]
    retrieval_hits: list[RetrievalHit]
    answer: Answer


@dataclass(frozen=True)
class InsufficientEvidenceCorpusQuestionSeam:
    """Honest insufficient-evidence answer over the same ready corpus."""

    question: str
    documents: list[Document]
    sections: list[Section]
    chunks: list[Chunk]
    retrieval_hits: list[RetrievalHit]
    answer: Answer


def make_documents() -> list[Document]:
    """Build one deterministic mixed-format corpus."""

    uploaded_at = datetime(2026, 3, 8, tzinfo=UTC)
    workspace_id = "workspace-1"
    return [
        Document(
            doc_id="doc-1",
            workspace_id=workspace_id,
            source_type=SourceType.PDF,
            title="Distributed Systems Notes",
            filename="distributed-systems.pdf",
            uploaded_at=uploaded_at,
            ingest_status=ProcessingStatus.READY,
            storage_ref="file:///docs/distributed-systems.pdf",
        ),
        Document(
            doc_id="doc-2",
            workspace_id=workspace_id,
            source_type=SourceType.MARKDOWN,
            title="Raft Study Guide",
            filename="raft-study-guide.md",
            uploaded_at=uploaded_at,
            ingest_status=ProcessingStatus.READY,
            storage_ref="file:///docs/raft-study-guide.md",
        ),
        Document(
            doc_id="doc-3",
            workspace_id=workspace_id,
            source_type=SourceType.PDF,
            title="Caching Handbook",
            filename="caching-handbook.pdf",
            uploaded_at=uploaded_at,
            ingest_status=ProcessingStatus.READY,
            storage_ref="file:///docs/caching-handbook.pdf",
        ),
        Document(
            doc_id="doc-4",
            workspace_id=workspace_id,
            source_type=SourceType.MARKDOWN,
            title="Observability Checklist",
            filename="observability-checklist.md",
            uploaded_at=uploaded_at,
            ingest_status=ProcessingStatus.READY,
            storage_ref="file:///docs/observability-checklist.md",
        ),
    ]


def make_sections(documents: list[Document]) -> list[Section]:
    """Build structure metadata for the deterministic corpus."""

    document_by_id = {document.doc_id: document for document in documents}
    return [
        Section(
            section_id="section-1",
            doc_id=document_by_id["doc-1"].doc_id,
            heading_path=["Chapter 2"],
            depth=0,
            heading_text="Chapter 2",
            page_start=12,
            page_end=12,
        ),
        Section(
            section_id="section-2",
            doc_id=document_by_id["doc-1"].doc_id,
            parent_section_id="section-1",
            heading_path=["Chapter 2", "Consensus"],
            depth=1,
            heading_text="Consensus",
            page_start=13,
            page_end=15,
        ),
        Section(
            section_id="section-3",
            doc_id=document_by_id["doc-2"].doc_id,
            heading_path=["Raft"],
            depth=0,
            heading_text="Raft",
        ),
        Section(
            section_id="section-4",
            doc_id=document_by_id["doc-2"].doc_id,
            parent_section_id="section-3",
            heading_path=["Raft", "Safety"],
            depth=1,
            heading_text="Safety",
        ),
        Section(
            section_id="section-5",
            doc_id=document_by_id["doc-3"].doc_id,
            heading_path=["Caching"],
            depth=0,
            heading_text="Caching",
            page_start=7,
            page_end=7,
        ),
        Section(
            section_id="section-6",
            doc_id=document_by_id["doc-4"].doc_id,
            heading_path=["Tracing"],
            depth=0,
            heading_text="Tracing",
        ),
    ]


def make_chunks(documents: list[Document], sections: list[Section]) -> list[Chunk]:
    """Build retrieval-ready chunks for the deterministic corpus."""

    _ = documents
    section_by_id = {section.section_id: section for section in sections}
    return [
        Chunk(
            chunk_id="chunk-1",
            doc_id="doc-1",
            section_id="section-2",
            text="Raft elects a leader so replicas follow one log source during coordination.",
            ordinal=0,
            heading_path=section_by_id["section-2"].heading_path,
            page_start=14,
            page_end=14,
            source_start_offset=0,
            source_end_offset=74,
        ),
        Chunk(
            chunk_id="chunk-2",
            doc_id="doc-2",
            section_id="section-4",
            text=(
                "Majority quorums overlap, so a newly elected leader carries "
                "committed entries forward safely."
            ),
            ordinal=0,
            heading_path=section_by_id["section-4"].heading_path,
            source_start_offset=0,
            source_end_offset=91,
        ),
        Chunk(
            chunk_id="chunk-3",
            doc_id="doc-3",
            section_id="section-5",
            text=(
                "Cache invalidation should prioritize correctness over hit rate "
                "when freshness is uncertain."
            ),
            ordinal=0,
            heading_path=section_by_id["section-5"].heading_path,
            page_start=7,
            page_end=7,
            source_start_offset=0,
            source_end_offset=89,
        ),
        Chunk(
            chunk_id="chunk-4",
            doc_id="doc-4",
            section_id="section-6",
            text="Tracing helps operators correlate requests across services during incidents.",
            ordinal=0,
            heading_path=section_by_id["section-6"].heading_path,
            source_start_offset=0,
            source_end_offset=76,
        ),
    ]


def make_source_reference(
    document: Document,
    chunk: Chunk,
    section: Section,
) -> SourceReference:
    """Build one inspectable answer citation for the deterministic corpus."""

    page_label = None
    if document.source_type is SourceType.PDF and chunk.page_start is not None:
        page_label = f"p. {chunk.page_start}"
    return SourceReference(
        doc_id=document.doc_id,
        document_title=document.title,
        snippet=chunk.text,
        section_id=section.section_id,
        heading_path=chunk.heading_path,
        page_label=page_label,
        chunk_id=chunk.chunk_id,
        passage_anchor=f"{document.doc_id}#{chunk.chunk_id}",
    )


def make_retrieval_hit(
    document: Document,
    chunk: Chunk,
    source_reference: SourceReference,
    score: float,
) -> RetrievalHit:
    """Build one deterministic retrieval hit."""

    return RetrievalHit(
        chunk_id=chunk.chunk_id,
        doc_id=document.doc_id,
        score=score,
        source_reference=source_reference,
    )


def build_supported_corpus_question_seam(
    question: str = SUPPORTED_QUESTION,
) -> SupportedCorpusQuestionSeam:
    """Compose a supported answer over two documents in the same corpus."""

    documents = make_documents()
    sections = make_sections(documents)
    chunks = make_chunks(documents, sections)

    document_by_id = {document.doc_id: document for document in documents}
    section_by_id = {section.section_id: section for section in sections}
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}

    first_reference = make_source_reference(
        document_by_id["doc-1"],
        chunk_by_id["chunk-1"],
        section_by_id["section-2"],
    )
    second_reference = make_source_reference(
        document_by_id["doc-2"],
        chunk_by_id["chunk-2"],
        section_by_id["section-4"],
    )

    retrieval_hits = [
        make_retrieval_hit(document_by_id["doc-1"], chunk_by_id["chunk-1"], first_reference, 0.93),
        make_retrieval_hit(document_by_id["doc-2"], chunk_by_id["chunk-2"], second_reference, 0.89),
    ]

    answer = Answer(
        status=AnswerStatus.SUPPORTED,
        answer_text=(
            "The corpus says Raft is resilient because leader election centralizes log "
            "replication and overlapping majorities preserve committed entries across "
            "leadership changes."
        ),
        source_references=[first_reference, second_reference],
    )

    return SupportedCorpusQuestionSeam(
        question=question,
        documents=documents,
        sections=sections,
        chunks=chunks,
        retrieval_hits=retrieval_hits,
        answer=answer,
    )


def build_insufficient_evidence_corpus_question_seam(
    question: str = INSUFFICIENT_EVIDENCE_QUESTION,
) -> InsufficientEvidenceCorpusQuestionSeam:
    """Compose an honest insufficient-evidence answer over the same corpus."""

    documents = make_documents()
    sections = make_sections(documents)
    chunks = make_chunks(documents, sections)
    answer = Answer(
        status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        answer_text="I could not find enough support in the uploaded corpus.",
        source_references=[],
        insufficiency_note=(
            "None of the retrieved corpus material answered the latency-budget question."
        ),
    )

    return InsufficientEvidenceCorpusQuestionSeam(
        question=question,
        documents=documents,
        sections=sections,
        chunks=chunks,
        retrieval_hits=[],
        answer=answer,
    )


def locked_lifecycle_path() -> list[ProcessingStatus]:
    """Return the canonical linear lifecycle locked by WS-001."""

    return [
        ProcessingStatus.UPLOADED,
        ProcessingStatus.REGISTERED,
        ProcessingStatus.EXTRACTING,
        ProcessingStatus.NORMALIZED,
        ProcessingStatus.CHUNKED,
        ProcessingStatus.INDEXED,
        ProcessingStatus.READY,
    ]
