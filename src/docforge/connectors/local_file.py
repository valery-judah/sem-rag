from __future__ import annotations

import mimetypes
from collections.abc import Iterator
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from docforge.config import SourceConfig
from docforge.models import DocumentTimestamps, RawDocument

PDF_CONTENT_TYPE = "application/pdf"
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream"


def _normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class LocalFileConnector:
    def __init__(self, source: SourceConfig) -> None:
        self.source = source

    def iter_raw_documents(self, since: datetime | None = None) -> Iterator[RawDocument]:
        source_ref = self.source.path
        file_path = Path(source_ref)
        stat_result = file_path.stat()
        updated_at = datetime.fromtimestamp(stat_result.st_mtime, tz=UTC)

        if since is not None and updated_at <= _normalize_utc(since):
            return

        content_bytes = file_path.read_bytes()
        timestamps = DocumentTimestamps(created_at=updated_at, updated_at=updated_at)

        yield RawDocument(
            doc_id=self.source.doc_id or _default_doc_id(source_ref),
            source="local_file",
            source_ref=source_ref,
            url=self.source.url or f"file:{source_ref}",
            content_bytes=content_bytes,
            content_type=_resolve_content_type(self.source),
            metadata=dict(self.source.metadata),
            acl_scope=dict(self.source.acl_scope),
            timestamps=timestamps,
        )


def _default_doc_id(source_ref: str) -> str:
    digest = sha256(source_ref.encode("utf-8")).hexdigest()
    return f"local_file:{digest}"


def _resolve_content_type(source: SourceConfig) -> str:
    if source.content_type is not None:
        return source.content_type

    path = Path(source.path)
    if path.suffix.lower() == ".pdf":
        return PDF_CONTENT_TYPE

    guessed_type, _ = mimetypes.guess_type(source.path)
    if guessed_type is None:
        return OCTET_STREAM_CONTENT_TYPE
    return guessed_type
