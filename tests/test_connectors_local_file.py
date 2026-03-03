from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path

from docforge.config import SourceConfig
from docforge.connectors import LocalFileConnector


def _set_mtime(path: Path, dt: datetime) -> None:
    timestamp = dt.astimezone(UTC).timestamp()
    os.utime(path, (timestamp, timestamp))


def test_local_file_connector_contract_fields_and_determinism(tmp_path: Path) -> None:
    pdf_path = tmp_path / "guide.pdf"
    content = b"%PDF-1.7\nhello\n"
    pdf_path.write_bytes(content)
    fixed_time = datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)
    _set_mtime(pdf_path, fixed_time)

    source = SourceConfig(
        type="local_file",
        path=str(pdf_path),
        metadata={"title": "Guide"},
        acl_scope={"visibility": "internal"},
    )
    connector = LocalFileConnector(source)

    first_doc = list(connector.iter_raw_documents())[0]
    second_doc = list(connector.iter_raw_documents())[0]

    expected_doc_id = f"local_file:{sha256(str(pdf_path).encode('utf-8')).hexdigest()}"
    assert first_doc.doc_id == expected_doc_id
    assert first_doc.source == "local_file"
    assert first_doc.source_ref == str(pdf_path)
    assert first_doc.url == f"file:{pdf_path}"
    assert first_doc.content_bytes == content
    assert first_doc.content_type == "application/pdf"
    assert first_doc.metadata == {"title": "Guide"}
    assert first_doc.acl_scope == {"visibility": "internal"}
    assert first_doc.timestamps.updated_at == fixed_time
    assert first_doc.timestamps.created_at == fixed_time
    assert first_doc.model_dump() == second_doc.model_dump()


def test_local_file_connector_since_filter_excludes_older_update(tmp_path: Path) -> None:
    doc_path = tmp_path / "note.txt"
    doc_path.write_text("hello", encoding="utf-8")
    updated_at = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
    _set_mtime(doc_path, updated_at)

    source = SourceConfig(type="local_file", path=str(doc_path))
    connector = LocalFileConnector(source)
    since = updated_at + timedelta(seconds=1)

    docs = list(connector.iter_raw_documents(since=since))

    assert docs == []


def test_local_file_connector_content_type_resolution_priority(tmp_path: Path) -> None:
    unknown_path = tmp_path / "blob.unknownext"
    unknown_path.write_bytes(b"x")

    override_source = SourceConfig(
        type="local_file",
        path=str(unknown_path),
        content_type="application/x-override",
    )
    connector_with_override = LocalFileConnector(override_source)
    overridden_doc = list(connector_with_override.iter_raw_documents())[0]
    assert overridden_doc.content_type == "application/x-override"

    default_source = SourceConfig(type="local_file", path=str(unknown_path))
    connector_default = LocalFileConnector(default_source)
    default_doc = list(connector_default.iter_raw_documents())[0]
    assert default_doc.content_type == "application/octet-stream"


def test_local_file_connector_url_override_is_used(tmp_path: Path) -> None:
    pdf_path = tmp_path / "guide.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nhello\n")
    fixed_time = datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)
    _set_mtime(pdf_path, fixed_time)

    source = SourceConfig(
        type="local_file",
        path=str(pdf_path),
        url="https://example.invalid/doc",
    )
    connector = LocalFileConnector(source)
    doc = list(connector.iter_raw_documents())[0]
    assert doc.url == "https://example.invalid/doc"


def test_local_file_connector_timestamps_are_utc_aware(tmp_path: Path) -> None:
    pdf_path = tmp_path / "guide.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nhello\n")
    fixed_time = datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)
    _set_mtime(pdf_path, fixed_time)

    source = SourceConfig(type="local_file", path=str(pdf_path))
    connector = LocalFileConnector(source)
    doc = list(connector.iter_raw_documents())[0]
    assert doc.timestamps.updated_at.tzinfo is UTC
    assert doc.timestamps.created_at.tzinfo is UTC


def test_local_file_connector_defaults_metadata_and_acl_scope_to_empty_dict(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "guide.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nhello\n")
    fixed_time = datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)
    _set_mtime(pdf_path, fixed_time)

    source = SourceConfig(type="local_file", path=str(pdf_path))
    connector = LocalFileConnector(source)
    doc = list(connector.iter_raw_documents())[0]
    assert doc.metadata == {}
    assert doc.acl_scope == {}
