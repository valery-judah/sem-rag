from __future__ import annotations

from datetime import UTC, datetime

import pytest

from doc_forge.indexing import IndexEntry
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlSectionRepository,
)
from doc_forge.query import QueryRequest, QueryService
from doc_forge.query.persistence import SqlQueryRunStore, SqlQuerySnapshotStore
from doc_forge.readmodels import SqlQueryableCorpusReadModel

pytestmark = pytest.mark.anyio


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
    )


def test_prepare_query_persists_run_and_snapshot(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    index_entries = SqlIndexEntryRepository(sql_engine)
    run_store = SqlQueryRunStore(sql_engine)
    snapshot_store = SqlQuerySnapshotStore(sql_engine)

    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    chunks.save([chunk_factory(doc_id="doc-ready", chunk_id="chunk-ready")])
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

    state = _service(sql_engine).prepare_query(
        QueryRequest(
            question="What does the ready document say?",
            workspace_id="ws-1",
        )
    )

    persisted_run = run_store.get_query_run(state.run.query_id)
    persisted_snapshot = snapshot_store.get_snapshot(state.run.query_id)

    assert persisted_run is not None
    assert persisted_run.workspace_id == "ws-1"
    assert persisted_run.policy_snapshot["retrieval_candidate_cap"] == 24
    assert persisted_snapshot is not None
    assert persisted_snapshot.query_started_at == state.run.submitted_at
    assert persisted_snapshot.eligible_doc_ids == ["doc-ready"]
    assert persisted_snapshot.retrieval_index_version == "idx-v1"


def test_prepare_query_freezes_snapshot_membership_across_later_ready_transition(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    index_entries = SqlIndexEntryRepository(sql_engine)
    snapshot_store = SqlQuerySnapshotStore(sql_engine)
    service = _service(sql_engine)

    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    documents.create(
        persisted_document_factory(
            doc_id="doc-later",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.INDEXED,
        )
    )
    chunks.save(
        [
            chunk_factory(doc_id="doc-ready", chunk_id="chunk-ready"),
            chunk_factory(doc_id="doc-later", chunk_id="chunk-later"),
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
    index_entries.replace_for_document(
        "doc-later",
        [
            IndexEntry(
                chunk_id="chunk-later",
                doc_id="doc-later",
                index_backend="deterministic",
                index_key="doc-later:chunk-later",
                index_version="idx-v1",
                published_at=datetime(2026, 3, 11, tzinfo=UTC),
            )
        ],
    )

    first = service.prepare_query(QueryRequest(question="first query", workspace_id="ws-1"))

    documents.update_status(doc_id="doc-later", status=ProcessingStatus.READY)

    second = service.prepare_query(QueryRequest(question="second query", workspace_id="ws-1"))

    assert first.snapshot is not None
    assert second.snapshot is not None
    assert first.snapshot.eligible_doc_ids == ["doc-ready"]
    assert second.snapshot.eligible_doc_ids == ["doc-later", "doc-ready"]
    first_persisted = snapshot_store.get_snapshot(first.run.query_id)
    second_persisted = snapshot_store.get_snapshot(second.run.query_id)
    assert first_persisted is not None
    assert second_persisted is not None
    assert first_persisted.model_dump() == first.snapshot.model_dump()
    assert second_persisted.model_dump() == second.snapshot.model_dump()


def test_prepare_query_allows_explicit_empty_snapshot(sql_engine) -> None:
    state = _service(sql_engine).prepare_query(
        QueryRequest(
            question="What documents are available?",
            workspace_id="empty-workspace",
        )
    )

    assert state.snapshot is not None
    assert state.snapshot.workspace_id == "empty-workspace"
    assert state.snapshot.eligible_doc_ids == []
