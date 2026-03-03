from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Literal

_ContentFamily = Literal["markdown", "html", "plain", "unsupported"]


@dataclass(frozen=True, slots=True)
class CanonicalizationResult:
    canonical_text: str
    has_textual_content: bool
    detected_content_family: _ContentFamily
    warnings: list[str] = field(default_factory=list)


def canonicalize(
    content_bytes: bytes, content_type: str, blank_line_collapse: int
) -> CanonicalizationResult:
    normalized_content_type = content_type.split(";", 1)[0].strip().lower()

    if normalized_content_type in {"text/markdown", "text/x-markdown"}:
        text = _decode_text_bytes(content_bytes)
        canonical_text = _normalize_markdown_like(text, blank_line_collapse=blank_line_collapse)
        return CanonicalizationResult(
            canonical_text=canonical_text,
            has_textual_content=bool(canonical_text),
            detected_content_family="markdown",
            warnings=[],
        )

    if normalized_content_type in {"text/html", "application/xhtml+xml"}:
        text = _decode_text_bytes(content_bytes)
        canonical_text = _canonicalize_html(text, blank_line_collapse=blank_line_collapse)
        return CanonicalizationResult(
            canonical_text=canonical_text,
            has_textual_content=bool(canonical_text),
            detected_content_family="html",
            warnings=[],
        )

    if normalized_content_type == "text/plain" or normalized_content_type.startswith("text/"):
        text = _decode_text_bytes(content_bytes)
        canonical_text = _normalize_markdown_like(text, blank_line_collapse=blank_line_collapse)
        return CanonicalizationResult(
            canonical_text=canonical_text,
            has_textual_content=bool(canonical_text),
            detected_content_family="plain",
            warnings=[],
        )

    return CanonicalizationResult(
        canonical_text="",
        has_textual_content=False,
        detected_content_family="unsupported",
        warnings=[f"unsupported content_type '{normalized_content_type}'"],
    )


def _decode_text_bytes(content_bytes: bytes) -> str:
    # Keep decode deterministic and always produce valid UTF-8 text.
    return content_bytes.decode("utf-8", errors="replace")


def _normalize_markdown_like(text: str, blank_line_collapse: int) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    max_blank_lines = max(0, blank_line_collapse)

    out_lines: list[str] = []
    blank_run = 0
    in_code_block = False

    for line in lines:
        if line.startswith("```"):
            in_code_block = not in_code_block
            out_lines.append(line)
            blank_run = 0
            continue

        if in_code_block:
            out_lines.append(line)
            continue

        line_no_trailing_ws = line.rstrip(" \t")
        if line_no_trailing_ws == "":
            blank_run += 1
            if blank_run <= max_blank_lines:
                out_lines.append("")
            continue

        blank_run = 0
        out_lines.append(line_no_trailing_ws)

    return "\n".join(out_lines).strip("\n")


def _canonicalize_html(text: str, blank_line_collapse: int) -> str:
    parser = _HtmlToMarkdownLikeParser()
    parser.feed(text)
    parser.close()
    parser.finalize()
    markdown_like = "\n\n".join(block for block in parser.blocks if block)
    return _normalize_markdown_like(markdown_like, blank_line_collapse=blank_line_collapse)


class _HtmlToMarkdownLikeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._inline_buffer: list[str] = []
        self._list_stack: list[tuple[str, int]] = []
        self._heading_level: int | None = None

        self._in_pre = False
        self._pre_buffer: list[str] = []
        self._pre_language = ""

        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._cell_buffer: list[str] = []
        self._row_cells: list[str] = []
        self._row_has_header_cell = False
        self._table_rows: list[list[str]] = []
        self._table_row_has_header: list[bool] = []
        self._table_has_header = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {k.lower(): v for k, v in attrs}
        tag_l = tag.lower()

        if tag_l in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._flush_inline_buffer()
            self._heading_level = int(tag_l[1])
            return

        if tag_l in {"ul", "ol"}:
            self._list_stack.append((tag_l, 1))
            return

        if tag_l in {"p", "li"}:
            self._flush_inline_buffer()
            return

        if tag_l == "br":
            self._inline_buffer.append("\n")
            return

        if tag_l == "pre":
            self._flush_inline_buffer()
            self._in_pre = True
            self._pre_buffer = []
            self._pre_language = ""
            return

        if tag_l == "code":
            class_attr = attrs_map.get("class")
            if isinstance(class_attr, str):
                for part in class_attr.split():
                    lowered = part.lower()
                    if lowered.startswith("language-"):
                        self._pre_language = lowered.removeprefix("language-")
                        break
            return

        if tag_l == "table":
            self._flush_inline_buffer()
            self._in_table = True
            self._table_rows = []
            self._table_row_has_header = []
            self._table_has_header = False
            return

        if tag_l == "tr" and self._in_table:
            self._in_row = True
            self._row_cells = []
            self._row_has_header_cell = False
            return

        if tag_l in {"th", "td"} and self._in_row:
            self._in_cell = True
            self._cell_buffer = []
            if tag_l == "th":
                self._row_has_header_cell = True
            return

    def handle_endtag(self, tag: str) -> None:
        tag_l = tag.lower()

        if tag_l in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = self._heading_level or 1
            text = _collapse_inline_whitespace("".join(self._inline_buffer)).strip()
            if text:
                self.blocks.append(f"{'#' * level} {text}")
            self._inline_buffer = []
            self._heading_level = None
            return

        if tag_l == "p":
            self._flush_inline_buffer()
            return

        if tag_l == "li":
            item_text = _collapse_inline_whitespace("".join(self._inline_buffer)).strip()
            if item_text:
                if self._list_stack and self._list_stack[-1][0] == "ol":
                    kind, current = self._list_stack[-1]
                    self.blocks.append(f"{current}. {item_text}")
                    self._list_stack[-1] = (kind, current + 1)
                else:
                    self.blocks.append(f"- {item_text}")
            self._inline_buffer = []
            return

        if tag_l in {"ul", "ol"} and self._list_stack:
            self._list_stack.pop()
            return

        if tag_l == "pre" and self._in_pre:
            code_text = "".join(self._pre_buffer).replace("\r\n", "\n").replace("\r", "\n")
            fence = f"```{self._pre_language}" if self._pre_language else "```"
            self.blocks.append(f"{fence}\n{code_text}\n```")
            self._in_pre = False
            self._pre_buffer = []
            self._pre_language = ""
            return

        if tag_l in {"th", "td"} and self._in_cell:
            cell_text = _collapse_inline_whitespace("".join(self._cell_buffer)).strip()
            self._row_cells.append(cell_text.replace("|", "\\|"))
            self._cell_buffer = []
            self._in_cell = False
            return

        if tag_l == "tr" and self._in_row:
            if self._row_cells:
                self._table_rows.append(self._row_cells)
                self._table_row_has_header.append(self._row_has_header_cell)
                if self._row_has_header_cell:
                    self._table_has_header = True
            self._row_cells = []
            self._row_has_header_cell = False
            self._in_row = False
            return

        if tag_l == "table" and self._in_table:
            self._emit_table()
            self._in_table = False
            return

    def handle_data(self, data: str) -> None:
        if self._in_pre:
            self._pre_buffer.append(data)
            return
        if self._in_cell:
            self._cell_buffer.append(data)
            return
        self._inline_buffer.append(data)

    def _flush_inline_buffer(self) -> None:
        text = _collapse_inline_whitespace("".join(self._inline_buffer)).strip()
        if text:
            self.blocks.append(text)
        self._inline_buffer = []

    def finalize(self) -> None:
        self._flush_inline_buffer()

    def _emit_table(self) -> None:
        if not self._table_rows:
            return

        rows = self._table_rows
        max_cols = max(len(row) for row in rows)
        padded_rows = [row + ([""] * (max_cols - len(row))) for row in rows]

        if self._table_has_header:
            header_idx = self._table_row_has_header.index(True)
            header = padded_rows[header_idx]
            separator = ["---"] * max_cols
            self.blocks.append(_render_table_row(header))
            self.blocks.append(_render_table_row(separator))
            for idx, row in enumerate(padded_rows):
                if idx == header_idx:
                    continue
                self.blocks.append(_render_table_row(row))
            return

        for row in padded_rows:
            self.blocks.append(_render_table_row(row))


def _collapse_inline_whitespace(text: str) -> str:
    return " ".join(text.split())


def _render_table_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"
