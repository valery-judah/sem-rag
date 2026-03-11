from __future__ import annotations

import sqlite3

import pytest

from parity._contracts import Document, ProcessingStatus, SourceType
from parity.persistence import list_documents_by_workspace, save_document

pytestmark = pytest.mark.persistence


def test_create_and_get_document_round_trip(
    conn: sqlite3.Connection,
    document_factory,
) -> None:
    document = document_factory()

    save_document(conn, document)

    loaded = list_documents_by_workspace(conn, "workspace-1")

    assert loaded == [document]


def test_workspace_isolation_filters_documents(
    conn: sqlite3.Connection,
    document_factory,
) -> None:
    save_document(conn, document_factory(doc_id="doc-1", workspace_id="workspace-1"))
    save_document(conn, document_factory(doc_id="doc-2", workspace_id="workspace-2"))

    loaded = list_documents_by_workspace(conn, "workspace-1")

    assert [document.doc_id for document in loaded] == ["doc-1"]


def test_save_document_replaces_existing_row_for_same_doc_id(
    conn: sqlite3.Connection,
    document_factory,
) -> None:
    original = document_factory(doc_id="doc-1", ingest_status=ProcessingStatus.REGISTERED)
    replacement = document_factory(
        doc_id="doc-1",
        source_type=SourceType.MARKDOWN,
        filename="doc-1.md",
        ingest_status=ProcessingStatus.FAILED,
        storage_ref="file:///tmp/doc-1.md",
        metadata={"origin": "retry"},
    )

    save_document(conn, original)
    save_document(conn, replacement)

    loaded = list_documents_by_workspace(conn, original.workspace_id)

    assert loaded == [replacement]
    assert isinstance(loaded[0], Document)
