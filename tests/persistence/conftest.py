from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from parity._contracts import Chunk, Document, ProcessingStatus, Section, SourceType
from parity.persistence import create_schema


@pytest.fixture
def conn() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    create_schema(connection)
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def document_factory():
    def make(
        doc_id: str = "doc-1",
        workspace_id: str = "workspace-1",
        source_type: SourceType = SourceType.PDF,
        **overrides: object,
    ) -> Document:
        filename = f"{doc_id}.pdf" if source_type is SourceType.PDF else f"{doc_id}.md"
        base = {
            "doc_id": doc_id,
            "workspace_id": workspace_id,
            "source_type": source_type,
            "title": f"Title for {doc_id}",
            "filename": filename,
            "uploaded_at": datetime(2026, 3, 8, tzinfo=UTC),
            "ingest_status": ProcessingStatus.READY,
            "storage_ref": f"file:///tmp/{doc_id}",
            "metadata": {"origin": "test"},
        }
        base.update(overrides)
        return Document(**base)

    return make


@pytest.fixture
def section_factory():
    def make(
        doc_id: str = "doc-1",
        section_id: str = "section-1",
        **overrides: object,
    ) -> Section:
        base = {
            "section_id": section_id,
            "doc_id": doc_id,
            "heading_path": ["Chapter 1"],
            "depth": 0,
            "heading_text": "Chapter 1",
            "page_start": 1,
            "page_end": 1,
        }
        base.update(overrides)
        return Section(**base)

    return make


@pytest.fixture
def chunk_factory():
    def make(
        doc_id: str = "doc-1",
        chunk_id: str = "chunk-1",
        **overrides: object,
    ) -> Chunk:
        base = {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "text": "Consensus requires stable coordination for replicated state.",
            "ordinal": 0,
            "heading_path": ["Chapter 1", "Overview"],
            "page_start": 2,
            "page_end": 2,
            "source_start_offset": 10,
            "source_end_offset": 65,
        }
        base.update(overrides)
        return Chunk(**base)

    return make
