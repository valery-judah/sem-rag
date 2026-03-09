from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from parity._contracts import Chunk, Document, ProcessingStatus, Section, SourceType
from parity.persistence import (
    create_schema,
    list_chunks_by_document,
    list_documents_by_workspace,
    list_sections_by_document,
    save_chunks,
    save_document,
    save_sections,
)


@pytest.fixture
def conn() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    create_schema(connection)
    try:
        yield connection
    finally:
        connection.close()


def make_document(
    doc_id: str = "doc-1",
    workspace_id: str = "workspace-1",
    source_type: SourceType = SourceType.PDF,
) -> Document:
    return Document(
        doc_id=doc_id,
        workspace_id=workspace_id,
        source_type=source_type,
        title=f"Title for {doc_id}",
        filename=f"{doc_id}.pdf" if source_type is SourceType.PDF else f"{doc_id}.md",
        uploaded_at=datetime(2026, 3, 8, tzinfo=UTC),
        ingest_status=ProcessingStatus.READY,
        storage_ref=f"file:///tmp/{doc_id}",
        metadata={"origin": "test"},
    )


def make_sections(doc_id: str = "doc-1") -> list[Section]:
    return [
        Section(
            section_id=f"{doc_id}-section-1",
            doc_id=doc_id,
            heading_path=["Chapter 1"],
            depth=0,
            heading_text="Chapter 1",
            page_start=1,
            page_end=1,
        ),
        Section(
            section_id=f"{doc_id}-section-2",
            doc_id=doc_id,
            parent_section_id=f"{doc_id}-section-1",
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


def make_chunks(doc_id: str = "doc-1") -> list[Chunk]:
    return [
        Chunk(
            chunk_id=f"{doc_id}-chunk-1",
            doc_id=doc_id,
            section_id=f"{doc_id}-section-2",
            text="Consensus requires stable coordination for replicated state.",
            ordinal=0,
            heading_path=["Chapter 1", "Overview"],
            page_start=2,
            page_end=2,
            source_start_offset=10,
            source_end_offset=65,
            lineage={"chunker_version": "v1"},
            debug_metadata={"token_count": "9"},
        ),
        Chunk(
            chunk_id=f"{doc_id}-chunk-2",
            doc_id=doc_id,
            section_id=f"{doc_id}-section-2",
            text="Leader election limits conflicting writes during failover.",
            ordinal=1,
            heading_path=["Chapter 1", "Overview"],
            source_start_offset=66,
            source_end_offset=120,
        ),
    ]


def test_document_round_trip_preserves_locked_fields(conn: sqlite3.Connection) -> None:
    document = make_document()

    save_document(conn, document)

    loaded = list_documents_by_workspace(conn, "workspace-1")

    assert loaded == [document]


def test_section_round_trip_preserves_hierarchy_and_heading_path(
    conn: sqlite3.Connection,
) -> None:
    document = make_document()
    sections = make_sections()
    save_document(conn, document)

    save_sections(conn, sections)

    loaded = list_sections_by_document(conn, document.doc_id)

    assert loaded == sections


def test_chunk_round_trip_preserves_section_link_and_offsets(conn: sqlite3.Connection) -> None:
    document = make_document()
    sections = make_sections()
    chunks = make_chunks()
    save_document(conn, document)
    save_sections(conn, sections)

    save_chunks(conn, chunks)

    loaded = list_chunks_by_document(conn, document.doc_id)

    assert loaded == chunks


def test_workspace_isolation_filters_documents(conn: sqlite3.Connection) -> None:
    save_document(conn, make_document(doc_id="doc-1", workspace_id="workspace-1"))
    save_document(conn, make_document(doc_id="doc-2", workspace_id="workspace-2"))

    loaded = list_documents_by_workspace(conn, "workspace-1")

    assert [document.doc_id for document in loaded] == ["doc-1"]


def test_workspace_isolation_prevents_cross_document_leakage(conn: sqlite3.Connection) -> None:
    document_one = make_document(doc_id="doc-1", workspace_id="workspace-1")
    document_two = make_document(doc_id="doc-2", workspace_id="workspace-2")
    sections_one = make_sections(doc_id="doc-1")
    sections_two = make_sections(doc_id="doc-2")
    chunks_one = make_chunks(doc_id="doc-1")
    chunks_two = make_chunks(doc_id="doc-2")

    save_document(conn, document_one)
    save_document(conn, document_two)
    save_sections(conn, sections_one + sections_two)
    save_chunks(conn, chunks_one + chunks_two)

    loaded_sections = list_sections_by_document(conn, "doc-1")
    loaded_chunks = list_chunks_by_document(conn, "doc-1")

    assert loaded_sections == sections_one
    assert loaded_chunks == chunks_one


def test_repository_rehydrates_valid_contract_models(conn: sqlite3.Connection) -> None:
    document = make_document()
    sections = make_sections()
    chunks = make_chunks()
    save_document(conn, document)
    save_sections(conn, sections)
    save_chunks(conn, chunks)

    loaded_document = list_documents_by_workspace(conn, document.workspace_id)[0]
    loaded_section = list_sections_by_document(conn, document.doc_id)[0]
    loaded_chunk = list_chunks_by_document(conn, document.doc_id)[0]

    assert isinstance(loaded_document, Document)
    assert isinstance(loaded_section, Section)
    assert isinstance(loaded_chunk, Chunk)


def test_optional_fields_round_trip_as_none_or_value(conn: sqlite3.Connection) -> None:
    document = make_document()
    sections = [
        Section(
            section_id="doc-1-section-1",
            doc_id=document.doc_id,
            heading_path=["Appendix"],
            depth=0,
        )
    ]
    chunks = [
        Chunk(
            chunk_id="doc-1-chunk-1",
            doc_id=document.doc_id,
            text="Appendix note.",
            ordinal=0,
            heading_path=["Appendix"],
        )
    ]
    save_document(conn, document)
    save_sections(conn, sections)
    save_chunks(conn, chunks)

    loaded_section = list_sections_by_document(conn, document.doc_id)[0]
    loaded_chunk = list_chunks_by_document(conn, document.doc_id)[0]

    assert loaded_section.page_start is None
    assert loaded_section.structure_confidence is None
    assert loaded_chunk.section_id is None
    assert loaded_chunk.lineage is None
    assert loaded_chunk.debug_metadata is None


def test_loaded_chunks_preserve_retrieval_ready_shape(conn: sqlite3.Connection) -> None:
    document = make_document()
    sections = make_sections()
    chunks = make_chunks()
    save_document(conn, document)
    save_sections(conn, sections)
    save_chunks(conn, chunks)

    loaded = list_chunks_by_document(conn, document.doc_id)

    assert loaded[0].doc_id == document.doc_id
    assert loaded[0].text == chunks[0].text
    assert loaded[0].ordinal == 0
    assert loaded[0].heading_path == ["Chapter 1", "Overview"]
    assert loaded[0].section_id == "doc-1-section-2"


def test_invalid_foreign_links_fail_fast(conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        save_sections(conn, make_sections())

    save_document(conn, make_document())

    with pytest.raises(sqlite3.IntegrityError):
        save_chunks(
            conn,
            [
                Chunk(
                    chunk_id="broken-chunk",
                    doc_id="doc-1",
                    section_id="missing-section",
                    text="Broken linkage.",
                    ordinal=0,
                    heading_path=["Broken"],
                )
            ],
        )
