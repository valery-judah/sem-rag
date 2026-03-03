from __future__ import annotations

import re
from collections.abc import Hashable, Iterable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from docforge.config import SegmentationConfig
from docforge.models import AnchorRef, RawDocument, Segment, StructureNode
from docforge.parsers.anchors import normalize_anchor_slug, section_path_string

_CODE_FENCE_PATTERN = re.compile(r"^\s*```")
_CODE_BOUNDARY_PATTERN = re.compile(r"^\s*(?:async\s+def|def|class)\s+[A-Za-z_]\w*")
_LIST_ITEM_PATTERN = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")

_T = TypeVar("_T", bound=Hashable)


@dataclass(slots=True)
class _SectionContext:
    index: int
    node: StructureNode
    path_parts: list[str]
    parent_index: int | None
    depth: int
    anchor: AnchorRef
    blocks: list[StructureNode] = field(default_factory=list)
    child_indices: list[int] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _Chunk:
    text: str
    token_count: int
    block_type: str
    start_offset: int | None
    end_offset: int | None
    source_start: int
    source_end: int
    language: str | None = None
    table_headers: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class _ChunkDraft:
    text: str
    token_count: int
    block_type: str
    start_offset: int | None
    end_offset: int | None
    language: str | None = None
    table_headers: tuple[str, ...] | None = None


class HierarchicalSegmenter:
    def __init__(self, *, config: SegmentationConfig | None = None) -> None:
        self._config = config or SegmentationConfig()

    def segment(
        self,
        *,
        document: RawDocument,
        canonical_text: str,
        structure_tree: StructureNode,
        doc_anchor: AnchorRef,
    ) -> list[Segment]:
        del doc_anchor
        sections = _build_section_contexts(
            structure_tree=structure_tree,
            doc_id=document.doc_id,
            canonical_text=canonical_text,
        )
        if not sections:
            return []

        section_segments: list[Segment] = []
        for section in sections:
            section_text = _section_text(section)
            section_segments.append(
                Segment(
                    segment_id=_section_segment_id(document.doc_id, section.index),
                    doc_id=document.doc_id,
                    type="SECTION",
                    parent_id=(
                        _section_segment_id(document.doc_id, section.parent_index)
                        if section.parent_index is not None
                        else None
                    ),
                    child_ids=[],
                    section_path=section.anchor.section_path,
                    anchor=section.anchor,
                    text=section_text,
                    token_count=_token_count(section_text),
                    metadata={"depth": section.depth},
                )
            )

        for section in sections:
            if section.parent_index is None:
                continue
            parent_segment = section_segments[section.parent_index]
            parent_segment.child_ids.append(_section_segment_id(document.doc_id, section.index))

        segments: list[Segment] = []
        for section in sections:
            section_segment = section_segments[section.index]
            segments.append(section_segment)
            passages = self._build_passages(
                doc_id=document.doc_id,
                section=section,
                section_segment_id=section_segment.segment_id,
            )
            section_segment.child_ids.extend(passage.segment_id for passage in passages)
            segments.extend(passages)

        return segments

    def _build_passages(
        self,
        *,
        doc_id: str,
        section: _SectionContext,
        section_segment_id: str,
    ) -> list[Segment]:
        chunks = self._build_section_chunks(section)
        if not chunks:
            return []

        chunk_groups = _group_chunks(chunks, target_tokens=self._config.passage_tokens_target)
        overlap_tokens = int(round(self._config.passage_tokens_target * self._config.overlap_ratio))

        passages: list[Segment] = []
        previous_text = ""
        for passage_index, chunk_group in enumerate(chunk_groups):
            group_text = "\n\n".join(chunk.text for chunk in chunk_group)
            overlap_text = ""
            if overlap_tokens > 0 and passage_index > 0:
                overlap_text = _tail_tokens(previous_text, overlap_tokens)
            text = f"{overlap_text}\n\n{group_text}" if overlap_text else group_text

            block_types = _unique_in_order(chunk.block_type for chunk in chunk_group)
            metadata: dict[str, Any] = {"block_types": block_types}
            languages = _unique_in_order(
                chunk.language for chunk in chunk_group if chunk.language is not None
            )
            if languages:
                metadata["language"] = languages[0] if len(languages) == 1 else languages
            headers = [
                chunk.table_headers for chunk in chunk_group if chunk.table_headers is not None
            ]
            if headers:
                metadata["table_headers"] = list(headers[0])
            if overlap_text:
                metadata["overlap_tokens"] = _token_count(overlap_text)

            source_start = min(chunk.source_start for chunk in chunk_group)
            source_end = max(chunk.source_end for chunk in chunk_group)
            start_offset = _min_optional(chunk.start_offset for chunk in chunk_group)
            end_offset = _max_optional(chunk.end_offset for chunk in chunk_group)
            anchor = AnchorRef(
                anchor_id=f"passage:{doc_id}:s{section.index}:{source_start}-{source_end}",
                kind="passage",
                section_path=section.anchor.section_path,
                start_offset=start_offset,
                end_offset=end_offset,
            )
            passages.append(
                Segment(
                    segment_id=_passage_segment_id(doc_id, section.index, passage_index),
                    doc_id=doc_id,
                    type="PASSAGE",
                    parent_id=section_segment_id,
                    section_path=section.anchor.section_path,
                    anchor=anchor,
                    text=text,
                    token_count=_token_count(text),
                    metadata=metadata,
                )
            )
            previous_text = text

        return passages

    def _build_section_chunks(self, section: _SectionContext) -> list[_Chunk]:
        drafts: list[_ChunkDraft] = []
        for block in section.blocks:
            block_text = block.text
            if block_text is None or not block_text.strip():
                continue
            drafts.extend(self._split_block(block))

        chunks: list[_Chunk] = []
        source_cursor = 0
        for draft in drafts:
            if draft.token_count <= 0:
                continue
            source_start = source_cursor
            source_end = source_start + draft.token_count
            source_cursor = source_end
            chunks.append(
                _Chunk(
                    text=draft.text,
                    token_count=draft.token_count,
                    block_type=draft.block_type,
                    start_offset=draft.start_offset,
                    end_offset=draft.end_offset,
                    source_start=source_start,
                    source_end=source_end,
                    language=draft.language,
                    table_headers=draft.table_headers,
                )
            )

        return chunks

    def _split_block(self, block: StructureNode) -> list[_ChunkDraft]:
        text = block.text or ""
        block_type = block.node_type
        start_offset = _metadata_int(block, "start_offset")
        end_offset = _metadata_int(block, "end_offset")
        target = self._config.passage_tokens_target

        if _token_count(text) <= target:
            return [
                _ChunkDraft(
                    text=text,
                    token_count=_token_count(text),
                    block_type=block_type,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    language=_language_from_metadata(block),
                    table_headers=_table_headers_from_metadata(block),
                )
            ]

        if block_type == "table":
            headers = _table_headers_from_metadata(block)
            pieces = _split_table_text(text, target_tokens=target)
            return [
                _ChunkDraft(
                    text=piece,
                    token_count=_token_count(piece),
                    block_type=block_type,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    table_headers=headers,
                )
                for piece in pieces
                if piece.strip()
            ]

        if block_type == "code":
            language = _language_from_metadata(block)
            pieces = _split_code_text(text, target_tokens=target)
            return [
                _ChunkDraft(
                    text=piece,
                    token_count=_token_count(piece),
                    block_type=block_type,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    language=language,
                )
                for piece in pieces
                if piece.strip()
            ]

        pieces = _split_generic_text(text, target_tokens=target, block_type=block_type)
        return [
            _ChunkDraft(
                text=piece,
                token_count=_token_count(piece),
                block_type=block_type,
                start_offset=start_offset,
                end_offset=end_offset,
            )
            for piece in pieces
            if piece.strip()
        ]


def _build_section_contexts(
    *,
    structure_tree: StructureNode,
    doc_id: str,
    canonical_text: str,
) -> list[_SectionContext]:
    sections: list[_SectionContext] = []
    root_headings = [child for child in structure_tree.children if child.node_type == "heading"]
    root_blocks = [child for child in structure_tree.children if child.node_type != "heading"]

    root_index: int | None = None
    include_root_section = bool(root_blocks) or not root_headings
    if include_root_section:
        root_section = _SectionContext(
            index=0,
            node=structure_tree,
            path_parts=[],
            parent_index=None,
            depth=0,
            anchor=AnchorRef(
                anchor_id=f"section:{doc_id}:root",
                kind="section",
                section_path="root",
            ),
            blocks=root_blocks,
        )
        sections.append(root_section)
        root_index = root_section.index
        if not root_blocks and canonical_text.strip():
            root_section.blocks = [
                StructureNode(
                    node_id=f"{doc_id}:root-body",
                    node_type="paragraph",
                    text=canonical_text,
                    metadata={"start_offset": 0, "end_offset": len(canonical_text)},
                )
            ]

    def visit_heading(
        node: StructureNode,
        *,
        path_prefix: list[str],
        parent_index: int | None,
        depth: int,
    ) -> int:
        heading_title = node.title or "section"
        path_parts = [*path_prefix, heading_title]
        anchor = _section_anchor(
            node=node,
            doc_id=doc_id,
            path_parts=path_parts,
            fallback_index=len(sections),
        )
        section = _SectionContext(
            index=len(sections),
            node=node,
            path_parts=path_parts,
            parent_index=parent_index,
            depth=depth,
            anchor=anchor,
        )
        for child in node.children:
            if child.node_type != "heading":
                section.blocks.append(child)

        sections.append(section)
        if parent_index is not None:
            sections[parent_index].child_indices.append(section.index)

        for child in node.children:
            if child.node_type == "heading":
                visit_heading(
                    child,
                    path_prefix=path_parts,
                    parent_index=section.index,
                    depth=depth + 1,
                )
        return section.index

    for heading in root_headings:
        visit_heading(
            heading,
            path_prefix=[],
            parent_index=root_index,
            depth=1,
        )

    return sections


def _section_anchor(
    *,
    node: StructureNode,
    doc_id: str,
    path_parts: list[str],
    fallback_index: int,
) -> AnchorRef:
    if node.anchor is not None and node.anchor.kind == "section":
        if node.anchor.section_path:
            return node.anchor
        return AnchorRef(
            anchor_id=node.anchor.anchor_id,
            kind="section",
            section_path=section_path_string(path_parts),
        )

    section_path = section_path_string(path_parts)
    path_slug = normalize_anchor_slug(section_path, default=f"section-{fallback_index}")
    return AnchorRef(
        anchor_id=f"section:{doc_id}:{path_slug}",
        kind="section",
        section_path=section_path,
    )


def _section_text(section: _SectionContext) -> str:
    parts: list[str] = []
    if section.node.node_type == "heading" and section.node.title:
        parts.append(section.node.title)
    for block in section.blocks:
        if block.text is None:
            continue
        text = block.text.strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def _section_segment_id(doc_id: str, index: int) -> str:
    return f"{doc_id}:section:{index}"


def _passage_segment_id(doc_id: str, section_index: int, passage_index: int) -> str:
    return f"{doc_id}:passage:{section_index}:{passage_index}"


def _group_chunks(chunks: list[_Chunk], *, target_tokens: int) -> list[list[_Chunk]]:
    groups: list[list[_Chunk]] = []
    current: list[_Chunk] = []
    current_tokens = 0

    for chunk in chunks:
        if current and current_tokens + chunk.token_count > target_tokens:
            groups.append(current)
            current = []
            current_tokens = 0
        current.append(chunk)
        current_tokens += chunk.token_count

    if current:
        groups.append(current)
    return groups


def _split_table_text(text: str, *, target_tokens: int) -> list[str]:
    lines = text.splitlines()
    if len(lines) < 3:
        return _hard_split_text(text, target_tokens=target_tokens)

    header = "\n".join(lines[:2]).strip()
    rows = lines[2:]
    header_tokens = _token_count(header)
    if not rows:
        return [text]

    chunks: list[str] = []
    current_rows: list[str] = []
    current_tokens = header_tokens

    for row in rows:
        row_tokens = _token_count(row)
        if current_rows and current_tokens + row_tokens > target_tokens:
            chunks.append(_join_table_chunk(header, current_rows))
            current_rows = []
            current_tokens = header_tokens

        if row_tokens + header_tokens > target_tokens:
            for piece in _hard_split_text(row, target_tokens=max(1, target_tokens - header_tokens)):
                chunks.append(_join_table_chunk(header, [piece]))
            continue

        current_rows.append(row)
        current_tokens += row_tokens

    if current_rows:
        chunks.append(_join_table_chunk(header, current_rows))
    return chunks


def _join_table_chunk(header: str, rows: list[str]) -> str:
    return f"{header}\n" + "\n".join(rows)


def _split_code_text(text: str, *, target_tokens: int) -> list[str]:
    lines = text.splitlines()
    if not lines:
        return []

    open_fence = lines[0] if _CODE_FENCE_PATTERN.match(lines[0]) else None
    close_fence = lines[-1] if len(lines) > 1 and _CODE_FENCE_PATTERN.match(lines[-1]) else None
    if open_fence is not None and close_fence is not None and len(lines) >= 2:
        body = lines[1:-1]
    else:
        open_fence = None
        close_fence = None
        body = lines

    groups = _split_code_groups(body)
    wrapped_groups = [
        _wrap_code_group(group, open_fence=open_fence, close_fence=close_fence) for group in groups
    ]
    return _pack_text_units(wrapped_groups, target_tokens=target_tokens, separator="\n\n")


def _split_code_groups(lines: list[str]) -> list[str]:
    if not lines:
        return []

    by_boundary: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if _CODE_BOUNDARY_PATTERN.match(line) and current:
            by_boundary.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        by_boundary.append(current)

    if len(by_boundary) > 1:
        return ["\n".join(group).strip("\n") for group in by_boundary if "\n".join(group).strip()]

    by_blank: list[list[str]] = []
    current = []
    for line in lines:
        if line.strip():
            current.append(line)
        elif current:
            by_blank.append(current)
            current = []
    if current:
        by_blank.append(current)

    if by_blank:
        return ["\n".join(group).strip("\n") for group in by_blank if "\n".join(group).strip()]
    return ["\n".join(lines).strip("\n")]


def _wrap_code_group(group: str, *, open_fence: str | None, close_fence: str | None) -> str:
    stripped = group.strip("\n")
    if open_fence is None or close_fence is None:
        return stripped
    return f"{open_fence}\n{stripped}\n{close_fence}"


def _split_generic_text(text: str, *, target_tokens: int, block_type: str) -> list[str]:
    if block_type == "list":
        list_items = [line.strip() for line in text.splitlines() if _LIST_ITEM_PATTERN.match(line)]
        if list_items:
            return _pack_text_units(list_items, target_tokens=target_tokens, separator="\n")

    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    if not paragraphs:
        return _hard_split_text(text, target_tokens=target_tokens)

    units: list[str] = []
    for paragraph in paragraphs:
        if _token_count(paragraph) <= target_tokens:
            units.append(paragraph)
            continue
        sentences = [
            piece.strip() for piece in _SENTENCE_SPLIT_PATTERN.split(paragraph) if piece.strip()
        ]
        if sentences:
            units.extend(sentences)
        else:
            units.append(paragraph)

    return _pack_text_units(units, target_tokens=target_tokens, separator="\n\n")


def _pack_text_units(units: list[str], *, target_tokens: int, separator: str) -> list[str]:
    chunks: list[str] = []
    current_units: list[str] = []

    for unit in units:
        if not unit.strip():
            continue
        if _token_count(unit) > target_tokens:
            if current_units:
                chunks.append(separator.join(current_units))
                current_units = []
            chunks.extend(_hard_split_text(unit, target_tokens=target_tokens))
            continue

        candidate_units = [*current_units, unit]
        if current_units and _token_count(separator.join(candidate_units)) > target_tokens:
            chunks.append(separator.join(current_units))
            current_units = [unit]
        else:
            current_units = candidate_units

    if current_units:
        chunks.append(separator.join(current_units))
    return chunks


def _hard_split_text(text: str, *, target_tokens: int) -> list[str]:
    tokens = text.split()
    if not tokens:
        return []
    bounded_target = max(1, target_tokens)
    chunks: list[str] = []
    index = 0
    while index < len(tokens):
        next_index = min(index + bounded_target, len(tokens))
        chunks.append(" ".join(tokens[index:next_index]))
        index = next_index
    return chunks


def _tail_tokens(text: str, token_count: int) -> str:
    if token_count <= 0:
        return ""
    tokens = text.split()
    if not tokens:
        return ""
    return " ".join(tokens[-token_count:])


def _language_from_metadata(block: StructureNode) -> str | None:
    language = block.metadata.get("language")
    if isinstance(language, str) and language:
        return language
    return None


def _table_headers_from_metadata(block: StructureNode) -> tuple[str, ...] | None:
    headers = block.metadata.get("headers")
    if isinstance(headers, list) and all(isinstance(header, str) for header in headers):
        return tuple(headers)
    return None


def _metadata_int(block: StructureNode, key: str) -> int | None:
    value = block.metadata.get(key)
    if isinstance(value, int):
        return value
    return None


def _unique_in_order(values: Iterable[_T]) -> list[_T]:
    seen: set[_T] = set()
    unique: list[_T] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def _min_optional(values: Iterable[int | None]) -> int | None:
    present = [value for value in values if value is not None]
    return min(present) if present else None


def _max_optional(values: Iterable[int | None]) -> int | None:
    present = [value for value in values if value is not None]
    return max(present) if present else None


def _token_count(text: str) -> int:
    if not text.strip():
        return 0
    return len(text.split())
