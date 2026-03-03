import hashlib
import mimetypes
import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from docforge.connectors.base import BaseSourceConnector
from docforge.connectors.exceptions import ConfigurationError
from docforge.connectors.models import RawDocument


class LocalFileConnector(BaseSourceConnector):
    """
    Connects to a local filesystem directory and yields RawDocuments.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize the LocalFileConnector.

        Args:
            config: A dictionary containing at least:
                - `base_dir`: The root directory to scan.
                - `include_globs`: (Optional) List of globs to include (e.g., ["*.pdf", "*.txt"]).
                - `exclude_globs`: (Optional) List of glob patterns to exclude.
        """
        self.base_dir = Path(config.get("base_dir", "")).resolve()
        if not self.base_dir.is_dir():
            raise ConfigurationError(
                f"base_dir '{self.base_dir}' does not exist or is not a directory."
            )

        self.include_globs = config.get("include_globs", ["*"])
        self.exclude_globs = config.get("exclude_globs", [])
        self.source_name = config.get("name", "local")

    def _matches_globs(self, path: Path) -> bool:
        """Check if a path matches the include/exclude globs."""
        rel_path = path.relative_to(self.base_dir)

        # Check exclusions first
        for ex_glob in self.exclude_globs:
            if rel_path.match(ex_glob):
                return False

        # Then inclusions
        for in_glob in self.include_globs:
            if rel_path.match(in_glob):
                return True

        return False

    def fetch_documents(self, cursor: Any | None = None) -> Iterator[tuple[RawDocument, Any]]:
        """
        Yields tuples of (RawDocument, next_cursor) for files in the base directory.
        Only yields files modified on or after the cursor (timestamp).
        """
        max_mtime = float(cursor) if cursor is not None else 0.0

        for root, _dirs, files in os.walk(self.base_dir):
            for file_name in files:
                file_path = Path(root) / file_name
                if not self._matches_globs(file_path):
                    continue

                try:
                    stat = file_path.stat()
                except OSError:
                    continue

                if stat.st_mtime < (float(cursor) if cursor is not None else 0.0):
                    continue

                max_mtime = max(max_mtime, stat.st_mtime)

                try:
                    yield self._read_file(file_path, stat), max_mtime
                except Exception:
                    # Handle errors safely (e.g., yield an error event or skip gracefully
                    # instead of raising TerminalSourceError and breaking the whole stream).
                    continue

    def _get_file_stream(self, file_path: Path, chunk_size: int = 65536) -> Iterator[bytes]:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    def _read_file(self, file_path: Path, stat: os.stat_result) -> RawDocument:
        """Read a single file and convert it to a RawDocument."""
        created_at = datetime.fromtimestamp(stat.st_ctime, tz=UTC).isoformat()
        updated_at = datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat()

        content_type, _ = mimetypes.guess_type(file_path.name)
        if not content_type:
            # Fallback based on extension or octet-stream
            if file_path.suffix.lower() == ".pdf":
                content_type = "application/pdf"
            elif file_path.suffix.lower() == ".md":
                content_type = "text/markdown"
            else:
                content_type = "application/octet-stream"

        source_ref = str(file_path.relative_to(self.base_dir))

        # Fix doc_id generation: use "local" type and source_ref instead of mutable self.source_name
        doc_id_input = f"local:{source_ref}".encode()
        doc_id = hashlib.sha256(doc_id_input).hexdigest()[:32]

        # url: local files use file:// scheme
        url = file_path.as_uri()

        return RawDocument(
            doc_id=doc_id,
            source=self.source_name,
            source_ref=source_ref,
            url=url,
            content_stream=self._get_file_stream(file_path),
            content_type=content_type,
            metadata={"title": file_path.name, "source_name": self.source_name},
            acl_scope={},
            timestamps={"created_at": created_at, "updated_at": updated_at},
        )
