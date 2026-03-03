from __future__ import annotations

from docforge.models import RawDocument
from docforge.parsers.canonicalize_common import (
    decode_utf8,
    normalize_newlines,
    require_non_empty_content,
)


class PlainTextCanonicalizer:
    def canonicalize(self, document: RawDocument) -> str:
        require_non_empty_content(document)
        return normalize_newlines(decode_utf8(document.content_bytes))
