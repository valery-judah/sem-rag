from __future__ import annotations

import sqlite3

import pytest

from parity._contracts import Section
from parity.persistence import (
    list_sections_by_document,
    replace_sections_for_document,
    save_document,
    save_sections,
)

pytestmark = pytest.mark.persistence


def test_sections_round_trip_preserves_parent_child_links(
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
) -> None:
    document = document_factory()
    sections = [
        section_factory(doc_id=document.doc_id, section_id="doc-1-section-1"),
        section_factory(
            doc_id=document.doc_id,
            section_id="doc-1-section-2",
            parent_section_id="doc-1-section-1",
            heading_path=["Chapter 1", "Overview"],
            depth=1,
            heading_text="Overview",
            page_start=2,
            page_end=3,
            source_start_offset=10,
            source_end_offset=42,
            structure_confidence=0.9,
        ),
    ]
    save_document(conn, document)

    save_sections(conn, sections)

    loaded = list_sections_by_document(conn, document.doc_id)

    assert loaded == sections
    assert isinstance(loaded[0], Section)


def test_optional_section_fields_round_trip_as_none(
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
) -> None:
    document = document_factory()
    section = section_factory(
        doc_id=document.doc_id,
        heading_path=["Appendix"],
        depth=0,
        heading_text=None,
        page_start=None,
        page_end=None,
        source_start_offset=None,
        source_end_offset=None,
        structure_confidence=None,
    )
    save_document(conn, document)

    save_sections(conn, [section])

    loaded = list_sections_by_document(conn, document.doc_id)[0]

    assert loaded.heading_text is None
    assert loaded.page_start is None
    assert loaded.structure_confidence is None


def test_replace_for_document_removes_prior_sections(
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
) -> None:
    document = document_factory()
    save_document(conn, document)
    save_sections(
        conn,
        [
            section_factory(doc_id=document.doc_id, section_id="old-section-1"),
            section_factory(doc_id=document.doc_id, section_id="old-section-2"),
        ],
    )

    replacement = [
        section_factory(
            doc_id=document.doc_id,
            section_id="new-section-1",
            heading_path=["Replacement"],
            heading_text="Replacement",
        )
    ]
    replace_sections_for_document(conn, document.doc_id, replacement)

    assert list_sections_by_document(conn, document.doc_id) == replacement


def test_replace_for_document_rejects_cross_document_sections(
    conn: sqlite3.Connection,
    document_factory,
    section_factory,
) -> None:
    document = document_factory()
    save_document(conn, document)

    with pytest.raises(ValueError, match="target document"):
        replace_sections_for_document(
            conn,
            document.doc_id,
            [section_factory(doc_id="doc-2", section_id="doc-2-section-1")],
        )
