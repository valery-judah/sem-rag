from __future__ import annotations

from datetime import UTC, datetime

import pytest
import sqlalchemy as sa
from sqlalchemy import event

from doc_forge.artifacts import (
    ExtractedArtifact,
    ExtractedArtifactBlock,
    ExtractedArtifactPage,
    FilesystemArtifactStore,
)
from doc_forge.corpus import SourceType
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.normalizers import MarkdownNormalizer, NormalizerRegistry, PdfNormalizer
from doc_forge.persistence import (
    PersistedDocument,
    SqlDocumentRepository,
    SqlLifecycleEventRepository,
    apply_migrations,
)
from doc_forge.stages.normalize import NormalizeDocumentStage


@pytest.fixture
def sql_engine(tmp_path):
    db_url = f"sqlite+pysqlite:///{tmp_path / 'normalize-markdown.db'}"
    apply_migrations(db_url)
    engine = sa.create_engine(db_url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
            del connection_record
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def artifact_store(tmp_path) -> FilesystemArtifactStore:
    return FilesystemArtifactStore(tmp_path / "artifacts")


@pytest.fixture
def repositories(sql_engine):
    return SqlDocumentRepository(sql_engine), SqlLifecycleEventRepository(sql_engine)


@pytest.fixture
def normalize_stage(sql_engine, repositories, artifact_store: FilesystemArtifactStore):
    documents, lifecycle_events = repositories
    return NormalizeDocumentStage(
        engine=sql_engine,
        documents=documents,
        lifecycle_events=lifecycle_events,
        artifact_store=artifact_store,
        normalizers=NormalizerRegistry(
            markdown=MarkdownNormalizer(),
            pdf=PdfNormalizer(),
        ),
    )


def _persist_extracting_markdown_document(
    *,
    documents,
    artifact_store: FilesystemArtifactStore,
    doc_id: str = "doc-md-norm-1",
) -> str:
    documents.create(
        PersistedDocument(
            doc_id=doc_id,
            workspace_id="ws-1",
            source_type=SourceType.MARKDOWN,
            title="Markdown Doc",
            filename="doc.md",
            uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
            ingest_status=ProcessingStatus.EXTRACTING,
            storage_ref="file:///tmp/doc.md",
            checksum="sha256:test",
            raw_storage_path=f"raw/ws-1/{doc_id}/source.md",
            created_at=datetime(2026, 3, 11, tzinfo=UTC),
            updated_at=datetime(2026, 3, 11, tzinfo=UTC),
        )
    )
    artifact_store.write_extracted(
        workspace_id="ws-1",
        artifact=ExtractedArtifact(
            doc_id=doc_id,
            source_type=SourceType.MARKDOWN,
            extractor_version="markdown-v1",
            pages=[
                ExtractedArtifactPage(
                    page_number=1,
                    blocks=[
                        ExtractedArtifactBlock(
                            kind="heading",
                            text="# Overview",
                            order_index=0,
                            source_start_offset=0,
                            source_end_offset=10,
                        ),
                        ExtractedArtifactBlock(
                            kind="text",
                            text="- first bullet",
                            order_index=1,
                            source_start_offset=12,
                            source_end_offset=26,
                        ),
                        ExtractedArtifactBlock(
                            kind="code",
                            text="```py\nprint('hi')\n```",
                            order_index=2,
                            source_start_offset=28,
                            source_end_offset=49,
                        ),
                        ExtractedArtifactBlock(
                            kind="text",
                            text="Consensus needs stable leadership.",
                            order_index=3,
                            source_start_offset=51,
                            source_end_offset=86,
                        ),
                    ],
                )
            ],
        ),
    )
    return doc_id


def test_markdown_normalize_recovers_heading_blocks(
    normalize_stage: NormalizeDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_extracting_markdown_document(
        documents=documents,
        artifact_store=artifact_store,
    )

    artifact = normalize_stage.run(doc_id)

    assert artifact.blocks[0].kind == "heading"
    assert artifact.blocks[0].heading_level == 1
    assert artifact.blocks[0].heading_path == ["Overview"]


def test_markdown_normalize_preserves_code_block_boundaries(
    normalize_stage: NormalizeDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_extracting_markdown_document(
        documents=documents,
        artifact_store=artifact_store,
    )

    artifact = normalize_stage.run(doc_id)

    assert artifact.blocks[2].kind == "code"
    assert artifact.blocks[2].text == "```py\nprint('hi')\n```"


def test_markdown_normalize_preserves_paragraph_boundaries(
    normalize_stage: NormalizeDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_extracting_markdown_document(
        documents=documents,
        artifact_store=artifact_store,
    )

    artifact = normalize_stage.run(doc_id)

    assert artifact.blocks[1].kind == "list_item"
    assert artifact.blocks[3].kind == "paragraph"
    assert artifact.blocks[3].text == "Consensus needs stable leadership."


def test_markdown_normalize_persists_payload_before_status_advance(
    normalize_stage: NormalizeDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, lifecycle_events = repositories
    doc_id = _persist_extracting_markdown_document(
        documents=documents,
        artifact_store=artifact_store,
    )

    normalize_stage.run(doc_id)

    stored = documents.get(doc_id)
    assert stored is not None
    assert stored.ingest_status is ProcessingStatus.NORMALIZED
    assert artifact_store.read_normalized(workspace_id="ws-1", doc_id=doc_id).doc_id == doc_id
    assert lifecycle_events.list_for_document(doc_id)[-1].to_status is ProcessingStatus.NORMALIZED
