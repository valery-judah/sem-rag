from __future__ import annotations

import sqlite3

import pytest

from parity.persistence import (
    list_chunks_by_document,
    list_sections_by_document,
    replace_chunks_for_document,
    replace_sections_for_document,
    save_chunks,
    save_document,
    save_sections,
)

pytestmark = pytest.mark.persistence


def test_retry_from_normalized_replaces_sections_and_chunks(
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
    chunk_factory,
) -> None:
    document = document_factory()
    old_section = section_factory(doc_id=document.doc_id, section_id="old-section")
    new_section = section_factory(
        doc_id=document.doc_id,
        section_id="new-section",
        heading_path=["Replacement"],
        heading_text="Replacement",
    )
    save_document(conn, document)
    save_sections(conn, [old_section])
    save_chunks(
        conn,
        [
            chunk_factory(
                doc_id=document.doc_id,
                chunk_id="old-chunk",
                section_id=old_section.section_id,
            )
        ],
    )

    replace_sections_for_document(conn, document.doc_id, [new_section])
    replace_chunks_for_document(
        conn,
        document.doc_id,
        [
            chunk_factory(
                doc_id=document.doc_id,
                chunk_id="new-chunk",
                section_id=new_section.section_id,
                heading_path=["Replacement"],
                text="Replacement chunk.",
            )
        ],
    )

    assert [section.section_id for section in list_sections_by_document(conn, document.doc_id)] == [
        "new-section"
    ]
    assert [chunk.chunk_id for chunk in list_chunks_by_document(conn, document.doc_id)] == [
        "new-chunk"
    ]


def test_double_retry_is_idempotent(
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
    chunk_factory,
) -> None:
    document = document_factory()
    section = section_factory(doc_id=document.doc_id, section_id="stable-section")
    chunk = chunk_factory(
        doc_id=document.doc_id,
        chunk_id="stable-chunk",
        section_id=section.section_id,
    )
    save_document(conn, document)

    replace_sections_for_document(conn, document.doc_id, [section])
    replace_chunks_for_document(conn, document.doc_id, [chunk])
    replace_sections_for_document(conn, document.doc_id, [section])
    replace_chunks_for_document(conn, document.doc_id, [chunk])

    assert list_sections_by_document(conn, document.doc_id) == [section]
    assert list_chunks_by_document(conn, document.doc_id) == [chunk]


def test_retry_does_not_duplicate_child_ownership(
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
    chunk_factory,
) -> None:
    document = document_factory()
    save_document(conn, document)

    for suffix in ("one", "two"):
        section = section_factory(doc_id=document.doc_id, section_id=f"section-{suffix}")
        replace_sections_for_document(conn, document.doc_id, [section])
        replace_chunks_for_document(
            conn,
            document.doc_id,
            [
                chunk_factory(
                    doc_id=document.doc_id,
                    chunk_id=f"chunk-{suffix}",
                    section_id=section.section_id,
                )
            ],
        )

    sections = list_sections_by_document(conn, document.doc_id)
    chunks = list_chunks_by_document(conn, document.doc_id)

    assert [section.section_id for section in sections] == ["section-two"]
    assert [chunk.chunk_id for chunk in chunks] == ["chunk-two"]
    assert chunks[0].section_id == sections[0].section_id
