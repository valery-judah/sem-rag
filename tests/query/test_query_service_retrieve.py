from __future__ import annotations

import pytest

from parity._contracts import ProcessingStatus
from parity.indexing import DeterministicEmbeddingAdapter, SqlVectorStore
from parity.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlSectionRepository,
)
from parity.query import QueryRequest, QueryService
from parity.query.persistence import SqlQueryRunStore, SqlQuerySnapshotStore, SqlQueryTraceStore
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


def _service(sql_engine) -> QueryService:
    read_model = _read_model(sql_engine)
    return QueryService(
        corpus_read_model=read_model,
        run_store=SqlQueryRunStore(sql_engine),
        snapshot_store=SqlQuerySnapshotStore(sql_engine),
        trace_store=SqlQueryTraceStore(sql_engine),
        retriever=SnapshotDenseQueryRetriever(
            corpus_read_model=read_model,
            embedding_adapter=DeterministicEmbeddingAdapter(),
        ),
    )


def test_execute_until_retrieval_persists_retrieval_trace_and_candidates(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    trace_store = SqlQueryTraceStore(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    ready_chunk = chunk_factory(
        doc_id="doc-ready",
        chunk_id="chunk-ready",
        text="semantic retrieval uses embeddings for passage search",
    )
    chunks.save([ready_chunk])
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(sql_engine),
    ).publish_document(doc_id="doc-ready", chunks=[ready_chunk])

    state = _service(sql_engine).execute_until_retrieval(
        QueryRequest(
            question="What uses embeddings for passage search?",
            workspace_id="ws-1",
        )
    )

    traces = trace_store.list_stage_traces(state.run.query_id)

    assert state.run.status.value == "running"
    assert state.snapshot is not None
    assert state.interpreted_query is not None
    assert [candidate.chunk_id for candidate in state.retrieved_candidates] == ["chunk-ready"]
    assert len(traces) == 2
    assert [trace.stage_name.value for trace in traces] == ["interpret", "retrieve"]
    assert traces[1].payload["retrievable_chunk_count"] == 1
    assert traces[1].payload["candidates"][0]["chunk_id"] == "chunk-ready"


def test_execute_until_retrieval_handles_empty_snapshot(sql_engine) -> None:
    trace_store = SqlQueryTraceStore(sql_engine)

    state = _service(sql_engine).execute_until_retrieval(
        QueryRequest(
            question="What is semantic retrieval?",
            workspace_id="empty-ws",
        )
    )

    traces = trace_store.list_stage_traces(state.run.query_id)

    assert state.snapshot is not None
    assert state.snapshot.eligible_doc_ids == []
    assert state.retrieved_candidates == []
    assert len(traces) == 2
    assert traces[1].stage_name.value == "retrieve"
    assert traces[1].payload["candidates"] == []
