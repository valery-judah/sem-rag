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
from parity.query.answer_mode_policy import DeterministicAnswerModePolicy
from parity.query.context_assembly import DeterministicContextAssembler
from parity.query.persistence import (
    SqlQueryAnswerStore,
    SqlQueryRunStore,
    SqlQuerySnapshotStore,
    SqlQueryTraceStore,
)
from parity.query.retrieval import SnapshotDenseQueryRetriever
from parity.query.selection import DeterministicQuerySelector
from parity.query.support_assessment import HybridSupportAssessor
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
        selector=DeterministicQuerySelector(corpus_read_model=read_model),
        context_assembler=DeterministicContextAssembler(),
        support_assessor=HybridSupportAssessor(),
        answer_mode_policy=DeterministicAnswerModePolicy(),
        answer_store=SqlQueryAnswerStore(sql_engine),
    )


def test_execute_until_selection_persists_selection_trace_and_evidence_sets(
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

    state = _service(sql_engine).execute_until_selection(
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
    assert [candidate.chunk_id for candidate in state.selected_candidates] == ["chunk-ready"]
    assert len(state.evidence_sets) == 1
    assert state.evidence_sets[0].grouping_mode.value == "single_passage"
    assert len(traces) == 3
    assert [trace.stage_name.value for trace in traces] == ["interpret", "retrieve", "select"]
    assert traces[1].payload["retrievable_chunk_count"] == 1
    assert traces[1].payload["candidates"][0]["chunk_id"] == "chunk-ready"
    assert traces[2].payload["selected_candidates"][0]["chunk_id"] == "chunk-ready"
    assert (
        traces[2].payload["evidence_sets"][0]["evidence_units"][0]["candidate"]["chunk_id"]
        == "chunk-ready"
    )


def test_execute_until_selection_handles_empty_snapshot(sql_engine) -> None:
    trace_store = SqlQueryTraceStore(sql_engine)

    state = _service(sql_engine).execute_until_selection(
        QueryRequest(
            question="What is semantic retrieval?",
            workspace_id="empty-ws",
        )
    )

    traces = trace_store.list_stage_traces(state.run.query_id)

    assert state.snapshot is not None
    assert state.snapshot.eligible_doc_ids == []
    assert state.retrieved_candidates == []
    assert state.selected_candidates == []
    assert state.evidence_sets == []
    assert len(traces) == 3
    assert traces[1].stage_name.value == "retrieve"
    assert traces[1].payload["candidates"] == []
    assert traces[2].stage_name.value == "select"
    assert traces[2].payload["evidence_sets"] == []


def test_execute_until_context_assembly_persists_context_trace_and_manifest(
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
        page_start=2,
        page_end=2,
        text="semantic retrieval uses embeddings for passage search",
    )
    chunks.save([ready_chunk])
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(sql_engine),
    ).publish_document(doc_id="doc-ready", chunks=[ready_chunk])

    state = _service(sql_engine).execute_until_context_assembly(
        QueryRequest(
            question="What uses embeddings for passage search?",
            workspace_id="ws-1",
        )
    )

    traces = trace_store.list_stage_traces(state.run.query_id)

    assert state.context_manifest is not None
    assert state.context_manifest.ordered_evidence_set_ids == ["es-1"]
    assert state.context_manifest.included_evidence_set_ids == ["es-1"]
    assert state.context_manifest.dropped_evidence_set_ids == []
    assert len(state.context_manifest.context_items) == 1
    assert state.context_manifest.context_items[0].evidence_set_id == "es-1"
    assert (
        "semantic retrieval uses embeddings"
        in state.context_manifest.context_items[0].rendered_text
    )
    assert len(traces) == 4
    assert [trace.stage_name.value for trace in traces] == [
        "interpret",
        "retrieve",
        "select",
        "assemble_context",
    ]
    assert traces[3].payload["included_evidence_set_ids"] == ["es-1"]
    assert traces[3].payload["context_items"][0]["evidence_set_id"] == "es-1"


def test_execute_until_context_assembly_handles_empty_snapshot(sql_engine) -> None:
    trace_store = SqlQueryTraceStore(sql_engine)

    state = _service(sql_engine).execute_until_context_assembly(
        QueryRequest(
            question="What is semantic retrieval?",
            workspace_id="empty-ws",
        )
    )

    traces = trace_store.list_stage_traces(state.run.query_id)

    assert state.context_manifest is not None
    assert state.context_manifest.ordered_evidence_set_ids == []
    assert state.context_manifest.included_evidence_set_ids == []
    assert state.context_manifest.context_items == []
    assert len(traces) == 4
    assert traces[3].stage_name.value == "assemble_context"
    assert traces[3].payload["context_items"] == []


def test_execute_until_answer_mode_persists_support_and_answer_mode_traces(
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
        page_start=4,
        page_end=4,
        text="vector search uses embeddings to retrieve related passages",
    )
    chunks.save([ready_chunk])
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(sql_engine),
    ).publish_document(doc_id="doc-ready", chunks=[ready_chunk])

    state = _service(sql_engine).execute_until_answer_mode(
        QueryRequest(
            question="What uses embeddings to retrieve related passages?",
            workspace_id="ws-1",
        )
    )

    traces = trace_store.list_stage_traces(state.run.query_id)

    assert state.support_assessment is not None
    assert state.support_assessment.support_state.value == "sufficient"
    assert state.support_assessment.qualifying_reason_codes == []
    assert state.answer_mode_decision is not None
    assert state.answer_mode_decision.answer_mode.value == "direct_answer"
    assert len(traces) == 6
    assert [trace.stage_name.value for trace in traces] == [
        "interpret",
        "retrieve",
        "select",
        "assemble_context",
        "assess_support",
        "decide_answer_mode",
    ]
    assert traces[4].payload["final_support_state"] == "sufficient"
    assert traces[5].payload["final_answer_mode"] == "direct_answer"


def test_execute_until_answer_mode_handles_empty_snapshot_with_abstention(sql_engine) -> None:
    trace_store = SqlQueryTraceStore(sql_engine)

    state = _service(sql_engine).execute_until_answer_mode(
        QueryRequest(
            question="What is available in the corpus?",
            workspace_id="empty-ws",
        )
    )

    traces = trace_store.list_stage_traces(state.run.query_id)

    assert state.support_assessment is not None
    assert state.support_assessment.support_state.value == "insufficient"
    assert [reason.value for reason in state.support_assessment.qualifying_reason_codes] == [
        "no_evidence_available"
    ]
    assert state.answer_mode_decision is not None
    assert state.answer_mode_decision.answer_mode.value == "full_abstention"
    assert len(traces) == 6
    assert traces[4].payload["qualifying_reason_codes"] == ["no_evidence_available"]
    assert traces[5].payload["final_answer_mode"] == "full_abstention"


def test_execute_until_answer_persists_final_answer_and_citation_artifacts(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    trace_store = SqlQueryTraceStore(sql_engine)
    answer_store = SqlQueryAnswerStore(sql_engine)
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
        page_start=4,
        page_end=4,
        text="vector search uses embeddings to retrieve related passages",
    )
    chunks.save([ready_chunk])
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(sql_engine),
    ).publish_document(doc_id="doc-ready", chunks=[ready_chunk])

    state = _service(sql_engine).execute_until_answer(
        QueryRequest(
            question="What uses embeddings to retrieve related passages?",
            workspace_id="ws-1",
        )
    )

    traces = trace_store.list_stage_traces(state.run.query_id)
    persisted = answer_store.get_answer_artifacts(state.run.query_id)

    assert state.run.status.value == "succeeded"
    assert state.answer_draft is not None
    assert (
        "vector search uses embeddings to retrieve related passages"
        in state.answer_draft.answer_text
    )
    assert state.answer_draft.grounded_evidence_set_ids == ["es-1"]
    assert state.answer_draft.generator_version == "answer_generation.deterministic.v1"
    assert state.citation_bundle is not None
    assert len(state.citation_bundle.citations) == 1
    assert state.citation_bundle.material_doc_ids == ["doc-ready"]
    assert state.citation_bundle.renderer_version == "citation_rendering.deterministic.v1"
    assert len(traces) == 8
    assert [trace.stage_name.value for trace in traces] == [
        "interpret",
        "retrieve",
        "select",
        "assemble_context",
        "assess_support",
        "decide_answer_mode",
        "generate",
        "render_citations",
    ]
    assert traces[6].payload["generator_version"] == "answer_generation.deterministic.v1"
    assert traces[7].payload["citation_count"] == 1
    assert persisted is not None
    assert persisted.answer.answer_text == state.answer_draft.answer_text
    assert persisted.citations.material_doc_ids == ["doc-ready"]
    assert persisted.answer_mode.value == "direct_answer"


def test_execute_until_answer_handles_empty_snapshot_with_honest_abstention(sql_engine) -> None:
    answer_store = SqlQueryAnswerStore(sql_engine)

    state = _service(sql_engine).execute_until_answer(
        QueryRequest(
            question="What is available in the corpus?",
            workspace_id="empty-ws",
        )
    )

    persisted = answer_store.get_answer_artifacts(state.run.query_id)

    assert state.run.status.value == "succeeded"
    assert state.answer_draft is not None
    assert "does not provide enough support" in state.answer_draft.answer_text
    assert state.answer_draft.should_render_citations is False
    assert state.citation_bundle is not None
    assert state.citation_bundle.citations == []
    assert persisted is not None
    assert persisted.citations.citations == []
