from __future__ import annotations

import enum
import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from docforge.parsers.pdf_hybrid.config import PdfHybridConfig


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class ParserBlockType(enum.StrEnum):
    PARA = "para"
    LIST = "list"
    TABLE = "table"
    CODE = "code"


def _validate_non_empty_string(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} must be a non-empty string")


def _validate_range(value: tuple[int, int], field_name: str) -> None:
    start, end = value
    if start < 0:
        raise ValueError(f"{field_name} start offset must be >= 0")
    if end < start:
        raise ValueError(f"{field_name} end offset must be >= start offset")


def _validate_range_in_bounds(value: tuple[int, int], text_length: int, field_name: str) -> None:
    _start, end = value
    if end > text_length:
        raise ValueError(f"{field_name} end offset must be <= canonical_text length")


class BlockNode(StrictModel):
    """A leaf content block within the structure tree."""

    type: ParserBlockType
    range: tuple[int, int]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_model(self) -> BlockNode:
        _validate_range(self.range, "BlockNode.range")
        return self


class HeadingNode(StrictModel):
    """A heading node that groups child blocks and nested headings."""

    level: int
    text: str
    type: Literal["heading"] = "heading"
    children: list[BlockNode | HeadingNode] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_model(self) -> HeadingNode:
        if not 1 <= self.level <= 6:
            raise ValueError("HeadingNode.level must be an integer in [1, 6]")
        _validate_non_empty_string(self.text, "HeadingNode.text")
        return self


class DocNode(StrictModel):
    """Root of the structure tree. type is always 'doc'."""

    type: Literal["doc"] = "doc"
    children: list[HeadingNode | BlockNode] = Field(default_factory=list)


class SectionAnchor(StrictModel):
    """Anchor for a single section identified by its path."""

    section_path: str
    sec_anchor: str

    @model_validator(mode="after")
    def _validate_model(self) -> SectionAnchor:
        _validate_non_empty_string(self.section_path, "SectionAnchor.section_path")
        _validate_non_empty_string(self.sec_anchor, "SectionAnchor.sec_anchor")
        return self


class BlockAnchor(StrictModel):
    """Anchor for a single content block."""

    type: ParserBlockType
    section_path: str
    pass_anchor: str
    range: tuple[int, int]

    @model_validator(mode="after")
    def _validate_model(self) -> BlockAnchor:
        _validate_non_empty_string(self.section_path, "BlockAnchor.section_path")
        _validate_non_empty_string(self.pass_anchor, "BlockAnchor.pass_anchor")
        _validate_range(self.range, "BlockAnchor.range")
        return self


class AnchorMap(StrictModel):
    """Anchor registry for a parsed document."""

    doc_anchor: str
    sections: list[SectionAnchor]
    blocks: list[BlockAnchor]

    @model_validator(mode="after")
    def _validate_model(self) -> AnchorMap:
        _validate_non_empty_string(self.doc_anchor, "AnchorMap.doc_anchor")
        return self


class ParserConfig(StrictModel):
    """Settings that affect deterministic parser output. Bump parser_version on any change."""

    parser_version: str
    blank_line_collapse: int = 2
    enable_hybrid_pdf_pipeline: bool = False
    pdf_hybrid: PdfHybridConfig = Field(default_factory=PdfHybridConfig)

    @model_validator(mode="after")
    def _validate_model(self) -> ParserConfig:
        _validate_non_empty_string(self.parser_version, "parser_version")
        return self

    @property
    def config_hash(self) -> str:
        """Return a deterministic SHA-256 hash of the configuration state."""
        serialized = self.model_dump(mode="json")
        json_str = json.dumps(serialized, sort_keys=True)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


class ParsedDocument(StrictModel):
    """Parser output contract (RFC §2.2). Invariants validated on construction."""

    doc_id: str
    title: str
    canonical_text: str
    structure_tree: DocNode
    anchors: AnchorMap
    metadata: dict[str, Any]

    @model_validator(mode="after")
    def _validate_model(self) -> ParsedDocument:
        _validate_non_empty_string(self.doc_id, "doc_id")

        has_textual_content = self.metadata.get("has_textual_content", True)
        if has_textual_content and not self.canonical_text:
            raise ValueError("canonical_text must be non-empty when document has textual content")

        parser_version = self.metadata.get("parser_version")
        if not isinstance(parser_version, str) or not parser_version:
            raise ValueError("metadata must contain a non-empty 'parser_version' string")

        canonical_len = len(self.canonical_text)
        for block in _iter_tree_blocks(self.structure_tree):
            _validate_range_in_bounds(block.range, canonical_len, "structure_tree block range")
        for block_anchor in self.anchors.blocks:
            _validate_range_in_bounds(block_anchor.range, canonical_len, "block anchor range")

        return self


def _iter_tree_blocks(node: DocNode | HeadingNode) -> list[BlockNode]:
    blocks: list[BlockNode] = []
    for child in node.children:
        if isinstance(child, BlockNode):
            blocks.append(child)
        else:
            blocks.extend(_iter_tree_blocks(child))
    return blocks
