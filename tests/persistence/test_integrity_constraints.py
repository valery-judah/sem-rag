from __future__ import annotations

import sqlite3

import pytest

from parity.persistence import save_chunks, save_document, save_sections

pytestmark = pytest.mark.persistence


def test_no_section_without_document_possible(
    conn: sqlite3.Connection,
    section_factory,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        save_sections(conn, [section_factory(doc_id="missing-doc", section_id="section-1")])


def test_no_chunk_without_document_possible(
    conn: sqlite3.Connection,
    chunk_factory,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        save_chunks(conn, [chunk_factory(doc_id="missing-doc", chunk_id="chunk-1")])


def test_no_orphan_chunks_possible(
    conn: sqlite3.Connection,
    document_factory,
    chunk_factory,
) -> None:
    save_document(conn, document_factory())

    with pytest.raises(sqlite3.IntegrityError):
        save_chunks(
            conn,
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
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
    chunk_factory,
) -> None:
    save_document(conn, document_factory(doc_id="doc-1"))
    save_document(conn, document_factory(doc_id="doc-2"))
    save_sections(
        conn,
        [section_factory(doc_id="doc-2", section_id="doc-2-section-1")],
    )

    with pytest.raises(sqlite3.IntegrityError):
        save_chunks(
            conn,
            [
                chunk_factory(
                    doc_id="doc-1",
                    chunk_id="broken-cross-link",
                    section_id="doc-2-section-1",
                )
            ],
        )


def test_section_cannot_reference_parent_from_another_document(
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
) -> None:
    save_document(conn, document_factory(doc_id="doc-1"))
    save_document(conn, document_factory(doc_id="doc-2"))
    save_sections(
        conn,
        [section_factory(doc_id="doc-2", section_id="doc-2-parent")],
    )

    with pytest.raises(sqlite3.IntegrityError):
        save_sections(
            conn,
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
