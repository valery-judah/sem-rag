from __future__ import annotations

from docforge.models import RawDocument
from docforge.parsers.canonicalize_common import (
    decode_utf8,
    normalize_newlines,
    require_non_empty_content,
)


class MarkdownCanonicalizer:
    def canonicalize(self, document: RawDocument) -> str:
        require_non_empty_content(document)
        # Markdown canonicalization preserves source fidelity except newline normalization.
        return normalize_newlines(decode_utf8(document.content_bytes))
