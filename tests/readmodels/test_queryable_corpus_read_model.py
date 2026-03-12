from __future__ import annotations

from datetime import UTC, datetime

import pytest

from doc_forge.indexing import ChunkEmbedding, IndexEntry
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlSectionRepository,
)
from doc_forge.readmodels import SqlQueryableCorpusReadModel

pytestmark = pytest.mark.anyio


def _read_model(sql_engine) -> SqlQueryableCorpusReadModel:
    return SqlQueryableCorpusReadModel(
        documents=SqlDocumentRepository(sql_engine),
        sections=SqlSectionRepository(sql_engine),
        chunks=SqlChunkRepository(sql_engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(sql_engine),
        index_entries=SqlIndexEntryRepository(sql_engine),
    )


def test_capture_snapshot_returns_only_ready_documents_for_workspace(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    index_entries = SqlIndexEntryRepository(sql_engine)

    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    documents.create(
        persisted_document_factory(
            doc_id="doc-indexed",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.INDEXED,
        )
    )
    documents.create(
        persisted_document_factory(
            doc_id="doc-other-workspace",
            workspace_id="ws-2",
            ingest_status=ProcessingStatus.READY,
        )
    )
    chunks.save(
        [
            chunk_factory(
                doc_id="doc-ready",
                chunk_id="chunk-ready",
                page_start=1,
                page_end=1,
                source_start_offset=None,
                source_end_offset=None,
            ),
            chunk_factory(
                doc_id="doc-indexed",
                chunk_id="chunk-indexed",
                page_start=2,
                page_end=2,
            ),
        ]
    )
    index_entries.replace_for_document(
        "doc-ready",
        [
            IndexEntry(
                chunk_id="chunk-ready",
                doc_id="doc-ready",
                index_backend="deterministic",
                index_key="doc-ready:chunk-ready",
                index_version="idx-v1",
                published_at=datetime(2026, 3, 11, tzinfo=UTC),
            )
        ],
    )

    snapshot = _read_model(sql_engine).capture_snapshot(
        "ws-1",
        query_started_at=datetime(2026, 3, 11, 9, tzinfo=UTC),
    )

    assert snapshot.workspace_id == "ws-1"
    assert snapshot.eligible_doc_ids == ["doc-ready"]
    assert snapshot.retrieval_index_version == "idx-v1"


def test_list_chunks_for_snapshot_returns_only_provenance_bearing_chunks(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)

    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    chunks.save(
        [
            chunk_factory(
                doc_id="doc-ready",
                chunk_id="chunk-provenanced",
                page_start=1,
                page_end=1,
                source_start_offset=None,
                source_end_offset=None,
            ),
            chunk_factory(
                doc_id="doc-ready",
                chunk_id="chunk-unprovenanced",
                section_id=None,
                page_start=None,
                page_end=None,
                source_start_offset=None,
                source_end_offset=None,
            ),
        ]
    )

    snapshot = _read_model(sql_engine).capture_snapshot("ws-1")
    queryable_chunks = _read_model(sql_engine).list_chunks_for_snapshot(snapshot)

    assert [chunk.chunk_id for chunk in queryable_chunks] == ["chunk-provenanced"]
    assert queryable_chunks[0].heading_path
    assert queryable_chunks[0].page_start == 1


def test_list_embedded_chunks_for_snapshot_returns_only_snapshot_chunks_with_embeddings(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    embeddings = SqlChunkEmbeddingRepository(sql_engine)

    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    documents.create(
        persisted_document_factory(
            doc_id="doc-outside",
            workspace_id="ws-2",
            ingest_status=ProcessingStatus.READY,
        )
    )
    chunks.save(
        [
            chunk_factory(
                doc_id="doc-ready",
                chunk_id="chunk-embedded",
                text="semantic retrieval over embeddings",
            ),
            chunk_factory(
                doc_id="doc-ready",
                chunk_id="chunk-missing-embedding",
                text="missing embedding should not surface",
                ordinal=1,
            ),
            chunk_factory(
                doc_id="doc-outside",
                chunk_id="chunk-outside",
                text="outside workspace chunk",
            ),
        ]
    )
    embeddings.replace_for_document(
        "doc-ready",
        [
            ChunkEmbedding(
                chunk_id="chunk-embedded",
                doc_id="doc-ready",
                embedding_model="deterministic-hash-v1",
                embedding_vector=[0.1, 0.2, 0.3],
                created_at=datetime(2026, 3, 11, tzinfo=UTC),
            )
        ],
    )
    embeddings.replace_for_document(
        "doc-outside",
        [
            ChunkEmbedding(
                chunk_id="chunk-outside",
                doc_id="doc-outside",
                embedding_model="deterministic-hash-v1",
                embedding_vector=[0.9, 0.8, 0.7],
                created_at=datetime(2026, 3, 11, tzinfo=UTC),
            )
        ],
    )

    snapshot = _read_model(sql_engine).capture_snapshot("ws-1")
    embedded_chunks = _read_model(sql_engine).list_embedded_chunks_for_snapshot(snapshot)

    assert [chunk.chunk_id for chunk in embedded_chunks] == ["chunk-embedded"]
    assert embedded_chunks[0].embedding_model == "deterministic-hash-v1"
    assert embedded_chunks[0].embedding_vector == [0.1, 0.2, 0.3]
