from __future__ import annotations

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from doc_forge.persistence import SqlChunkRepository, SqlDocumentRepository, SqlSectionRepository
from tests.persistence.conftest import ChunkFactory, PersistedDocumentFactory, SectionFactory

pytestmark = pytest.mark.persistence


def test_no_section_without_document_possible(
    sql_engine: sa.Engine,
    section_factory: SectionFactory,
) -> None:
    sections = SqlSectionRepository(sql_engine)

    with pytest.raises(IntegrityError):
        sections.save([section_factory(doc_id="missing-doc", section_id="section-1")])


def test_no_chunk_without_document_possible(
    sql_engine: sa.Engine,
    chunk_factory: ChunkFactory,
) -> None:
    chunks = SqlChunkRepository(sql_engine)

    with pytest.raises(IntegrityError):
        chunks.save([chunk_factory(doc_id="missing-doc", chunk_id="chunk-1")])


def test_no_orphan_chunks_possible(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
    chunk_factory: ChunkFactory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    documents.create(persisted_document_factory())

    with pytest.raises(IntegrityError):
        chunks.save(
            [
                chunk_factory(
                    doc_id="doc-1",
                    chunk_id="broken-chunk",
                    section_id="missing-section",
                    heading_path=["Broken"],
                )
            ],
        )


def test_chunk_cannot_reference_section_from_another_document(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
    section_factory: SectionFactory,
    chunk_factory: ChunkFactory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections = SqlSectionRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    documents.create(persisted_document_factory(doc_id="doc-1"))
    documents.create(persisted_document_factory(doc_id="doc-2"))
    sections.save([section_factory(doc_id="doc-2", section_id="doc-2-section-1")])

    with pytest.raises(IntegrityError):
        chunks.save(
            [
                chunk_factory(
                    doc_id="doc-1",
                    chunk_id="broken-cross-link",
                    section_id="doc-2-section-1",
                )
            ],
        )


def test_section_cannot_reference_parent_from_another_document(
    sql_engine: sa.Engine,
    persisted_document_factory: PersistedDocumentFactory,
    section_factory: SectionFactory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections = SqlSectionRepository(sql_engine)
    documents.create(persisted_document_factory(doc_id="doc-1"))
    documents.create(persisted_document_factory(doc_id="doc-2"))
    sections.save([section_factory(doc_id="doc-2", section_id="doc-2-parent")])

    with pytest.raises(IntegrityError):
        sections.save(
            [
                section_factory(
                    doc_id="doc-1",
                    section_id="doc-1-child",
                    parent_section_id="doc-2-parent",
                    heading_path=["Broken", "Child"],
                    depth=1,
                )
            ],
        )
