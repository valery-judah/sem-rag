from __future__ import annotations

import re
import zlib

from docforge.models import RawDocument
from docforge.parsers.canonicalize_common import normalize_newlines, require_non_empty_content
from docforge.parsers.errors import PdfExtractionError

_STREAM_PATTERN = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)
_TEXT_SHOW_PATTERN = re.compile(r"(\((?:\\.|[^\\()])*\))\s*Tj", re.DOTALL)
_TEXT_ARRAY_PATTERN = re.compile(r"\[(.*?)\]\s*TJ", re.DOTALL)
_LITERAL_PATTERN = re.compile(r"\((?:\\.|[^\\()])*\)", re.DOTALL)


class PdfCanonicalizer:
    def canonicalize(self, document: RawDocument) -> str:
        require_non_empty_content(document)
        if not document.content_bytes.lstrip().startswith(b"%PDF-"):
            raise PdfExtractionError(
                doc_id=document.doc_id,
                content_type=document.content_type,
                reason="invalid_pdf_header",
            )

        text_fragments: list[str] = []
        for stream in _stream_payloads(document.content_bytes):
            text_fragments.extend(
                _extract_text_fragments(stream.decode("latin-1", errors="ignore"))
            )

        if not text_fragments:
            text_fragments = _extract_text_fragments(
                document.content_bytes.decode("latin-1", errors="ignore")
            )
        if not text_fragments:
            raise PdfExtractionError(
                doc_id=document.doc_id,
                content_type=document.content_type,
                reason="no_extractable_text",
            )

        canonical_text = normalize_newlines(
            "\n".join(fragment for fragment in text_fragments if fragment.strip())
        ).strip()
        if not canonical_text:
            raise PdfExtractionError(
                doc_id=document.doc_id,
                content_type=document.content_type,
                reason="empty_text_after_normalization",
            )
        return canonical_text


def _stream_payloads(content: bytes) -> list[bytes]:
    payloads: list[bytes] = []
    for match in _STREAM_PATTERN.finditer(content):
        stream = match.group(1)
        decoded = _inflate_if_possible(stream)
        payloads.append(decoded if decoded is not None else stream)
    return payloads


def _inflate_if_possible(stream: bytes) -> bytes | None:
    try:
        return zlib.decompress(stream)
    except zlib.error:
        return None


def _extract_text_fragments(content: str) -> list[str]:
    fragments: list[str] = []
    for match in _TEXT_SHOW_PATTERN.finditer(content):
        fragments.append(_decode_pdf_literal(match.group(1)))
    for match in _TEXT_ARRAY_PATTERN.finditer(content):
        array_literals = _LITERAL_PATTERN.findall(match.group(1))
        fragments.extend(_decode_pdf_literal(literal) for literal in array_literals)
    return fragments


def _decode_pdf_literal(literal: str) -> str:
    body = literal[1:-1]
    output: list[str] = []
    index = 0
    while index < len(body):
        current = body[index]
        if current != "\\":
            output.append(current)
            index += 1
            continue

        index += 1
        if index >= len(body):
            break
        escaped = body[index]

        if escaped in _ESCAPE_MAP:
            output.append(_ESCAPE_MAP[escaped])
            index += 1
            continue
        if escaped in {"\n", "\r"}:
            # Backslash followed by newline is a PDF line continuation.
            index += 1
            if escaped == "\r" and index < len(body) and body[index] == "\n":
                index += 1
            continue
        if escaped.isdigit():
            octal_digits = escaped
            index += 1
            while index < len(body) and len(octal_digits) < 3 and body[index].isdigit():
                octal_digits += body[index]
                index += 1
            output.append(chr(int(octal_digits, 8)))
            continue

        output.append(escaped)
        index += 1
    return "".join(output)


_ESCAPE_MAP = {
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "b": "\b",
    "f": "\f",
    "(": "(",
    ")": ")",
    "\\": "\\",
}
