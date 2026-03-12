from __future__ import annotations

from datetime import UTC, datetime

import pytest

from doc_forge._contracts import ProcessingStatus, SourceType
from doc_forge.artifacts import FilesystemArtifactStore, NormalizedArtifact, NormalizedArtifactBlock
from doc_forge.indexing import DeterministicEmbeddingAdapter, SqlVectorStore
from doc_forge.lifecycle.readiness import ReadinessService
from doc_forge.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlSectionRepository,
)

pytestmark = pytest.mark.contract


def _seed_ready_document(
    *,
    sql_engine,
    tmp_path,
    persisted_document_factory,
    section_factory,
    chunk_factory,
):
    artifact_store = FilesystemArtifactStore(tmp_path / "artifacts")
    documents = SqlDocumentRepository(sql_engine)
    sections = SqlSectionRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    index_entries = SqlIndexEntryRepository(sql_engine)
    chunk_embeddings = SqlChunkEmbeddingRepository(sql_engine)
    vector_store = SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=index_entries,
        chunk_embeddings=chunk_embeddings,
    )

    document = persisted_document_factory(
        doc_id="doc-ready-contract",
        workspace_id="ws-contract",
        source_type=SourceType.MARKDOWN,
        ingest_status=ProcessingStatus.INDEXED,
        filename="ready.md",
        title="Readiness Contract",
        uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
        updated_at=datetime(2026, 3, 11, tzinfo=UTC),
    )
    documents.create(document)
    artifact_store.write_normalized(
        workspace_id=document.workspace_id,
        artifact=NormalizedArtifact(
            doc_id=document.doc_id,
            source_type=document.source_type,
            normalizer_version="markdown-v1",
            blocks=[
                NormalizedArtifactBlock(
                    kind="heading",
                    text="Overview",
                    order_index=0,
                    heading_path=["Overview"],
                    heading_level=1,
                ),
                NormalizedArtifactBlock(
                    kind="paragraph",
                    text="Consensus keeps replicas aligned.",
                    order_index=1,
                    heading_path=["Overview"],
                ),
            ],
        ),
    )
    section = section_factory(
        doc_id=document.doc_id,
        section_id="section-ready-contract",
        heading_path=["Overview"],
        heading_text="Overview",
        depth=0,
        page_start=None,
        page_end=None,
    )
    sections.replace_for_document(document.doc_id, [section])
    chunk = chunk_factory(
        doc_id=document.doc_id,
        chunk_id="chunk-ready-contract",
        section_id=section.section_id,
        heading_path=["Overview"],
        text="Consensus keeps replicas aligned.",
        page_start=None,
        page_end=None,
        source_start_offset=0,
        source_end_offset=33,
    )
    chunks.replace_for_document(document.doc_id, [chunk])
    vector_store.publish_document(doc_id=document.doc_id, chunks=[chunk])

    readiness = ReadinessService(
        documents=documents,
        sections=sections,
        chunks=chunks,
        index_entries=index_entries,
        artifact_store=artifact_store,
        vector_store=vector_store,
    )
    return {
        "artifact_store": artifact_store,
        "chunk_embeddings": chunk_embeddings,
        "chunks": chunks,
        "doc_id": document.doc_id,
        "documents": documents,
        "index_entries": index_entries,
        "readiness": readiness,
        "sections": sections,
    }


def test_readiness_accepts_complete_document(
    sql_engine,
    tmp_path,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    state = _seed_ready_document(
        sql_engine=sql_engine,
        tmp_path=tmp_path,
        persisted_document_factory=persisted_document_factory,
        section_factory=section_factory,
        chunk_factory=chunk_factory,
    )

    result = state["readiness"].evaluate(doc_id=state["doc_id"])

    assert result.is_ready is True
    assert result.reasons == []


def test_readiness_requires_document_record(
    sql_engine,
    tmp_path,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    state = _seed_ready_document(
        sql_engine=sql_engine,
        tmp_path=tmp_path,
        persisted_document_factory=persisted_document_factory,
        section_factory=section_factory,
        chunk_factory=chunk_factory,
    )

    result = state["readiness"].evaluate(doc_id="missing-doc")

    assert result.is_ready is False
    assert result.reasons == ["missing_document"]


def test_readiness_requires_normalized_artifact(
    sql_engine,
    tmp_path,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    state = _seed_ready_document(
        sql_engine=sql_engine,
        tmp_path=tmp_path,
        persisted_document_factory=persisted_document_factory,
        section_factory=section_factory,
        chunk_factory=chunk_factory,
    )
    document = state["documents"].get(state["doc_id"])
    assert document is not None
    state["artifact_store"].delete_normalized(
        workspace_id=document.workspace_id,
        doc_id=document.doc_id,
    )

    result = state["readiness"].evaluate(doc_id=state["doc_id"])

    assert result.is_ready is False
    assert "missing_normalized_artifact" in result.reasons


def test_readiness_requires_sections(
    sql_engine,
    tmp_path,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    state = _seed_ready_document(
        sql_engine=sql_engine,
        tmp_path=tmp_path,
        persisted_document_factory=persisted_document_factory,
        section_factory=section_factory,
        chunk_factory=chunk_factory,
    )
    state["sections"].replace_for_document(state["doc_id"], [])

    result = state["readiness"].evaluate(doc_id=state["doc_id"])

    assert result.is_ready is False
    assert "missing_sections" in result.reasons
    assert "missing_chunks" in result.reasons
    assert "retrieval_smoke_failed" in result.reasons


def test_readiness_requires_chunks(
    sql_engine,
    tmp_path,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    state = _seed_ready_document(
        sql_engine=sql_engine,
        tmp_path=tmp_path,
        persisted_document_factory=persisted_document_factory,
        section_factory=section_factory,
        chunk_factory=chunk_factory,
    )
    state["chunks"].replace_for_document(state["doc_id"], [])

    result = state["readiness"].evaluate(doc_id=state["doc_id"])

    assert result.is_ready is False
    assert "missing_chunks" in result.reasons
    assert "retrieval_smoke_failed" in result.reasons


def test_readiness_requires_index_count_to_match_chunk_count(
    sql_engine,
    tmp_path,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    state = _seed_ready_document(
        sql_engine=sql_engine,
        tmp_path=tmp_path,
        persisted_document_factory=persisted_document_factory,
        section_factory=section_factory,
        chunk_factory=chunk_factory,
    )
    state["index_entries"].replace_for_document(state["doc_id"], [])

    result = state["readiness"].evaluate(doc_id=state["doc_id"])

    assert result.is_ready is False
    assert "index_entry_count_mismatch" in result.reasons


def test_readiness_requires_valid_chunk_section_linkage(
    sql_engine,
    tmp_path,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    state = _seed_ready_document(
        sql_engine=sql_engine,
        tmp_path=tmp_path,
        persisted_document_factory=persisted_document_factory,
        section_factory=section_factory,
        chunk_factory=chunk_factory,
    )
    state["chunks"].replace_for_document(
        state["doc_id"],
        [
            chunk_factory(
                doc_id=state["doc_id"],
                chunk_id="chunk-ready-contract",
                section_id=None,
                heading_path=["Overview"],
                text="Consensus keeps replicas aligned.",
                page_start=None,
                page_end=None,
                source_start_offset=0,
                source_end_offset=33,
            )
        ],
    )

    result = state["readiness"].evaluate(doc_id=state["doc_id"])

    assert result.is_ready is False
    assert "broken_chunk_section_linkage" in result.reasons


def test_readiness_requires_retrieval_smoke_query_to_pass(
    sql_engine,
    tmp_path,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    state = _seed_ready_document(
        sql_engine=sql_engine,
        tmp_path=tmp_path,
        persisted_document_factory=persisted_document_factory,
        section_factory=section_factory,
        chunk_factory=chunk_factory,
    )
    state["chunk_embeddings"].replace_for_document(state["doc_id"], [])

    result = state["readiness"].evaluate(doc_id=state["doc_id"])

    assert result.is_ready is False
    assert result.reasons == ["retrieval_smoke_failed"]


def test_readiness_rejected_for_failed_document(
    sql_engine,
    tmp_path,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    state = _seed_ready_document(
        sql_engine=sql_engine,
        tmp_path=tmp_path,
        persisted_document_factory=persisted_document_factory,
        section_factory=section_factory,
        chunk_factory=chunk_factory,
    )
    state["documents"].update_status(
        doc_id=state["doc_id"],
        status=ProcessingStatus.FAILED,
        updated_at=datetime(2026, 3, 11, 1, tzinfo=UTC),
        failure_code="extract_failed",
        failure_detail="failed to extract malformed pdf",
    )

    result = state["readiness"].evaluate(doc_id=state["doc_id"])

    assert result.is_ready is False
    assert result.reasons == ["document_failed"]
