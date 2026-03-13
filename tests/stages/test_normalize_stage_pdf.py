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
    db_url = f"sqlite+pysqlite:///{tmp_path / 'normalize-pdf.db'}"
    apply_migrations(db_url)
    engine = sa.create_engine(db_url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
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


def _persist_extracting_pdf_document(
    *,
    documents,
    artifact_store: FilesystemArtifactStore,
    pages: list[ExtractedArtifactPage],
    doc_id: str = "doc-pdf-norm-1",
) -> str:
    documents.create(
        PersistedDocument(
            doc_id=doc_id,
            workspace_id="ws-1",
            source_type=SourceType.PDF,
            title="PDF Doc",
            filename="doc.pdf",
            uploaded_at=datetime(2026, 3, 11, tzinfo=UTC),
            ingest_status=ProcessingStatus.EXTRACTING,
            storage_ref="file:///tmp/doc.pdf",
            checksum="sha256:test",
            raw_storage_path=f"raw/ws-1/{doc_id}/source.pdf",
            created_at=datetime(2026, 3, 11, tzinfo=UTC),
            updated_at=datetime(2026, 3, 11, tzinfo=UTC),
        )
    )
    artifact_store.write_extracted(
        workspace_id="ws-1",
        artifact=ExtractedArtifact(
            doc_id=doc_id,
            source_type=SourceType.PDF,
            extractor_version="pdf-v1",
            pages=pages,
        ),
    )
    return doc_id


def test_pdf_normalize_preserves_page_transition_blocks(
    normalize_stage: NormalizeDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_extracting_pdf_document(
        documents=documents,
        artifact_store=artifact_store,
        pages=[
            ExtractedArtifactPage(
                page_number=1,
                blocks=[ExtractedArtifactBlock(text="INTRODUCTION", order_index=0)],
            ),
            ExtractedArtifactPage(
                page_number=2,
                blocks=[ExtractedArtifactBlock(text="Second page paragraph", order_index=0)],
            ),
        ],
    )

    artifact = normalize_stage.run(doc_id)

    assert artifact.blocks[1].kind == "page_break"
    assert artifact.blocks[1].page_number == 2


def test_pdf_normalize_promotes_heading_only_above_confidence_threshold(
    normalize_stage: NormalizeDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_extracting_pdf_document(
        documents=documents,
        artifact_store=artifact_store,
        pages=[
            ExtractedArtifactPage(
                page_number=1,
                blocks=[ExtractedArtifactBlock(text="1 INTRODUCTION", order_index=0)],
            )
        ],
    )

    artifact = normalize_stage.run(doc_id)

    assert artifact.blocks[0].kind == "heading"
    assert artifact.blocks[0].heading_level == 1


def test_pdf_normalize_keeps_uncertain_heading_as_paragraph(
    normalize_stage: NormalizeDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_extracting_pdf_document(
        documents=documents,
        artifact_store=artifact_store,
        pages=[
            ExtractedArtifactPage(
                page_number=1,
                blocks=[
                    ExtractedArtifactBlock(
                        text="this looks like a sentence without strong heading cues.",
                        order_index=0,
                    )
                ],
            )
        ],
    )

    artifact = normalize_stage.run(doc_id)

    assert artifact.blocks[0].kind == "paragraph"
    assert artifact.blocks[0].heading_level is None


def test_pdf_normalize_allows_synthetic_structure_fallback(
    normalize_stage: NormalizeDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_extracting_pdf_document(
        documents=documents,
        artifact_store=artifact_store,
        pages=[
            ExtractedArtifactPage(
                page_number=1,
                blocks=[ExtractedArtifactBlock(text="plain paragraph text", order_index=0)],
            )
        ],
    )

    artifact = normalize_stage.run(doc_id)

    assert artifact.meta["section_fallback"] == "synthetic_required"


def test_pdf_normalize_never_claims_unrecovered_layout_semantics(
    normalize_stage: NormalizeDocumentStage,
    repositories,
    artifact_store: FilesystemArtifactStore,
) -> None:
    documents, _ = repositories
    doc_id = _persist_extracting_pdf_document(
        documents=documents,
        artifact_store=artifact_store,
        pages=[
            ExtractedArtifactPage(
                page_number=1,
                blocks=[ExtractedArtifactBlock(text="plain paragraph text", order_index=0)],
            )
        ],
    )

    artifact = normalize_stage.run(doc_id)

    assert all(block.kind in {"paragraph", "page_break", "heading"} for block in artifact.blocks)
    assert all(block.meta is None or "layout" not in block.meta for block in artifact.blocks)
