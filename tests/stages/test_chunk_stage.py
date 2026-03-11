from __future__ import annotations

from datetime import UTC, datetime

from parity._contracts import ProcessingStatus, Section, SourceType
from parity.artifacts import FilesystemArtifactStore, NormalizedArtifact, NormalizedArtifactBlock
from parity.chunking import ChunkingService
from parity.persistence import (
    DocumentJobStage,
    PersistedDocument,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlLifecycleEventRepository,
    SqlSectionRepository,
)
from parity.stages.chunk import ChunkDocumentStage


def test_chunk_stage_persists_chunks_and_marks_document_chunked(
    sql_engine,
    tmp_path,
    document_job_factory,
) -> None:
    artifact_store = FilesystemArtifactStore(tmp_path / "artifacts")
    documents = SqlDocumentRepository(sql_engine)
    sections = SqlSectionRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    lifecycle_events = SqlLifecycleEventRepository(sql_engine)
    doc_id = "doc-chunk-1"
    documents.create(
        PersistedDocument(
            doc_id=doc_id,
            workspace_id="ws-1",
            source_type=SourceType.MARKDOWN,
            title="Chunk Notes",
            filename="chunk.md",
            uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
            ingest_status=ProcessingStatus.NORMALIZED,
            storage_ref="file:///tmp/chunk.md",
            raw_storage_path="raw/ws-1/doc-chunk-1/source.md",
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
                    text="Consensus needs stable leadership.",
                    order_index=0,
                    heading_path=["Overview"],
                    source_start_offset=0,
                    source_end_offset=35,
                ),
                NormalizedArtifactBlock(
                    kind="code",
                    text="```py\nprint('hi')\n```",
                    order_index=1,
                    heading_path=["Overview"],
                    source_start_offset=36,
                    source_end_offset=57,
                ),
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

    stage = ChunkDocumentStage(
        documents=documents,
        sections=sections,
        chunks=chunks,
        lifecycle_events=lifecycle_events,
        artifact_store=artifact_store,
        service=ChunkingService(),
    )
    stage.run(
        document_job_factory(
            doc_id=doc_id,
            job_id="job-chunk",
            target_stage=DocumentJobStage.CHUNK,
        )
    )

    stored = chunks.list_for_document(doc_id)
    assert len(stored) == 2
    assert all(chunk.section_id == f"{doc_id}:section:0" for chunk in stored)
    assert stored[1].debug_metadata == {"token_count": "3"}
    assert documents.get(doc_id).ingest_status is ProcessingStatus.CHUNKED
    assert lifecycle_events.list_for_document(doc_id)[-1].to_status is ProcessingStatus.CHUNKED
