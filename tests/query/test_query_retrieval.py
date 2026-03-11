from __future__ import annotations

from datetime import UTC, datetime

import pytest

from parity._contracts import ProcessingStatus
from parity.indexing import ChunkEmbedding, DeterministicEmbeddingAdapter
from parity.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlSectionRepository,
)
from parity.query import (
    InterpretedQuery,
    QueryPolicyDefaults,
    QueryRequest,
    QueryRequestType,
    QuerySpecificity,
    SynthesisMode,
)
from parity.query.retrieval import SnapshotDenseQueryRetriever
from parity.readmodels import SqlQueryableCorpusReadModel

pytestmark = pytest.mark.anyio


def _read_model(sql_engine) -> SqlQueryableCorpusReadModel:
    return SqlQueryableCorpusReadModel(
        documents=SqlDocumentRepository(sql_engine),
        sections=SqlSectionRepository(sql_engine),
        chunks=SqlChunkRepository(sql_engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(sql_engine),
        index_entries=SqlIndexEntryRepository(sql_engine),
    )


def _interpreted_query(normalized_question: str) -> InterpretedQuery:
    return InterpretedQuery(
        normalized_question=normalized_question,
        request_type=QueryRequestType.FACT_LOOKUP,
        answer_shape="short answer",
        specificity=QuerySpecificity.PRECISE,
        scope_hints=["retrieval"],
        requires_synthesis=False,
        synthesis_mode=SynthesisMode.NONE,
        requires_source_navigation=False,
        unsupported_capability_flags=[],
        normalization_notes=[],
    )


def test_snapshot_dense_retriever_respects_snapshot_and_preserves_provenance(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    embeddings = SqlChunkEmbeddingRepository(sql_engine)

    documents.create(
        persisted_document_factory(
            doc_id="doc-target",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    documents.create(
        persisted_document_factory(
            doc_id="doc-other",
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
                doc_id="doc-target",
                chunk_id="chunk-target",
                text="vector search uses embeddings to retrieve related passages",
                page_start=3,
                page_end=3,
            ),
            chunk_factory(
                doc_id="doc-other",
                chunk_id="chunk-other",
                text="consensus requires a stable leader and quorum",
                page_start=4,
                page_end=4,
            ),
            chunk_factory(
                doc_id="doc-outside",
                chunk_id="chunk-outside",
                text="vector search uses embeddings to retrieve related passages",
                page_start=9,
                page_end=9,
            ),
        ]
    )
    adapter = DeterministicEmbeddingAdapter()
    embeddings.replace_for_document(
        "doc-target",
        [
            ChunkEmbedding(
                chunk_id="chunk-target",
                doc_id="doc-target",
                embedding_model=adapter.model_name,
                embedding_vector=adapter.embed_texts(
                    ["vector search uses embeddings to retrieve related passages"]
                )[0],
                created_at=datetime(2026, 3, 11, tzinfo=UTC),
            )
        ],
    )
    embeddings.replace_for_document(
        "doc-other",
        [
            ChunkEmbedding(
                chunk_id="chunk-other",
                doc_id="doc-other",
                embedding_model=adapter.model_name,
                embedding_vector=adapter.embed_texts(
                    ["consensus requires a stable leader and quorum"]
                )[0],
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
                embedding_model=adapter.model_name,
                embedding_vector=adapter.embed_texts(
                    ["vector search uses embeddings to retrieve related passages"]
                )[0],
                created_at=datetime(2026, 3, 11, tzinfo=UTC),
            )
        ],
    )

    snapshot = _read_model(sql_engine).capture_snapshot("ws-1")
    result = SnapshotDenseQueryRetriever(
        corpus_read_model=_read_model(sql_engine),
        embedding_adapter=adapter,
    ).retrieve(
        request=QueryRequest(
            question="What uses embeddings to retrieve related passages?",
            workspace_id="ws-1",
        ),
        snapshot=snapshot,
        interpreted_query=_interpreted_query("what uses embeddings to retrieve related passages"),
        policy=QueryPolicyDefaults.build(),
    )

    assert [candidate.doc_id for candidate in result.candidates] == ["doc-target", "doc-other"]
    assert result.candidates[0].chunk_id == "chunk-target"
    assert result.candidates[0].locator == "p. 3"
    assert result.candidates[0].retrieval_rank == 1
    assert result.retrievable_chunk_count == 2


def test_snapshot_dense_retriever_returns_empty_candidates_for_empty_snapshot(sql_engine) -> None:
    snapshot = _read_model(sql_engine).capture_snapshot("empty-ws")
    result = SnapshotDenseQueryRetriever(
        corpus_read_model=_read_model(sql_engine),
        embedding_adapter=DeterministicEmbeddingAdapter(),
    ).retrieve(
        request=QueryRequest(
            question="What is semantic retrieval?",
            workspace_id="empty-ws",
        ),
        snapshot=snapshot,
        interpreted_query=_interpreted_query("what is semantic retrieval"),
        policy=QueryPolicyDefaults.build(),
    )

    assert result.retrievable_chunk_count == 0
    assert result.candidates == []
