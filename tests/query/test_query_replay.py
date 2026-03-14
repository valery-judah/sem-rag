from __future__ import annotations

import pytest
import sqlalchemy as sa

from doc_forge.indexing import DeterministicEmbeddingAdapter, SqlVectorStore
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlSectionRepository,
)
from doc_forge.query import QueryRequest, QueryService
from doc_forge.query.answer_mode_policy import DeterministicAnswerModePolicy
from doc_forge.query.context_assembly import DeterministicContextAssembler
from doc_forge.query.persistence import (
    SqlQueryAnswerStore,
    SqlQueryRunStore,
    SqlQuerySnapshotStore,
    SqlQueryTraceStore,
)
from doc_forge.query.replay import QueryReplayService
from doc_forge.query.retrieval import SnapshotDenseQueryRetriever
from doc_forge.query.selection import DeterministicQuerySelector
from doc_forge.query.support_assessment import HybridSupportAssessor
from doc_forge.readmodels import SqlQueryableCorpusReadModel
from tests.persistence.conftest import ChunkFactory, PersistedDocumentFactory

pytestmark = pytest.mark.anyio


def _read_model(sql_engine: sa.Engine) -> SqlQueryableCorpusReadModel:
    return SqlQueryableCorpusReadModel(
        documents=SqlDocumentRepository(sql_engine),
        sections=SqlSectionRepository(sql_engine),
        chunks=SqlChunkRepository(sql_engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(sql_engine),
        index_entries=SqlIndexEntryRepository(sql_engine),
    )


def _query_service(sql_engine: sa.Engine) -> QueryService:
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
        selector=DeterministicQuerySelector(corpus_read_model=read_model),
        context_assembler=DeterministicContextAssembler(),
        support_assessor=HybridSupportAssessor(),
        answer_mode_policy=DeterministicAnswerModePolicy(),
        answer_store=SqlQueryAnswerStore(sql_engine),
    )


def _replay_service(sql_engine: sa.Engine) -> QueryReplayService:
    return QueryReplayService(
        run_store=SqlQueryRunStore(sql_engine),
        snapshot_store=SqlQuerySnapshotStore(sql_engine),
        trace_store=SqlQueryTraceStore(sql_engine),
        answer_store=SqlQueryAnswerStore(sql_engine),
    )


def test_replay_bundle_uses_persisted_snapshot_and_policy(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
    chunk_factory: ChunkFactory,
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
    documents.create(
        persisted_document_factory(
            doc_id="doc-later",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.INDEXED,
        )
    )
    ready_chunk = chunk_factory(
        doc_id="doc-ready",
        chunk_id="chunk-ready",
        text="vector search uses embeddings to retrieve related passages",
    )
    later_chunk = chunk_factory(
        doc_id="doc-later",
        chunk_id="chunk-later",
        text="later document content",
    )
    chunks.save([ready_chunk, later_chunk])
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(sql_engine),
    ).publish_document(doc_id="doc-ready", chunks=[ready_chunk])

    state = _query_service(sql_engine).execute_until_answer(
        QueryRequest(
            question="What uses embeddings to retrieve related passages?",
            workspace_id="ws-1",
        )
    )

    documents.update_status(doc_id="doc-later", status=ProcessingStatus.READY)
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(sql_engine),
    ).publish_document(doc_id="doc-later", chunks=[later_chunk])

    bundle = _replay_service(sql_engine).build_bundle(state.run.query_id)

    assert bundle.request.question == "What uses embeddings to retrieve related passages?"
    assert bundle.policy.retrieval_candidate_cap == 24
    assert bundle.snapshot is not None
    assert bundle.snapshot.eligible_doc_ids == ["doc-ready"]
    assert bundle.trace_bundle.run_status.value == "succeeded"
    assert len(bundle.trace_bundle.stage_traces) == 8


def test_replay_reconstructs_stage_inputs_from_persisted_traces(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
    chunk_factory: ChunkFactory,
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

    state = _query_service(sql_engine).execute_until_answer(
        QueryRequest(
            question="What uses embeddings for passage search?",
            workspace_id="ws-1",
        )
    )

    reconstructed = _replay_service(sql_engine).reconstruct_inputs(state.run.query_id)

    assert reconstructed.snapshot is not None
    assert reconstructed.snapshot.eligible_doc_ids == ["doc-ready"]
    assert reconstructed.interpreted_query is not None
    assert reconstructed.interpreted_query.request_type.value == "fact_lookup"
    assert [candidate.chunk_id for candidate in reconstructed.retrieved_candidates] == [
        "chunk-ready"
    ]
    assert [candidate.chunk_id for candidate in reconstructed.selected_candidates] == [
        "chunk-ready"
    ]
    assert [evidence_set.evidence_set_id for evidence_set in reconstructed.evidence_sets] == [
        "es-1"
    ]
    assert reconstructed.context_manifest is not None
    assert state.context_manifest is not None
    assert (
        reconstructed.context_manifest.ordered_evidence_set_ids
        == state.context_manifest.ordered_evidence_set_ids
    )
    assert reconstructed.context_manifest.included_evidence_set_ids == ["es-1"]
    assert reconstructed.support_assessment is not None
    assert reconstructed.support_assessment.support_state.value == "sufficient"
    assert reconstructed.answer_mode_decision is not None
    assert reconstructed.answer_mode_decision.answer_mode.value == "direct_answer"
    assert reconstructed.answer_draft is not None
    assert "semantic retrieval uses embeddings" in reconstructed.answer_draft.answer_text
