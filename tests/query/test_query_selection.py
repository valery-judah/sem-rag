from __future__ import annotations

import pytest
import sqlalchemy as sa
from typing import Any

from doc_forge.lifecycle import ProcessingStatus
from doc_forge.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlSectionRepository,
)
from doc_forge.query import (
    DuplicateSuppressionMode,
    InterpretedQuery,
    QueryPolicyDefaults,
    QueryRequest,
    QueryRequestType,
    QuerySpecificity,
    RetrievedCandidate,
    SynthesisMode,
)
from doc_forge.query.selection import DeterministicQuerySelector
from doc_forge.readmodels import SqlQueryableCorpusReadModel

pytestmark = pytest.mark.anyio


def _read_model(sql_engine: sa.Engine) -> SqlQueryableCorpusReadModel:
    return SqlQueryableCorpusReadModel(
        documents=SqlDocumentRepository(sql_engine),
        sections=SqlSectionRepository(sql_engine),
        chunks=SqlChunkRepository(sql_engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(sql_engine),
        index_entries=SqlIndexEntryRepository(sql_engine),
    )


def _base_interpreted_query(**overrides: object) -> InterpretedQuery:
    return InterpretedQuery(
        normalized_question="explain semantic retrieval",
        request_type=QueryRequestType.EXPLANATION,
        answer_shape="explanatory paragraph",
        specificity=QuerySpecificity.SECTION_SCOPED,
        scope_hints=["retrieval"],
        requires_synthesis=False,
        synthesis_mode=SynthesisMode.NONE,
        requires_source_navigation=False,
        unsupported_capability_flags=[],
        normalization_notes=[],
    ).model_copy(update=overrides)


from tests.persistence.conftest import ChunkFactory, PersistedDocumentFactory, SectionFactory


def test_selector_groups_multiple_same_document_passages_for_explanation(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
    section_factory: SectionFactory,
    chunk_factory: ChunkFactory,
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
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
    chunk_factory: ChunkFactory,
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


def test_selector_prefers_scope_matching_documents_for_comparison(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
    chunk_factory: ChunkFactory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-atlas",
            workspace_id="ws-1",
            title="Atlas Cache Design",
            ingest_status=ProcessingStatus.READY,
        )
    )
    documents.create(
        persisted_document_factory(
            doc_id="doc-beacon",
            workspace_id="ws-1",
            title="Beacon Dashboard Cache",
            ingest_status=ProcessingStatus.READY,
        )
    )
    documents.create(
        persisted_document_factory(
            doc_id="doc-comet",
            workspace_id="ws-1",
            title="Comet Background Notes",
            ingest_status=ProcessingStatus.READY,
        )
    )
    chunks.save(
        [
            chunk_factory(
                doc_id="doc-atlas",
                chunk_id="chunk-atlas",
                heading_path=["Atlas", "Caching"],
                ordinal=0,
                text="Atlas uses immediate invalidation and write-through caching.",
            ),
            chunk_factory(
                doc_id="doc-beacon",
                chunk_id="chunk-beacon",
                heading_path=["Beacon", "Caching"],
                ordinal=0,
                text="Beacon uses a 15-minute TTL and allows stale reads.",
            ),
            chunk_factory(
                doc_id="doc-comet",
                chunk_id="chunk-comet",
                heading_path=["Comet", "Reports"],
                ordinal=0,
                text="Comet runs unrelated overnight batch analytics jobs.",
            ),
        ]
    )

    snapshot = _read_model(sql_engine).capture_snapshot("ws-1")
    result = DeterministicQuerySelector(corpus_read_model=_read_model(sql_engine)).select(
        request=QueryRequest(
            question=(
                "Compare Atlas and Beacon caching strategies. "
                "Which system has stricter freshness guarantees?"
            ),
            workspace_id="ws-1",
        ),
        snapshot=snapshot,
        interpreted_query=_base_interpreted_query(
            normalized_question=(
                "compare atlas and beacon caching strategies which system has "
                "stricter freshness guarantees"
            ),
            request_type=QueryRequestType.COMPARISON,
            answer_shape="qualified_comparison",
            specificity=QuerySpecificity.BROAD,
            scope_hints=["atlas", "beacon", "caching", "freshness"],
            requires_synthesis=True,
            synthesis_mode=SynthesisMode.CROSS_DOCUMENT,
        ),
        retrieved_candidates=[
            RetrievedCandidate(
                doc_id="doc-comet",
                chunk_id="chunk-comet",
                section_id="section-comet",
                heading_path=["Comet", "Reports"],
                locator="p. 5",
                retrieval_score=0.99,
                retrieval_rank=1,
            ),
            RetrievedCandidate(
                doc_id="doc-atlas",
                chunk_id="chunk-atlas",
                section_id="section-atlas",
                heading_path=["Atlas", "Caching"],
                locator="p. 2",
                retrieval_score=0.96,
                retrieval_rank=2,
            ),
            RetrievedCandidate(
                doc_id="doc-beacon",
                chunk_id="chunk-beacon",
                section_id="section-beacon",
                heading_path=["Beacon", "Caching"],
                locator="p. 4",
                retrieval_score=0.95,
                retrieval_rank=3,
            ),
        ],
        policy=QueryPolicyDefaults.build(),
    )

    assert len(result.evidence_sets) == 1
    assert [unit.candidate.doc_id for unit in result.evidence_sets[0].evidence_units] == [
        "doc-atlas",
        "doc-beacon",
    ]
