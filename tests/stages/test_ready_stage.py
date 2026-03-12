from __future__ import annotations

from datetime import UTC, datetime

import pytest

from doc_forge.artifacts import FilesystemArtifactStore, NormalizedArtifact, NormalizedArtifactBlock
from doc_forge.corpus import Chunk, Section, SourceType
from doc_forge.indexing import DeterministicEmbeddingAdapter, SqlVectorStore
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.lifecycle.readiness import ReadinessService
from doc_forge.persistence import (
    DocumentJobStage,
    PersistedDocument,
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlLifecycleEventRepository,
    SqlSectionRepository,
)
from doc_forge.stages.base import StageExecutionError
from doc_forge.stages.ready import ReadyDocumentStage


def test_ready_stage_requires_provenance_and_smoke_query(
    sql_engine,
    tmp_path,
    document_job_factory,
) -> None:
    artifact_store = FilesystemArtifactStore(tmp_path / "artifacts")
    documents = SqlDocumentRepository(sql_engine)
    sections = SqlSectionRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    lifecycle_events = SqlLifecycleEventRepository(sql_engine)
    index_entries = SqlIndexEntryRepository(sql_engine)
    chunk_embeddings = SqlChunkEmbeddingRepository(sql_engine)
    doc_id = "doc-ready-1"
    documents.create(
        PersistedDocument(
            doc_id=doc_id,
            workspace_id="ws-1",
            source_type=SourceType.MARKDOWN,
            title="Ready Notes",
            filename="ready.md",
            uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
            ingest_status=ProcessingStatus.INDEXED,
            storage_ref="file:///tmp/ready.md",
            raw_storage_path="raw/ws-1/doc-ready-1/source.md",
        )
    )
    artifact_store.write_normalized(
        workspace_id="ws-1",
        artifact=NormalizedArtifact(
            doc_id=doc_id,
            source_type=SourceType.MARKDOWN,
            normalizer_version="markdown-v1",
            blocks=[
                NormalizedArtifactBlock(
                    kind="paragraph",
                    text="Consensus keeps nodes aligned.",
                    order_index=0,
                    heading_path=["Overview"],
                )
            ],
        ),
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
                text="Consensus keeps nodes aligned.",
                ordinal=0,
                heading_path=["Overview"],
            )
        ],
    )
    vector_store = SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=index_entries,
        chunk_embeddings=chunk_embeddings,
    )
    vector_store.publish_document(doc_id=doc_id, chunks=chunks.list_for_document(doc_id))

    stage = ReadyDocumentStage(
        documents=documents,
        lifecycle_events=lifecycle_events,
        readiness=ReadinessService(
            documents=documents,
            sections=sections,
            chunks=chunks,
            index_entries=index_entries,
            artifact_store=artifact_store,
            vector_store=vector_store,
        ),
    )
    stage.run(
        document_job_factory(
            doc_id=doc_id,
            job_id="job-ready",
            target_stage=DocumentJobStage.READY_CHECK,
        )
    )

    document = documents.get(doc_id)
    assert document is not None
    assert document.ingest_status is ProcessingStatus.READY
    assert lifecycle_events.list_for_document(doc_id)[-1].to_status is ProcessingStatus.READY


def test_ready_stage_rejects_chunks_without_section_links(
    sql_engine,
    tmp_path,
    document_job_factory,
) -> None:
    artifact_store = FilesystemArtifactStore(tmp_path / "artifacts")
    documents = SqlDocumentRepository(sql_engine)
    sections = SqlSectionRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    index_entries = SqlIndexEntryRepository(sql_engine)
    chunk_embeddings = SqlChunkEmbeddingRepository(sql_engine)
    doc_id = "doc-ready-fail"
    documents.create(
        PersistedDocument(
            doc_id=doc_id,
            workspace_id="ws-1",
            source_type=SourceType.MARKDOWN,
            title="Broken Ready",
            filename="broken.md",
            uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
            ingest_status=ProcessingStatus.INDEXED,
            storage_ref="file:///tmp/broken.md",
            raw_storage_path="raw/ws-1/doc-ready-fail/source.md",
        )
    )
    artifact_store.write_normalized(
        workspace_id="ws-1",
        artifact=NormalizedArtifact(
            doc_id=doc_id,
            source_type=SourceType.MARKDOWN,
            normalizer_version="markdown-v1",
            blocks=[NormalizedArtifactBlock(kind="paragraph", text="text", order_index=0)],
        ),
    )
    sections.replace_for_document(
        doc_id,
        [
            Section(
                section_id=f"{doc_id}:section:0", doc_id=doc_id, heading_path=["Overview"], depth=0
            )
        ],
    )
    chunks.replace_for_document(
        doc_id,
        [
            Chunk(
                chunk_id=f"{doc_id}:chunk:0",
                doc_id=doc_id,
                section_id=None,
                text="Missing provenance",
                ordinal=0,
                heading_path=["Overview"],
            )
        ],
    )
    vector_store = SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=index_entries,
        chunk_embeddings=chunk_embeddings,
    )
    vector_store.publish_document(doc_id=doc_id, chunks=chunks.list_for_document(doc_id))

    stage = ReadyDocumentStage(
        documents=documents,
        lifecycle_events=SqlLifecycleEventRepository(sql_engine),
        readiness=ReadinessService(
            documents=documents,
            sections=sections,
            chunks=chunks,
            index_entries=index_entries,
            artifact_store=artifact_store,
            vector_store=vector_store,
        ),
    )

    with pytest.raises(StageExecutionError, match="broken_chunk_section_linkage"):
        stage.run(
            document_job_factory(
                doc_id=doc_id,
                job_id="job-ready-fail",
                target_stage=DocumentJobStage.READY_CHECK,
            )
        )
