from __future__ import annotations

import pytest

from parity._contracts import ProcessingStatus
from parity.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlSectionRepository,
)
from parity.query import (
    DuplicateSuppressionMode,
    InterpretedQuery,
    QueryPolicyDefaults,
    QueryRequest,
    QueryRequestType,
    QuerySpecificity,
    RetrievedCandidate,
    SynthesisMode,
)
from parity.query.selection import DeterministicQuerySelector
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


def _base_interpreted_query(**overrides: object) -> InterpretedQuery:
    payload: dict[str, object] = {
        "normalized_question": "explain semantic retrieval",
        "request_type": QueryRequestType.EXPLANATION,
        "answer_shape": "explanatory paragraph",
        "specificity": QuerySpecificity.SECTION_SCOPED,
        "scope_hints": ["retrieval"],
        "requires_synthesis": False,
        "synthesis_mode": SynthesisMode.NONE,
        "requires_source_navigation": False,
        "unsupported_capability_flags": [],
        "normalization_notes": [],
    }
    payload.update(overrides)
    return InterpretedQuery(**payload)


def test_selector_groups_multiple_same_document_passages_for_explanation(
    sql_engine,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections = SqlSectionRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-1",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    sections.save(
        [
            section_factory(
                doc_id="doc-1",
                section_id="section-a",
                heading_path=["Chapter 1", "Retrieval"],
                heading_text="Retrieval",
                page_start=2,
                page_end=3,
            )
        ]
    )
    chunks.save(
        [
            chunk_factory(
                doc_id="doc-1",
                chunk_id="chunk-1",
                section_id="section-a",
                heading_path=["Chapter 1", "Retrieval"],
                ordinal=0,
                text="Retrieval begins by embedding the normalized question.",
            ),
            chunk_factory(
                doc_id="doc-1",
                chunk_id="chunk-2",
                section_id="section-a",
                heading_path=["Chapter 1", "Retrieval"],
                ordinal=1,
                page_start=3,
                page_end=3,
                text="The system then searches nearby passages in vector space.",
            ),
        ]
    )
    snapshot = _read_model(sql_engine).capture_snapshot("ws-1")
    result = DeterministicQuerySelector(corpus_read_model=_read_model(sql_engine)).select(
        request=QueryRequest(question="Explain retrieval", workspace_id="ws-1"),
        snapshot=snapshot,
        interpreted_query=_base_interpreted_query(),
        retrieved_candidates=[
            RetrievedCandidate(
                doc_id="doc-1",
                chunk_id="chunk-1",
                section_id="section-a",
                heading_path=["Chapter 1", "Retrieval"],
                locator="p. 2",
                retrieval_score=0.95,
                retrieval_rank=1,
            ),
            RetrievedCandidate(
                doc_id="doc-1",
                chunk_id="chunk-2",
                section_id="section-a",
                heading_path=["Chapter 1", "Retrieval"],
                locator="p. 3",
                retrieval_score=0.88,
                retrieval_rank=2,
            ),
        ],
        policy=QueryPolicyDefaults.build(),
    )

    assert [candidate.chunk_id for candidate in result.selected_candidates] == [
        "chunk-1",
        "chunk-2",
    ]
    assert len(result.evidence_sets) == 1
    assert result.evidence_sets[0].grouping_mode.value == "same_document_multi_passage"
    assert [unit.candidate.chunk_id for unit in result.evidence_sets[0].evidence_units][:2] == [
        "chunk-1",
        "chunk-2",
    ]


def test_selector_suppresses_heading_and_locator_duplicates_deterministically(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-1",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    chunks.save(
        [
            chunk_factory(
                doc_id="doc-1",
                chunk_id="chunk-a",
                heading_path=["Chapter 1", "Retrieval"],
                ordinal=0,
            ),
            chunk_factory(
                doc_id="doc-1",
                chunk_id="chunk-b",
                heading_path=["Chapter 1", "Retrieval"],
                ordinal=1,
            ),
        ]
    )
    snapshot = _read_model(sql_engine).capture_snapshot("ws-1")
    policy = QueryPolicyDefaults.build().model_copy(
        update={"duplicate_suppression_mode": DuplicateSuppressionMode.HEADING_AND_LOCATOR}
    )
    result = DeterministicQuerySelector(corpus_read_model=_read_model(sql_engine)).select(
        request=QueryRequest(question="Where is retrieval discussed?", workspace_id="ws-1"),
        snapshot=snapshot,
        interpreted_query=_base_interpreted_query(
            request_type=QueryRequestType.SOURCE_NAVIGATION,
            specificity=QuerySpecificity.PRECISE,
            requires_source_navigation=True,
        ),
        retrieved_candidates=[
            RetrievedCandidate(
                doc_id="doc-1",
                chunk_id="chunk-a",
                section_id="section-a",
                heading_path=["Chapter 1", "Retrieval"],
                locator="p. 2",
                retrieval_score=0.91,
                retrieval_rank=1,
            ),
            RetrievedCandidate(
                doc_id="doc-1",
                chunk_id="chunk-b",
                section_id="section-a",
                heading_path=["Chapter 1", "Retrieval"],
                locator="p. 2",
                retrieval_score=0.87,
                retrieval_rank=2,
            ),
        ],
        policy=policy,
    )

    assert [candidate.chunk_id for candidate in result.selected_candidates] == ["chunk-a"]
    assert any(decision.drop_reason == "duplicate_suppression" for decision in result.decisions)
    assert result.duplicate_suppression_notes == ["chunk-b suppressed as duplicate of chunk-a"]
