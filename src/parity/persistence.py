"""SQLite-backed persistence for internal corpus contract models."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from parity._contracts import Chunk, Document, ProcessingStatus, Section, SourceType


def create_schema(conn: sqlite3.Connection) -> None:
    """Create the minimal SQLite schema for persisted corpus primitives."""

    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            ingest_status TEXT NOT NULL,
            storage_ref TEXT NOT NULL,
            metadata_json TEXT
        );

        CREATE TABLE IF NOT EXISTS sections (
            section_id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            heading_path_json TEXT NOT NULL,
            depth INTEGER NOT NULL,
            parent_section_id TEXT,
            heading_text TEXT,
            page_start INTEGER,
            page_end INTEGER,
            source_start_offset INTEGER,
            source_end_offset INTEGER,
            structure_confidence REAL,
            UNIQUE (doc_id, section_id),
            FOREIGN KEY (doc_id) REFERENCES documents (doc_id) ON DELETE CASCADE,
            FOREIGN KEY (doc_id, parent_section_id)
                REFERENCES sections (doc_id, section_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            text TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            heading_path_json TEXT NOT NULL,
            section_id TEXT,
            page_start INTEGER,
            page_end INTEGER,
            source_start_offset INTEGER,
            source_end_offset INTEGER,
            lineage_json TEXT,
            debug_metadata_json TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents (doc_id) ON DELETE CASCADE,
            FOREIGN KEY (doc_id, section_id)
                REFERENCES sections (doc_id, section_id)
                ON DELETE CASCADE
        );
        """
    )


def save_document(conn: sqlite3.Connection, document: Document) -> None:
    """Persist one document contract model."""

    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        """
        INSERT OR REPLACE INTO documents (
            doc_id,
            workspace_id,
            source_type,
            title,
            filename,
            uploaded_at,
            ingest_status,
            storage_ref,
            metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            document.doc_id,
            document.workspace_id,
            str(document.source_type),
            document.title,
            document.filename,
            _dump_datetime(document.uploaded_at),
            str(document.ingest_status),
            document.storage_ref,
            _dump_optional_dict(document.metadata),
        ),
    )


def save_sections(conn: sqlite3.Connection, sections: list[Section]) -> None:
    """Persist one or more section contract models."""

    conn.execute("PRAGMA foreign_keys = ON")
    conn.executemany(
        """
        INSERT OR REPLACE INTO sections (
            section_id,
            doc_id,
            heading_path_json,
            depth,
            parent_section_id,
            heading_text,
            page_start,
            page_end,
            source_start_offset,
            source_end_offset,
            structure_confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                section.section_id,
                section.doc_id,
                _dump_json(section.heading_path),
                section.depth,
                section.parent_section_id,
                section.heading_text,
                section.page_start,
                section.page_end,
                section.source_start_offset,
                section.source_end_offset,
                section.structure_confidence,
            )
            for section in sections
        ],
    )


def save_chunks(conn: sqlite3.Connection, chunks: list[Chunk]) -> None:
    """Persist one or more chunk contract models."""

    conn.execute("PRAGMA foreign_keys = ON")
    conn.executemany(
        """
        INSERT OR REPLACE INTO chunks (
            chunk_id,
            doc_id,
            text,
            ordinal,
            heading_path_json,
            section_id,
            page_start,
            page_end,
            source_start_offset,
            source_end_offset,
            lineage_json,
            debug_metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                chunk.chunk_id,
                chunk.doc_id,
                chunk.text,
                chunk.ordinal,
                _dump_json(chunk.heading_path),
                chunk.section_id,
                chunk.page_start,
                chunk.page_end,
                chunk.source_start_offset,
                chunk.source_end_offset,
                _dump_optional_dict(chunk.lineage),
                _dump_optional_dict(chunk.debug_metadata),
            )
            for chunk in chunks
        ],
    )


def replace_sections_for_document(
    conn: sqlite3.Connection,
    doc_id: str,
    sections: list[Section],
) -> None:
    """Replace the full persisted section set for one document."""

    _require_matching_doc_id(doc_id, sections)
    conn.execute("PRAGMA foreign_keys = ON")
    with conn:
        conn.execute("DELETE FROM sections WHERE doc_id = ?", (doc_id,))
        save_sections(conn, sections)


def replace_chunks_for_document(
    conn: sqlite3.Connection,
    doc_id: str,
    chunks: list[Chunk],
) -> None:
    """Replace the full persisted chunk set for one document."""

    _require_matching_doc_id(doc_id, chunks)
    conn.execute("PRAGMA foreign_keys = ON")
    with conn:
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        save_chunks(conn, chunks)


def list_documents_by_workspace(
    conn: sqlite3.Connection,
    workspace_id: str,
) -> list[Document]:
    """Load documents belonging to one workspace."""

    conn.execute("PRAGMA foreign_keys = ON")
    rows = conn.execute(
        """
        SELECT
            doc_id,
            workspace_id,
            source_type,
            title,
            filename,
            uploaded_at,
            ingest_status,
            storage_ref,
            metadata_json
        FROM documents
        WHERE workspace_id = ?
        ORDER BY doc_id
        """,
        (workspace_id,),
    ).fetchall()
    return [_row_to_document(row) for row in rows]


def list_sections_by_document(conn: sqlite3.Connection, doc_id: str) -> list[Section]:
    """Load sections belonging to one document."""

    conn.execute("PRAGMA foreign_keys = ON")
    rows = conn.execute(
        """
        SELECT
            section_id,
            doc_id,
            heading_path_json,
            depth,
            parent_section_id,
            heading_text,
            page_start,
            page_end,
            source_start_offset,
            source_end_offset,
            structure_confidence
        FROM sections
        WHERE doc_id = ?
        ORDER BY depth, section_id
        """,
        (doc_id,),
    ).fetchall()
    return [_row_to_section(row) for row in rows]


def list_chunks_by_document(conn: sqlite3.Connection, doc_id: str) -> list[Chunk]:
    """Load chunks belonging to one document."""

    conn.execute("PRAGMA foreign_keys = ON")
    rows = conn.execute(
        """
        SELECT
            chunk_id,
            doc_id,
            text,
            ordinal,
            heading_path_json,
            section_id,
            page_start,
            page_end,
            source_start_offset,
            source_end_offset,
            lineage_json,
            debug_metadata_json
        FROM chunks
        WHERE doc_id = ?
        ORDER BY ordinal, chunk_id
        """,
        (doc_id,),
    ).fetchall()
    return [_row_to_chunk(row) for row in rows]


def _row_to_document(row: sqlite3.Row | tuple[object, ...]) -> Document:
    (
        doc_id,
        workspace_id,
        source_type,
        title,
        filename,
        uploaded_at,
        ingest_status,
        storage_ref,
        metadata_json,
    ) = row
    return Document(
        doc_id=_cast_str(doc_id),
        workspace_id=_cast_str(workspace_id),
        source_type=SourceType(_cast_str(source_type)),
        title=_cast_str(title),
        filename=_cast_str(filename),
        uploaded_at=datetime.fromisoformat(_cast_str(uploaded_at)),
        ingest_status=ProcessingStatus(_cast_str(ingest_status)),
        storage_ref=_cast_str(storage_ref),
        metadata=_load_optional_dict(metadata_json),
    )


def _row_to_section(row: sqlite3.Row | tuple[object, ...]) -> Section:
    (
        section_id,
        doc_id,
        heading_path_json,
        depth,
        parent_section_id,
        heading_text,
        page_start,
        page_end,
        source_start_offset,
        source_end_offset,
        structure_confidence,
    ) = row
    return Section(
        section_id=_cast_str(section_id),
        doc_id=_cast_str(doc_id),
        heading_path=_load_str_list(heading_path_json),
        depth=_cast_int(depth),
        parent_section_id=_cast_optional_str(parent_section_id),
        heading_text=_cast_optional_str(heading_text),
        page_start=_cast_optional_int(page_start),
        page_end=_cast_optional_int(page_end),
        source_start_offset=_cast_optional_int(source_start_offset),
        source_end_offset=_cast_optional_int(source_end_offset),
        structure_confidence=_cast_optional_float(structure_confidence),
    )


def _row_to_chunk(row: sqlite3.Row | tuple[object, ...]) -> Chunk:
    (
        chunk_id,
        doc_id,
        text,
        ordinal,
        heading_path_json,
        section_id,
        page_start,
        page_end,
        source_start_offset,
        source_end_offset,
        lineage_json,
        debug_metadata_json,
    ) = row
    return Chunk(
        chunk_id=_cast_str(chunk_id),
        doc_id=_cast_str(doc_id),
        text=_cast_str(text),
        ordinal=_cast_int(ordinal),
        heading_path=_load_str_list(heading_path_json),
        section_id=_cast_optional_str(section_id),
        page_start=_cast_optional_int(page_start),
        page_end=_cast_optional_int(page_end),
        source_start_offset=_cast_optional_int(source_start_offset),
        source_end_offset=_cast_optional_int(source_end_offset),
        lineage=_load_optional_dict(lineage_json),
        debug_metadata=_load_optional_dict(debug_metadata_json),
    )


def _dump_datetime(value: datetime) -> str:
    return value.isoformat()


def _dump_json(value: list[str]) -> str:
    return json.dumps(value)


def _dump_optional_dict(value: dict[str, str] | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value)


def _load_str_list(value: object) -> list[str]:
    raw = json.loads(_cast_str(value))
    return [str(item) for item in raw]


def _load_optional_dict(value: object) -> dict[str, str] | None:
    if value is None:
        return None
    raw = json.loads(_cast_str(value))
    return {str(key): str(val) for key, val in raw.items()}


def _cast_str(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"expected str, got {type(value).__name__}")
    return value


def _cast_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return _cast_str(value)


def _cast_int(value: object) -> int:
    if not isinstance(value, int):
        raise TypeError(f"expected int, got {type(value).__name__}")
    return value


def _cast_optional_int(value: object) -> int | None:
    if value is None:
        return None
    return _cast_int(value)


def _cast_optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, int):
        return float(value)
    if not isinstance(value, float):
        raise TypeError(f"expected float, got {type(value).__name__}")
    return value


def _require_matching_doc_id(
    doc_id: str,
    records: list[Section] | list[Chunk],
) -> None:
    if any(record.doc_id != doc_id for record in records):
        raise ValueError("all persisted records must belong to the target document")
