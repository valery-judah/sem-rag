from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import event

from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.corpus import SourceType
from doc_forge.extractors import ExtractorRegistry, MarkdownExtractor, PdfExtractor
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.persistence import (
    PersistedDocument,
    SqlDocumentRepository,
    SqlLifecycleEventRepository,
    apply_migrations,
)
from doc_forge.stages.extract import DocumentExtractionError, ExtractDocumentStage


@pytest.fixture
def sql_engine(tmp_path: Path) -> Iterator[sa.Engine]:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'extract-markdown.db'}"
    apply_migrations(db_url)
    engine = sa.create_engine(db_url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(
            dbapi_connection: sa.Connection, connection_record: sa.Connection
        ) -> None:
            del connection_record
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def artifact_store(tmp_path: Path) -> FilesystemArtifactStore:
    return FilesystemArtifactStore(tmp_path / "artifacts")


@pytest.fixture
def repositories(
    sql_engine: sa.Engine,
) -> tuple[SqlDocumentRepository, SqlLifecycleEventRepository]:
    return SqlDocumentRepository(sql_engine), SqlLifecycleEventRepository(sql_engine)


@pytest.fixture
def extract_stage(
    sql_engine: sa.Engine,
    repositories: tuple[SqlDocumentRepository, SqlLifecycleEventRepository],
    artifact_store: FilesystemArtifactStore,
) -> ExtractDocumentStage:
    documents, lifecycle_events = repositories
    return ExtractDocumentStage(
        engine=sql_engine,
        documents=documents,
        lifecycle_events=lifecycle_events,
        artifact_store=artifact_store,
        extractors=ExtractorRegistry(
            markdown=MarkdownExtractor(),
            pdf=PdfExtractor(),
        ),
    )


def _persist_markdown_document(
    *,
    documents: SqlDocumentRepository,
    artifact_store: FilesystemArtifactStore,
    doc_id: str = "doc-md-1",
    content: bytes = b"# Overview\n\nFirst paragraph.\n\n```py\nprint('hi')\n```\n",
) -> str:
    ref = artifact_store.write_raw(
        workspace_id="ws-1",
        doc_id=doc_id,
        source_type=SourceType.MARKDOWN,
        content=content,
    )
    documents.create(
        PersistedDocument(
            doc_id=doc_id,
            workspace_id="ws-1",
            source_type=SourceType.MARKDOWN,
            title="Markdown Doc",
            filename="doc.md",
            uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
            ingest_status=ProcessingStatus.REGISTERED,
            storage_ref=artifact_store.raw_path(
                workspace_id="ws-1",
                doc_id=doc_id,
                source_type=SourceType.MARKDOWN,
            ).as_uri(),
            checksum="sha256:test",
            raw_storage_path=ref.relative_path,
            created_at=datetime(2026, 3, 11, tzinfo=UTC),
            updated_at=datetime(2026, 3, 11, tzinfo=UTC),
        )
    )
    return doc_id


def test_markdown_extract_preserves_order_exactly(
    extract_stage: ExtractDocumentStage,
    repositories: tuple[SqlDocumentRepository, SqlLifecycleEventRepository],
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_markdown_document(documents=documents, artifact_store=artifact_store)

    artifact = extract_stage.run(doc_id)

    assert [block.text for block in artifact.pages[0].blocks] == [
        "# Overview",
        "First paragraph.",
        "```py\nprint('hi')\n```",
    ]


def test_markdown_extract_preserves_code_fences(
    extract_stage: ExtractDocumentStage,
    repositories: tuple[SqlDocumentRepository, SqlLifecycleEventRepository],
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_markdown_document(documents=documents, artifact_store=artifact_store)

    artifact = extract_stage.run(doc_id)

    code_block = artifact.pages[0].blocks[2]
    assert code_block.kind == "code"
    assert code_block.text.startswith("```py")
    assert code_block.text.endswith("```")


def test_markdown_extract_records_offsets_when_available(
    extract_stage: ExtractDocumentStage,
    repositories: tuple[SqlDocumentRepository, SqlLifecycleEventRepository],
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    content = b"# Title\n\nParagraph text.\n"
    doc_id = _persist_markdown_document(
        documents=documents,
        artifact_store=artifact_store,
        content=content,
    )

    artifact = extract_stage.run(doc_id)
    first_block, second_block = artifact.pages[0].blocks

    assert first_block.source_start_offset == 0
    assert first_block.source_end_offset == len("# Title")
    assert first_block.source_end_offset is not None
    assert second_block.source_start_offset is not None
    assert second_block.source_end_offset is not None
    assert second_block.source_start_offset > first_block.source_end_offset
    assert second_block.source_end_offset == second_block.source_start_offset + len(
        "Paragraph text."
    )


def test_extract_stage_persists_extracted_artifact_before_advance(
    extract_stage: ExtractDocumentStage,
    repositories: tuple[SqlDocumentRepository, SqlLifecycleEventRepository],
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, lifecycle_events = repositories
    doc_id = _persist_markdown_document(documents=documents, artifact_store=artifact_store)

    extract_stage.run(doc_id)

    stored = documents.get(doc_id)
    assert stored is not None
    assert stored.ingest_status is ProcessingStatus.EXTRACTING
    assert artifact_store.read_extracted(workspace_id="ws-1", doc_id=doc_id).doc_id == doc_id
    assert lifecycle_events.list_for_document(doc_id)[-1].to_status is ProcessingStatus.EXTRACTING


def test_extract_stage_fails_on_decode_error(
    extract_stage: ExtractDocumentStage,
    repositories: tuple[SqlDocumentRepository, SqlLifecycleEventRepository],
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_markdown_document(
        documents=documents,
        artifact_store=artifact_store,
        content=b"\xff\xfe\x00broken",
    )

    with pytest.raises(DocumentExtractionError):
        extract_stage.run(doc_id)

    stored = documents.get(doc_id)
    assert stored is not None
    assert stored.ingest_status is ProcessingStatus.REGISTERED
    assert not artifact_store.extracted_path(workspace_id="ws-1", doc_id=doc_id).exists()
