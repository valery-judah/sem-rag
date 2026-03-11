from __future__ import annotations

import sqlite3

import pytest

from parity._contracts import Chunk
from parity.persistence import (
    list_chunks_by_document,
    replace_chunks_for_document,
    save_chunks,
    save_document,
    save_sections,
)

pytestmark = pytest.mark.persistence


def test_chunk_round_trip_preserves_section_link(
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
    chunk_factory,
) -> None:
    document = document_factory()
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
    save_document(conn, document)
    save_sections(conn, [section])

    save_chunks(conn, chunks)

    loaded = list_chunks_by_document(conn, document.doc_id)

    assert loaded == chunks
    assert isinstance(loaded[0], Chunk)


def test_chunk_ordering_round_trip_is_stable(
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
    chunk_factory,
) -> None:
    document = document_factory()
    section = section_factory(doc_id=document.doc_id, section_id="doc-1-section-1")
    save_document(conn, document)
    save_sections(conn, [section])
    save_chunks(
        conn,
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

    loaded = list_chunks_by_document(conn, document.doc_id)

    assert [chunk.chunk_id for chunk in loaded] == ["chunk-1", "chunk-2"]


def test_optional_chunk_fields_round_trip_as_none(
    conn: sqlite3.Connection,
    document_factory,
    chunk_factory,
) -> None:
    document = document_factory()
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
    save_document(conn, document)

    save_chunks(conn, [chunk])

    loaded = list_chunks_by_document(conn, document.doc_id)[0]

    assert loaded.section_id is None
    assert loaded.lineage is None
    assert loaded.debug_metadata is None


def test_replace_for_document_removes_prior_chunks(
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
    chunk_factory,
) -> None:
    document = document_factory()
    section = section_factory(doc_id=document.doc_id, section_id="doc-1-section-1")
    save_document(conn, document)
    save_sections(conn, [section])
    save_chunks(
        conn,
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
    replace_chunks_for_document(conn, document.doc_id, replacement)

    assert list_chunks_by_document(conn, document.doc_id) == replacement


def test_replace_for_document_rejects_cross_document_chunks(
    conn: sqlite3.Connection,
    document_factory,
    chunk_factory,
) -> None:
    document = document_factory()
    save_document(conn, document)

    with pytest.raises(ValueError, match="target document"):
        replace_chunks_for_document(
            conn,
            document.doc_id,
            [chunk_factory(doc_id="doc-2", chunk_id="doc-2-chunk-1")],
        )
