import re
from typing import Any

from docforge.parsers.pdf_hybrid.models import (
    AssetCandidate,
    AssetType,
    BlockCandidate,
    BlockSource,
    BlockType,
    PageCandidate,
    PageSignals,
    ParseStatus,
)


def _map_block_type(marker_type: str) -> BlockType:
    marker_type_lower = marker_type.lower()
    if marker_type_lower in ("title", "sectionheader"):
        return BlockType.HEADING
    elif marker_type_lower in ("text", "paragraph"):
        return BlockType.PARA
    elif marker_type_lower in ("listitem", "list"):
        return BlockType.LIST
    elif marker_type_lower == "table":
        return BlockType.TABLE
    elif marker_type_lower == "code":
        return BlockType.CODE
    elif marker_type_lower == "picture":
        return BlockType.CAPTION
    elif marker_type_lower == "footer":
        return BlockType.FOOTER
    elif marker_type_lower in ("header", "pageheader"):
        return BlockType.HEADER
    return BlockType.UNKNOWN


def _strip_html_tags(html_str: str) -> str:
    """Basic HTML tag stripping to get plain text."""
    if not html_str:
        return ""
    text = re.sub(r"<[^>]+>", "", html_str)
    return text.strip()


def adapt_marker_output(raw_output: dict[str, Any], artifact_ref: str) -> list[PageCandidate]:
    """
    Adapts Marker raw output to the shared candidate models.
    Expects raw_output to have a 'children' key containing a list of Page dicts.
    """
    candidates = []

    pages = raw_output.get("children", [])
    if not pages and "pages" in raw_output:
        # Fallback to older marker format if 'children' is not at root
        pages = raw_output["pages"]

    for page_idx, page_dict in enumerate(pages):
        # Allow older format where page index is explicit, or rely on enumeration
        page_num = page_dict.get("page", page_dict.get("page_idx", page_idx))

        # New format blocks are in 'children'. Old format uses 'blocks'
        raw_blocks = page_dict.get("children", page_dict.get("blocks", []))
        if raw_blocks is None:
            raw_blocks = []

        blocks: list[BlockCandidate] = []
        assets: list[AssetCandidate] = []

        for idx, raw_block in enumerate(raw_blocks):
            block_type_str = raw_block.get("block_type", raw_block.get("type", "unknown"))
            block_id = raw_block.get("id", f"marker_p{page_num}_b{idx}")

            # Text can be in 'html', 'raw_text', or 'text'
            raw_text = raw_block.get("html", raw_block.get("raw_text", raw_block.get("text", "")))
            text = _strip_html_tags(raw_text)

            polygon = raw_block.get("polygon")
            bbox = raw_block.get("bbox")

            source = BlockSource(
                engine="marker", engine_artifact_ref=artifact_ref, engine_block_ref=block_id
            )

            # Extract assets if picture or equation
            if block_type_str.lower() in ("picture", "equation", "table"):
                asset_type = AssetType.IMAGE
                if block_type_str.lower() == "equation":
                    asset_type = AssetType.EQUATION
                elif block_type_str.lower() == "table":
                    asset_type = AssetType.TABLE_RENDER

                assets.append(
                    AssetCandidate(
                        asset_id=f"asset_{block_id}",
                        type=asset_type,
                        page_idx=page_num,
                        path_or_ref="",
                        bbox_or_poly=polygon or bbox,
                        source=source,
                    )
                )
                if not text and block_type_str.lower() != "table":
                    # Skip block creation if there's no text and it's not a table
                    continue

            # Avoid creating empty blocks unless it's a structural element
            if not text and block_type_str.lower() not in ("table", "picture", "equation"):
                continue

            block = BlockCandidate(
                block_id=block_id,
                type=_map_block_type(block_type_str),
                text=text,
                page_idx=page_num,
                bbox=bbox,
                poly=polygon,
                reading_order_key=f"{idx:05d}",
                source=source,
            )
            blocks.append(block)

        status = ParseStatus.OK if blocks or assets else ParseStatus.EMPTY

        candidate = PageCandidate(
            page_idx=page_num,
            blocks=blocks,
            assets=assets,
            signals=PageSignals.compute(blocks, assets),
            status=status,
        )
        candidates.append(candidate)

    return candidates
