from __future__ import annotations

from datetime import UTC, datetime

import pytest

from parity._contracts import Chunk, ProcessingStatus, Section, SourceType
from parity.indexing import ChunkEmbedding, DeterministicEmbeddingAdapter, IndexEntry, SqlVectorStore
from parity.persistence import (
    DocumentJobStage,
    PersistedDocument,
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlLifecycleEventRepository,
    SqlSectionRepository,
)
from parity.stages.base import StageExecutionError
from parity.stages.index import IndexDocumentStage


def test_index_stage_publishes_all_chunks(sql_engine, document_job_factory) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    sections = SqlSectionRepository(sql_engine)
    lifecycle_events = SqlLifecycleEventRepository(sql_engine)
    index_entries = SqlIndexEntryRepository(sql_engine)
    chunk_embeddings = SqlChunkEmbeddingRepository(sql_engine)
    doc_id = "doc-index-1"
    documents.create(
        PersistedDocument(
            doc_id=doc_id,
            workspace_id="ws-1",
            source_type=SourceType.MARKDOWN,
            title="Index Notes",
            filename="index.md",
            uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
            ingest_status=ProcessingStatus.CHUNKED,
            storage_ref="file:///tmp/index.md",
            raw_storage_path="raw/ws-1/doc-index-1/source.md",
        )
    )
    sections.replace_for_document(
        doc_id,
        [
            Section(
                section_id=f"{doc_id}:section:0",
                doc_id=doc_id,
                heading_path=["Overview"],
                depth=0,
                heading_text="Overview",
            )
        ],
    )
    chunks.replace_for_document(
        doc_id,
        [
            Chunk(
                chunk_id=f"{doc_id}:chunk:0",
                doc_id=doc_id,
                section_id=f"{doc_id}:section:0",
                text="Consensus keeps replicas aligned.",
                ordinal=0,
                heading_path=["Overview"],
            ),
            Chunk(
                chunk_id=f"{doc_id}:chunk:1",
                doc_id=doc_id,
                section_id=f"{doc_id}:section:0",
                text="Retries clear derived artifacts.",
                ordinal=1,
                heading_path=["Overview"],
            ),
        ],
    )

    stage = IndexDocumentStage(
        documents=documents,
        chunks=chunks,
        lifecycle_events=lifecycle_events,
        vector_store=SqlVectorStore(
            engine=sql_engine,
            embedding_adapter=DeterministicEmbeddingAdapter(),
            index_entries=index_entries,
            chunk_embeddings=chunk_embeddings,
        ),
    )
    stage.run(
        document_job_factory(
            doc_id=doc_id,
            job_id="job-index",
            target_stage=DocumentJobStage.INDEX,
        )
    )

    assert len(index_entries.list_for_document(doc_id)) == 2
    assert len(chunk_embeddings.list_for_document(doc_id)) == 2
    assert documents.get(doc_id).ingest_status is ProcessingStatus.INDEXED
    assert lifecycle_events.list_for_document(doc_id)[-1].to_status is ProcessingStatus.INDEXED


class _FailingVectorStore:
    def __init__(self, *, index_entries, chunk_embeddings) -> None:
        self._index_entries = index_entries
        self._chunk_embeddings = chunk_embeddings

    def publish_document(self, *, doc_id: str, chunks: list[Chunk]) -> list[IndexEntry]:
        published_at = datetime(2026, 3, 11, tzinfo=UTC)
        self._chunk_embeddings.replace_for_document(
            doc_id,
            [
                ChunkEmbedding(
                    chunk_id=chunks[0].chunk_id,
                    doc_id=doc_id,
                    embedding_model="failing-test",
                    embedding_vector=[0.5, 0.25],
                    created_at=published_at,
                )
            ],
        )
        self._index_entries.replace_for_document(
            doc_id,
            [
                IndexEntry(
                    chunk_id=chunks[0].chunk_id,
                    doc_id=doc_id,
                    index_backend="failing-test",
                    index_key=chunks[0].chunk_id,
                    index_version="v1",
                    published_at=published_at,
                )
            ],
        )
        raise RuntimeError("vector backend write failed")


def test_index_stage_cleans_up_partial_publication_on_failure(
    sql_engine,
    document_job_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    sections = SqlSectionRepository(sql_engine)
    lifecycle_events = SqlLifecycleEventRepository(sql_engine)
    index_entries = SqlIndexEntryRepository(sql_engine)
    chunk_embeddings = SqlChunkEmbeddingRepository(sql_engine)
    doc_id = "doc-index-failure"
    documents.create(
        PersistedDocument(
            doc_id=doc_id,
            workspace_id="ws-1",
            source_type=SourceType.MARKDOWN,
            title="Index Failure",
            filename="index-failure.md",
            uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
            ingest_status=ProcessingStatus.CHUNKED,
            storage_ref="file:///tmp/index-failure.md",
            raw_storage_path="raw/ws-1/doc-index-failure/source.md",
        )
    )
    sections.replace_for_document(
        doc_id,
        [
            Section(
                section_id=f"{doc_id}:section:0",
                doc_id=doc_id,
                heading_path=["Overview"],
                depth=0,
                heading_text="Overview",
            )
        ],
    )
    chunks.replace_for_document(
        doc_id,
        [
            Chunk(
                chunk_id=f"{doc_id}:chunk:0",
                doc_id=doc_id,
                section_id=f"{doc_id}:section:0",
                text="Consensus keeps replicas aligned.",
                ordinal=0,
                heading_path=["Overview"],
            )
        ],
    )

    stage = IndexDocumentStage(
        documents=documents,
        chunks=chunks,
        lifecycle_events=lifecycle_events,
        vector_store=_FailingVectorStore(
            index_entries=index_entries,
            chunk_embeddings=chunk_embeddings,
        ),
        index_entries=index_entries,
        chunk_embeddings=chunk_embeddings,
    )

    with pytest.raises(StageExecutionError) as exc_info:
        stage.run(
            document_job_factory(
                doc_id=doc_id,
                job_id="job-index-failure",
                target_stage=DocumentJobStage.INDEX,
            )
        )

    assert exc_info.value.error_code == "index_failed"
    assert index_entries.list_for_document(doc_id) == []
    assert chunk_embeddings.list_for_document(doc_id) == []
