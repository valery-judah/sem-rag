from __future__ import annotations

from doc_forge._contracts import ProcessingStatus
from doc_forge.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlSectionRepository,
)
from doc_forge.query import QueryRequest, QueryService
from doc_forge.query.persistence import SqlQueryRunStore, SqlQuerySnapshotStore, SqlQueryTraceStore
from doc_forge.readmodels import SqlQueryableCorpusReadModel


def _service(sql_engine) -> QueryService:
    return QueryService(
        corpus_read_model=SqlQueryableCorpusReadModel(
            documents=SqlDocumentRepository(sql_engine),
            sections=SqlSectionRepository(sql_engine),
            chunks=SqlChunkRepository(sql_engine),
            chunk_embeddings=SqlChunkEmbeddingRepository(sql_engine),
            index_entries=SqlIndexEntryRepository(sql_engine),
        ),
        run_store=SqlQueryRunStore(sql_engine),
        snapshot_store=SqlQuerySnapshotStore(sql_engine),
        trace_store=SqlQueryTraceStore(sql_engine),
    )


def test_execute_until_interpretation_updates_run_and_persists_trace(
    sql_engine,
    persisted_document_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    run_store = SqlQueryRunStore(sql_engine)
    trace_store = SqlQueryTraceStore(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )

    state = _service(sql_engine).execute_until_interpretation(
        QueryRequest(
            question="Which section explains retries?",
            workspace_id="ws-1",
        )
    )

    persisted_run = run_store.get_query_run(state.run.query_id)
    persisted_traces = trace_store.list_stage_traces(state.run.query_id)

    assert persisted_run is not None
    assert persisted_run.status.value == "running"
    assert state.run.status.value == "running"
    assert state.snapshot is not None
    assert state.snapshot.eligible_doc_ids == ["doc-ready"]
    assert state.interpreted_query is not None
    assert state.interpreted_query.request_type.value == "source_navigation"
    assert len(persisted_traces) == 1
    assert persisted_traces[0].stage_name.value == "interpret"
    assert persisted_traces[0].payload["interpreted_query"] == state.interpreted_query.model_dump(
        mode="json"
    )


def test_execute_until_interpretation_runs_even_with_empty_snapshot(sql_engine) -> None:
    trace_store = SqlQueryTraceStore(sql_engine)

    state = _service(sql_engine).execute_until_interpretation(
        QueryRequest(
            question="What is semantic retrieval?",
            workspace_id="empty-ws",
        )
    )

    traces = trace_store.list_stage_traces(state.run.query_id)

    assert state.snapshot is not None
    assert state.snapshot.eligible_doc_ids == []
    assert state.interpreted_query is not None
    assert state.interpreted_query.request_type.value == "fact_lookup"
    assert len(traces) == 1
