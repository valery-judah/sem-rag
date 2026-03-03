from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Sequence

from docforge.models import AnchorRef, StructureNode

_NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")
_DASH_PATTERN = re.compile(r"-+")


def normalize_anchor_slug(value: str, *, default: str) -> str:
    lowered = value.strip().lower()
    replaced = _NON_ALNUM_PATTERN.sub("-", lowered)
    compact = _DASH_PATTERN.sub("-", replaced).strip("-")
    if compact:
        return compact
    return default


def section_path_string(path_parts: Sequence[str]) -> str:
    if not path_parts:
        return "root"
    return " > ".join(path_parts)


def section_path_slug(path_parts: Sequence[str]) -> str:
    if not path_parts:
        return "root"
    return "/".join(
        normalize_anchor_slug(part, default=f"section-{index + 1}")
        for index, part in enumerate(path_parts)
    )


class AnchorBuilder:
    def __init__(self, *, doc_id: str) -> None:
        self._doc_id = doc_id
        self._collision_counts: dict[str, int] = defaultdict(int)

    def build_section_anchor(self, *, path_parts: Sequence[str]) -> AnchorRef:
        section_path = section_path_string(path_parts)
        anchor_base = f"section:{self._doc_id}:{section_path_slug(path_parts)}"
        return AnchorRef(
            anchor_id=self._collision_safe(anchor_base),
            kind="section",
            section_path=section_path,
        )

    def build_block_anchor(
        self,
        *,
        path_parts: Sequence[str],
        block_type: str,
        start_offset: int,
        end_offset: int,
    ) -> AnchorRef:
        section_slug = section_path_slug(path_parts)
        block_slug = normalize_anchor_slug(block_type, default="block")
        anchor_base = (
            f"block:{self._doc_id}:{section_slug}:{block_slug}:{start_offset}-{end_offset}"
        )
        return AnchorRef(
            anchor_id=self._collision_safe(anchor_base),
            kind="block",
            section_path=section_path_string(path_parts),
            start_offset=start_offset,
            end_offset=end_offset,
        )

    def _collision_safe(self, anchor_id: str) -> str:
        self._collision_counts[anchor_id] += 1
        occurrence = self._collision_counts[anchor_id]
        if occurrence == 1:
            return anchor_id
        return f"{anchor_id}-{occurrence}"


def collect_structure_anchors(
    structure_tree: StructureNode,
) -> tuple[list[AnchorRef], list[AnchorRef]]:
    section_anchors: list[AnchorRef] = []
    block_anchors: list[AnchorRef] = []

    def visit(node: StructureNode) -> None:
        if node.anchor is not None:
            if node.anchor.kind == "section":
                section_anchors.append(node.anchor)
            elif node.anchor.kind in {"block", "passage"}:
                block_anchors.append(node.anchor)
        for child in node.children:
            visit(child)

    visit(structure_tree)
    return section_anchors, block_anchors
