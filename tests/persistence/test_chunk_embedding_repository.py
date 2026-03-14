from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from doc_forge.indexing import ChunkEmbedding, DeterministicEmbeddingAdapter, SqlVectorStore
from doc_forge.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
)

if TYPE_CHECKING:
    from sqlalchemy import Engine

from tests.persistence.conftest import ChunkFactory, PersistedDocumentFactory

pytestmark = pytest.mark.persistence


def test_chunk_embeddings_round_trip_for_document(
    sql_engine: Engine,
    persisted_document_factory: PersistedDocumentFactory,
    chunk_factory: ChunkFactory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    embeddings = SqlChunkEmbeddingRepository(sql_engine)
    document = persisted_document_factory()
    documents.create(document)
    chunks.save([chunk_factory(doc_id=document.doc_id)])

    stored = [
        ChunkEmbedding(
            chunk_id="chunk-1",
            doc_id=document.doc_id,
            embedding_model="deterministic-hash-v1",
            embedding_vector=[0.25, -0.5, 0.75],
            created_at=datetime(2026, 3, 11, tzinfo=UTC),
        )
    ]

    embeddings.replace_for_document(document.doc_id, stored)

    assert embeddings.list_for_document(document.doc_id) == stored


def test_replace_for_document_removes_prior_embeddings(
    sql_engine: Engine,
    persisted_document_factory: PersistedDocumentFactory,
    chunk_factory: ChunkFactory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    embeddings = SqlChunkEmbeddingRepository(sql_engine)
    document = persisted_document_factory()
    documents.create(document)
    chunks.save(
        [
            chunk_factory(doc_id=document.doc_id, chunk_id="chunk-1"),
            chunk_factory(doc_id=document.doc_id, chunk_id="chunk-2", ordinal=1),
        ]
    )
    embeddings.replace_for_document(
        document.doc_id,
        [
            ChunkEmbedding(
                chunk_id="chunk-1",
                doc_id=document.doc_id,
                embedding_model="deterministic-hash-v1",
                embedding_vector=[0.1, 0.2],
                created_at=datetime(2026, 3, 11, tzinfo=UTC),
            )
        ],
    )

    replacement = [
        ChunkEmbedding(
            chunk_id="chunk-2",
            doc_id=document.doc_id,
            embedding_model="deterministic-hash-v1",
            embedding_vector=[0.3, -0.1],
            created_at=datetime(2026, 3, 11, 1, tzinfo=UTC),
        )
    ]
    embeddings.replace_for_document(document.doc_id, replacement)

    assert embeddings.list_for_document(document.doc_id) == replacement


def test_replace_for_document_rejects_cross_document_embeddings(sql_engine: Engine) -> None:
    repository = SqlChunkEmbeddingRepository(sql_engine)

    with pytest.raises(ValueError, match="must belong to the target document"):
        repository.replace_for_document(
            "doc-1",
            [
                ChunkEmbedding(
                    chunk_id="chunk-1",
                    doc_id="doc-2",
                    embedding_model="deterministic-hash-v1",
                    embedding_vector=[1.0],
                    created_at=datetime(2026, 3, 11, tzinfo=UTC),
                )
            ],
        )


def test_vector_store_publish_replaces_document_embeddings_and_supports_smoke_query(
    sql_engine: Engine,
    persisted_document_factory: PersistedDocumentFactory,
    chunk_factory: ChunkFactory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    embeddings = SqlChunkEmbeddingRepository(sql_engine)
    index_entries = SqlIndexEntryRepository(sql_engine)
    document = persisted_document_factory()
    documents.create(document)

    original_chunks = [
        chunk_factory(
            doc_id=document.doc_id,
            chunk_id="chunk-1",
            text="Consensus requires stable coordination for replicated state.",
        ),
        chunk_factory(
            doc_id=document.doc_id,
            chunk_id="chunk-2",
            ordinal=1,
            text="Leader election narrows conflicting writers during failover.",
        ),
    ]
    chunks.save(original_chunks)

    store = SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        chunk_embeddings=embeddings,
        index_entries=index_entries,
    )
    store.publish_document(doc_id=document.doc_id, chunks=original_chunks)

    replacement_chunks = [
        chunk_factory(
            doc_id=document.doc_id,
            chunk_id="chunk-3",
            ordinal=2,
            text="Consensus requires stable coordination and quorum progress.",
        )
    ]
    chunks.replace_for_document(document.doc_id, replacement_chunks)
    published = store.publish_document(doc_id=document.doc_id, chunks=replacement_chunks)

    assert [entry.chunk_id for entry in published] == ["chunk-3"]
    assert [embedding.chunk_id for embedding in embeddings.list_for_document(document.doc_id)] == [
        "chunk-3"
    ]
    assert [entry.chunk_id for entry in index_entries.list_for_document(document.doc_id)] == [
        "chunk-3"
    ]

    hits = store.smoke_query(
        doc_id=document.doc_id,
        text="How does consensus coordinate quorum progress?",
    )

    assert [hit.chunk_id for hit in hits] == ["chunk-3"]
    assert hits[0].score > 0.0
