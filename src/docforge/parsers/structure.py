from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from docforge.models import AnchorRef, RawDocument, StructureNode
from docforge.parsers.anchors import AnchorBuilder, section_path_string

_HEADING_PATTERN = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
_HEADING_TRAILING_HASH_PATTERN = re.compile(r"\s+#+\s*$")
_CODE_FENCE_PATTERN = re.compile(r"^\s*```(?P<language>[A-Za-z0-9_+-]*)\s*$")
_ORDERED_LIST_PATTERN = re.compile(r"^\s*\d+[.)]\s+(.+?)\s*$")
_UNORDERED_LIST_PATTERN = re.compile(r"^\s*[-*+]\s+(.+?)\s*$")
_TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|?(?:\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$")


@dataclass(frozen=True, slots=True)
class _LineSpan:
    raw: str
    text: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True, slots=True)
class _Block:
    block_type: Literal["heading", "paragraph", "list", "table", "code"]
    text: str
    start_offset: int
    end_offset: int
    metadata: dict[str, Any] = field(default_factory=dict)
    heading_level: int | None = None
    heading_title: str | None = None


@dataclass(slots=True)
class _SectionContext:
    level: int
    node: StructureNode
    path_parts: list[str]


class HeuristicStructureExtractor:
    def extract(
        self,
        *,
        document: RawDocument,
        canonical_text: str,
        doc_anchor: AnchorRef,
    ) -> StructureNode:
        root = StructureNode(
            node_id=f"{document.doc_id}:root",
            node_type="doc",
            title=_title_from_document(document),
            text=canonical_text,
            anchor=doc_anchor,
        )
        if not canonical_text.strip():
            return root

        blocks = _parse_blocks(canonical_text)
        anchor_builder = AnchorBuilder(doc_id=document.doc_id)
        section_stack: list[_SectionContext] = []
        node_index = 0

        for block in blocks:
            if block.block_type == "heading":
                level = block.heading_level
                title = block.heading_title
                if level is None or title is None:
                    continue

                while section_stack and section_stack[-1].level >= level:
                    section_stack.pop()

                parent = section_stack[-1].node if section_stack else root
                parent_path = section_stack[-1].path_parts if section_stack else []
                path_parts = [*parent_path, title]
                section_anchor = anchor_builder.build_section_anchor(path_parts=path_parts)
                heading_node = StructureNode(
                    node_id=f"{document.doc_id}:node:{node_index}",
                    node_type="heading",
                    title=title,
                    anchor=section_anchor,
                    metadata={
                        "level": level,
                        "section_path": section_path_string(path_parts),
                        "start_offset": block.start_offset,
                        "end_offset": block.end_offset,
                    },
                )
                node_index += 1
                parent.children.append(heading_node)
                section_stack.append(
                    _SectionContext(level=level, node=heading_node, path_parts=path_parts)
                )
                continue

            current_path = section_stack[-1].path_parts if section_stack else []
            parent = section_stack[-1].node if section_stack else root
            block_anchor = anchor_builder.build_block_anchor(
                path_parts=current_path,
                block_type=block.block_type,
                start_offset=block.start_offset,
                end_offset=block.end_offset,
            )
            block_metadata: dict[str, Any] = dict(block.metadata)
            block_metadata["section_path"] = section_path_string(current_path)
            block_metadata["start_offset"] = block.start_offset
            block_metadata["end_offset"] = block.end_offset
            block_node = StructureNode(
                node_id=f"{document.doc_id}:node:{node_index}",
                node_type=block.block_type,
                text=block.text,
                anchor=block_anchor,
                metadata=block_metadata,
            )
            node_index += 1
            parent.children.append(block_node)

        return root


def _parse_blocks(text: str) -> list[_Block]:
    lines = _to_line_spans(text)
    blocks: list[_Block] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if line.text.strip() == "":
            index += 1
            continue

        fence_match = _CODE_FENCE_PATTERN.match(line.text)
        if fence_match is not None:
            block, index = _consume_code_block(lines, index, fence_match.group("language"))
            blocks.append(block)
            continue

        if index + 1 < len(lines) and _is_table_header(lines[index].text, lines[index + 1].text):
            block, index = _consume_table(lines, index)
            blocks.append(block)
            continue

        heading_match = _HEADING_PATTERN.match(line.text)
        if heading_match is not None:
            heading_title = _normalize_heading_title(heading_match.group(2))
            blocks.append(
                _Block(
                    block_type="heading",
                    text=heading_title,
                    start_offset=line.start_offset,
                    end_offset=line.end_offset,
                    heading_level=len(heading_match.group(1)),
                    heading_title=heading_title,
                )
            )
            index += 1
            continue

        if _list_marker(line.text) is not None:
            block, index = _consume_list(lines, index)
            blocks.append(block)
            continue

        block, index = _consume_paragraph(lines, index)
        blocks.append(block)

    return blocks


def _consume_code_block(
    lines: list[_LineSpan], start_index: int, language: str | None
) -> tuple[_Block, int]:
    end_index = start_index + 1
    while end_index < len(lines):
        if _CODE_FENCE_PATTERN.match(lines[end_index].text):
            break
        end_index += 1
    if end_index >= len(lines):
        end_index = len(lines) - 1

    metadata: dict[str, Any] = {}
    if language:
        metadata["language"] = language
    return (
        _Block(
            block_type="code",
            text=_join_raw(lines, start_index, end_index),
            start_offset=lines[start_index].start_offset,
            end_offset=lines[end_index].end_offset,
            metadata=metadata,
        ),
        end_index + 1,
    )


def _consume_table(lines: list[_LineSpan], start_index: int) -> tuple[_Block, int]:
    end_index = start_index + 2
    while end_index < len(lines):
        text = lines[end_index].text
        if text.strip() == "" or "|" not in text:
            break
        end_index += 1

    final_index = end_index - 1
    headers = _split_table_row(lines[start_index].text)
    return (
        _Block(
            block_type="table",
            text=_join_raw(lines, start_index, final_index),
            start_offset=lines[start_index].start_offset,
            end_offset=lines[final_index].end_offset,
            metadata={"headers": headers},
        ),
        end_index,
    )


def _consume_list(lines: list[_LineSpan], start_index: int) -> tuple[_Block, int]:
    end_index = start_index
    items: list[str] = []
    ordered: bool | None = None

    while end_index < len(lines):
        marker_match = _list_marker(lines[end_index].text)
        if marker_match is None:
            break

        marker_kind, item_text = marker_match
        if ordered is None:
            ordered = marker_kind == "ordered"
        items.append(item_text)
        end_index += 1

    final_index = end_index - 1
    return (
        _Block(
            block_type="list",
            text=_join_raw(lines, start_index, final_index),
            start_offset=lines[start_index].start_offset,
            end_offset=lines[final_index].end_offset,
            metadata={
                "ordered": bool(ordered),
                "items": items,
                "item_count": len(items),
            },
        ),
        end_index,
    )


def _consume_paragraph(lines: list[_LineSpan], start_index: int) -> tuple[_Block, int]:
    end_index = start_index
    while end_index < len(lines):
        text = lines[end_index].text
        if text.strip() == "":
            break
        if _CODE_FENCE_PATTERN.match(text):
            break
        if _HEADING_PATTERN.match(text):
            break
        if _list_marker(text) is not None:
            break
        if end_index + 1 < len(lines) and _is_table_header(text, lines[end_index + 1].text):
            break
        end_index += 1

    final_index = end_index - 1
    if final_index < start_index:
        final_index = start_index
        end_index = start_index + 1
    return (
        _Block(
            block_type="paragraph",
            text=_join_raw(lines, start_index, final_index),
            start_offset=lines[start_index].start_offset,
            end_offset=lines[final_index].end_offset,
        ),
        end_index,
    )


def _to_line_spans(text: str) -> list[_LineSpan]:
    lines = text.splitlines(keepends=True)
    if not lines:
        return []

    spans: list[_LineSpan] = []
    cursor = 0
    for raw_line in lines:
        end_offset = cursor + len(raw_line)
        text_line = raw_line[:-1] if raw_line.endswith("\n") else raw_line
        spans.append(
            _LineSpan(
                raw=raw_line,
                text=text_line,
                start_offset=cursor,
                end_offset=end_offset,
            )
        )
        cursor = end_offset
    return spans


def _join_raw(lines: list[_LineSpan], start_index: int, end_index: int) -> str:
    return "".join(line.raw for line in lines[start_index : end_index + 1]).rstrip("\n")


def _is_table_header(line: str, next_line: str) -> bool:
    if "|" not in line:
        return False
    return _TABLE_SEPARATOR_PATTERN.match(next_line) is not None


def _split_table_row(line: str) -> list[str]:
    trimmed = line.strip()
    if trimmed.startswith("|"):
        trimmed = trimmed[1:]
    if trimmed.endswith("|"):
        trimmed = trimmed[:-1]
    cells = [cell.strip() for cell in trimmed.split("|")]
    return [cell for cell in cells if cell]


def _normalize_heading_title(raw_title: str) -> str:
    stripped = raw_title.strip()
    without_trailing = _HEADING_TRAILING_HASH_PATTERN.sub("", stripped)
    return without_trailing.strip()


def _list_marker(line: str) -> tuple[Literal["ordered", "unordered"], str] | None:
    unordered_match = _UNORDERED_LIST_PATTERN.match(line)
    if unordered_match is not None:
        return ("unordered", unordered_match.group(1).strip())

    ordered_match = _ORDERED_LIST_PATTERN.match(line)
    if ordered_match is not None:
        return ("ordered", ordered_match.group(1).strip())
    return None


def _title_from_document(document: RawDocument) -> str | None:
    title = document.metadata.get("title")
    if isinstance(title, str):
        return title
    return None
