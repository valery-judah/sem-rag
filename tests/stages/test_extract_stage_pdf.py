from __future__ import annotations

from datetime import UTC, datetime

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


class _FakePdfPage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakePdfReader:
    def __init__(self, pages: list[str]) -> None:
        self.pages = [_FakePdfPage(text) for text in pages]


@pytest.fixture
def sql_engine(tmp_path):
    db_url = f"sqlite+pysqlite:///{tmp_path / 'extract-pdf.db'}"
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
def extract_stage(sql_engine, repositories, artifact_store: FilesystemArtifactStore):
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


def _persist_pdf_document(
    *,
    documents,
    artifact_store: FilesystemArtifactStore,
    content: bytes = b"%PDF-1.7\nfake",
    doc_id: str = "doc-pdf-1",
) -> str:
    ref = artifact_store.write_raw(
        workspace_id="ws-1",
        doc_id=doc_id,
        source_type=SourceType.PDF,
        content=content,
    )
    documents.create(
        PersistedDocument(
            doc_id=doc_id,
            workspace_id="ws-1",
            source_type=SourceType.PDF,
            title="PDF Doc",
            filename="doc.pdf",
            uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
            ingest_status=ProcessingStatus.REGISTERED,
            storage_ref=artifact_store.raw_path(
                workspace_id="ws-1",
                doc_id=doc_id,
                source_type=SourceType.PDF,
            ).as_uri(),
            checksum="sha256:test",
            raw_storage_path=ref.relative_path,
            created_at=datetime(2026, 3, 11, tzinfo=UTC),
            updated_at=datetime(2026, 3, 11, tzinfo=UTC),
        )
    )
    return doc_id


def test_pdf_extract_preserves_page_boundaries(
    extract_stage: ExtractDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    documents, _ = repositories
    doc_id = _persist_pdf_document(documents=documents, artifact_store=artifact_store)
    monkeypatch.setattr(
        "doc_forge.extractors.pdf.PdfReader",
        lambda _: _FakePdfReader(
            [
                "INTRODUCTION\n\nConsensus keeps nodes aligned.",
                "OPERATIONS\n\nOperators inspect failures.",
            ]
        ),
    )

    artifact = extract_stage.run(doc_id)

    assert [page.page_number for page in artifact.pages] == [1, 2]
    assert artifact.pages[0].blocks[0].text == "INTRODUCTION"
    assert artifact.pages[1].blocks[1].text == "Operators inspect failures."


def test_pdf_extract_records_warnings_for_sparse_text_layer(
    extract_stage: ExtractDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    documents, _ = repositories
    doc_id = _persist_pdf_document(documents=documents, artifact_store=artifact_store)
    monkeypatch.setattr(
        "doc_forge.extractors.pdf.PdfReader",
        lambda _: _FakePdfReader(["SHORT"]),
    )

    artifact = extract_stage.run(doc_id)

    assert artifact.warnings == ["page 1 has a sparse text layer"]


def test_pdf_extract_rejects_no_recoverable_text_layer(
    extract_stage: ExtractDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    documents, _ = repositories
    doc_id = _persist_pdf_document(documents=documents, artifact_store=artifact_store)
    monkeypatch.setattr(
        "doc_forge.extractors.pdf.PdfReader",
        lambda _: _FakePdfReader(["", "   "]),
    )

    with pytest.raises(DocumentExtractionError):
        extract_stage.run(doc_id)


def test_pdf_extract_fails_on_malformed_pdf(
    extract_stage: ExtractDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_pdf_document(
        documents=documents,
        artifact_store=artifact_store,
        content=b"%PDF-1.7\nmalformed",
    )

    with pytest.raises(DocumentExtractionError):
        extract_stage.run(doc_id)


def test_extract_stage_does_not_mark_extracted_without_artifact(
    extract_stage: ExtractDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    documents, _ = repositories
    doc_id = _persist_pdf_document(documents=documents, artifact_store=artifact_store)
    monkeypatch.setattr(
        "doc_forge.extractors.pdf.PdfReader",
        lambda _: _FakePdfReader(["Meaningful PDF text for extraction."]),
    )

    def _boom(*args, **kwargs):
        del args, kwargs
        raise OSError("disk full")

    monkeypatch.setattr(artifact_store, "write_extracted", _boom)

    with pytest.raises(DocumentExtractionError):
        extract_stage.run(doc_id)

    stored = documents.get(doc_id)
    assert stored is not None
    assert stored.ingest_status is ProcessingStatus.REGISTERED
    assert not artifact_store.extracted_path(workspace_id="ws-1", doc_id=doc_id).exists()
