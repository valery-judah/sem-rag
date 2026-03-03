from __future__ import annotations

from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, Field

AnchorKind: TypeAlias = Literal["doc", "section", "block", "passage"]
StructureNodeType: TypeAlias = Literal["doc", "heading", "paragraph", "list", "table", "code"]
SegmentType: TypeAlias = Literal["SECTION", "PASSAGE"]


class AnchorRef(BaseModel):
    anchor_id: str
    kind: AnchorKind
    section_path: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None


class StructureNode(BaseModel):
    node_id: str
    node_type: StructureNodeType
    title: str | None = None
    text: str | None = None
    anchor: AnchorRef | None = None
    children: list[StructureNode] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Segment(BaseModel):
    segment_id: str
    doc_id: str
    type: SegmentType
    parent_id: str | None = None
    child_ids: list[str] = Field(default_factory=list)
    section_path: str | None = None
    anchor: AnchorRef
    text: str
    token_count: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    doc_id: str
    title: str | None = None
    canonical_text: str
    structure_tree: StructureNode
    doc_anchor: AnchorRef
    section_anchors: list[AnchorRef] = Field(default_factory=list)
    block_anchors: list[AnchorRef] = Field(default_factory=list)
    segments: list[Segment] = Field(default_factory=list)
