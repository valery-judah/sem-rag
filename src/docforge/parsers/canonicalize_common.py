from __future__ import annotations

from docforge.models import RawDocument
from docforge.parsers.errors import EmptyContentError


def decode_utf8(content: bytes) -> str:
    return content.decode("utf-8-sig", errors="replace")


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def require_non_empty_content(document: RawDocument) -> None:
    if document.content_bytes:
        return
    raise EmptyContentError(doc_id=document.doc_id, content_type=document.content_type)
