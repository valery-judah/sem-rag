from __future__ import annotations

import re
from html.parser import HTMLParser

from docforge.models import RawDocument
from docforge.parsers.canonicalize_common import (
    decode_utf8,
    normalize_newlines,
    require_non_empty_content,
)


class _HtmlToTextParser(HTMLParser):
    _BLOCK_TAGS = {
        "article",
        "blockquote",
        "div",
        "dl",
        "dt",
        "dd",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "footer",
        "li",
        "main",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "ul",
    }
    _SKIP_TAGS = {"head", "script", "style"}
    _INLINE_PUNCTUATION = (".", ",", ";", ":", "!", "?", ")", "]", "}")

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0
        self._pre_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        normalized_tag = tag.lower()
        if normalized_tag in self._SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return
        if normalized_tag == "br":
            self._append_newline()
            return
        if normalized_tag == "pre":
            self._pre_depth += 1
        if normalized_tag == "li":
            self._append_newline()
            self.parts.append("- ")
            return
        if normalized_tag in self._BLOCK_TAGS:
            self._append_newline()

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in self._SKIP_TAGS:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if self._skip_depth > 0:
            return
        if normalized_tag == "pre" and self._pre_depth > 0:
            self._pre_depth -= 1
        if normalized_tag in self._BLOCK_TAGS:
            self._append_newline()

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0 or not data:
            return
        if self._pre_depth > 0:
            self.parts.append(data)
            return

        collapsed = re.sub(r"\s+", " ", data)
        stripped = collapsed.strip()
        if not stripped:
            return

        if (
            self.parts
            and not self.parts[-1].endswith((" ", "\n"))
            and not stripped.startswith((" ", *self._INLINE_PUNCTUATION))
        ):
            self.parts.append(" ")
        self.parts.append(stripped)

    def text(self) -> str:
        merged = "".join(self.parts)
        normalized = normalize_newlines(merged)
        lines = [line.rstrip() for line in normalized.split("\n")]
        compact_lines = _collapse_empty_lines(lines)
        return "\n".join(compact_lines).strip()

    def _append_newline(self) -> None:
        if not self.parts:
            return
        if self.parts[-1].endswith("\n"):
            return
        self.parts.append("\n")


def _collapse_empty_lines(lines: list[str]) -> list[str]:
    output: list[str] = []
    previous_empty = False
    for line in lines:
        is_empty = line.strip() == ""
        if is_empty and previous_empty:
            continue
        output.append(line)
        previous_empty = is_empty
    return output


class HtmlCanonicalizer:
    def canonicalize(self, document: RawDocument) -> str:
        require_non_empty_content(document)
        text = normalize_newlines(decode_utf8(document.content_bytes))
        parser = _HtmlToTextParser()
        parser.feed(text)
        parser.close()
        return parser.text()
