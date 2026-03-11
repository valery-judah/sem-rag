from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from parity._contracts import Chunk
from parity.persistence import (
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlSectionRepository,
)

pytestmark = pytest.mark.persistence


def test_chunk_round_trip_preserves_section_link(
    sql_engine,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections_repo = SqlSectionRepository(sql_engine)
    chunks_repo = SqlChunkRepository(sql_engine)
    document = persisted_document_factory()
    section = section_factory(doc_id=document.doc_id, section_id="doc-1-section-2")
    chunks = [
        chunk_factory(
            doc_id=document.doc_id,
            chunk_id="doc-1-chunk-1",
            section_id=section.section_id,
            lineage={"chunker_version": "v1"},
            debug_metadata={"token_count": "9"},
        ),
        chunk_factory(
            doc_id=document.doc_id,
            chunk_id="doc-1-chunk-2",
            section_id=section.section_id,
            ordinal=1,
            text="Leader election limits conflicting writes during failover.",
            source_start_offset=66,
            source_end_offset=120,
            page_start=None,
            page_end=None,
        ),
    ]
    documents.create(document)
    sections_repo.save([section])

    chunks_repo.save(chunks)

    loaded = chunks_repo.list_for_document(document.doc_id)

    assert loaded == chunks
    assert isinstance(loaded[0], Chunk)


def test_chunk_ordering_round_trip_is_stable(
    sql_engine,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections_repo = SqlSectionRepository(sql_engine)
    chunks_repo = SqlChunkRepository(sql_engine)
    document = persisted_document_factory()
    section = section_factory(doc_id=document.doc_id, section_id="doc-1-section-1")
    documents.create(document)
    sections_repo.save([section])
    chunks_repo.save(
        [
            chunk_factory(
                doc_id=document.doc_id,
                chunk_id="chunk-2",
                section_id=section.section_id,
                ordinal=1,
            ),
            chunk_factory(
                doc_id=document.doc_id,
                chunk_id="chunk-1",
                section_id=section.section_id,
                ordinal=0,
            ),
        ],
    )

    loaded = chunks_repo.list_for_document(document.doc_id)

    assert [chunk.chunk_id for chunk in loaded] == ["chunk-1", "chunk-2"]


def test_optional_chunk_fields_round_trip_as_none(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks_repo = SqlChunkRepository(sql_engine)
    document = persisted_document_factory()
    chunk = chunk_factory(
        doc_id=document.doc_id,
        heading_path=["Appendix"],
        section_id=None,
        page_start=None,
        page_end=None,
        source_start_offset=None,
        source_end_offset=None,
        lineage=None,
        debug_metadata=None,
    )
    documents.create(document)

    chunks_repo.save([chunk])

    loaded = chunks_repo.list_for_document(document.doc_id)[0]

    assert loaded.section_id is None
    assert loaded.lineage is None
    assert loaded.debug_metadata is None


def test_replace_for_document_removes_prior_chunks(
    sql_engine,
    persisted_document_factory,
    section_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    sections_repo = SqlSectionRepository(sql_engine)
    chunks_repo = SqlChunkRepository(sql_engine)
    document = persisted_document_factory()
    section = section_factory(doc_id=document.doc_id, section_id="doc-1-section-1")
    documents.create(document)
    sections_repo.save([section])
    chunks_repo.save(
        [
            chunk_factory(
                doc_id=document.doc_id,
                chunk_id="old-chunk-1",
                section_id=section.section_id,
            ),
            chunk_factory(
                doc_id=document.doc_id,
                chunk_id="old-chunk-2",
                section_id=section.section_id,
                ordinal=1,
            ),
        ],
    )

    replacement = [
        chunk_factory(
            doc_id=document.doc_id,
            chunk_id="new-chunk-1",
            section_id=section.section_id,
            heading_path=["Replacement"],
            text="Replacement chunk.",
        )
    ]
    chunks_repo.replace_for_document(document.doc_id, replacement)

    assert chunks_repo.list_for_document(document.doc_id) == replacement


def test_replace_for_document_rejects_cross_document_chunks(
    sql_engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks_repo = SqlChunkRepository(sql_engine)
    document = persisted_document_factory()
    documents.create(document)

    with pytest.raises(ValueError, match="target document"):
        chunks_repo.replace_for_document(
            document.doc_id,
            [chunk_factory(doc_id="doc-2", chunk_id="doc-2-chunk-1")],
        )


def test_chunk_save_requires_existing_document(
    sql_engine,
    chunk_factory,
) -> None:
    chunks_repo = SqlChunkRepository(sql_engine)

    with pytest.raises(IntegrityError):
        chunks_repo.save([chunk_factory(doc_id="missing-doc", chunk_id="chunk-1")])
