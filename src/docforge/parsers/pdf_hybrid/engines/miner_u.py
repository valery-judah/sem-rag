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


def _map_block_type(mineru_type: str) -> BlockType:
    mineru_type_lower = mineru_type.lower()
    if mineru_type_lower in ("title", "heading"):
        return BlockType.HEADING
    elif mineru_type_lower in ("text", "paragraph", "text_block"):
        return BlockType.PARA
    elif mineru_type_lower in ("list", "list_item"):
        return BlockType.LIST
    elif mineru_type_lower == "table":
        return BlockType.TABLE
    elif mineru_type_lower in ("code", "code_block"):
        return BlockType.CODE
    elif mineru_type_lower in ("footnote", "footer"):
        return BlockType.FOOTER
    elif mineru_type_lower == "header":
        return BlockType.HEADER
    elif mineru_type_lower in ("caption", "image_caption", "table_caption"):
        return BlockType.CAPTION
    return BlockType.UNKNOWN


def adapt_mineru_output(
    raw_output: dict[str, Any] | list[dict[str, Any]], artifact_ref: str
) -> list[PageCandidate]:
    """
    Adapts MinerU (Magic-PDF) raw output to the shared candidate models.
    Supports either _content_list.json format (a flat list of blocks with page_idx)
    or a dictionary with 'pdf_info' or 'pages'.
    """
    pages_dict: dict[int, dict[str, Any]] = {}

    if isinstance(raw_output, list):
        # Flat list of blocks from _content_list.json
        for raw_block in raw_output:
            page_idx = raw_block.get("page_idx", 0)
            if page_idx not in pages_dict:
                pages_dict[page_idx] = {"page_idx": page_idx, "blocks": []}
            pages_dict[page_idx]["blocks"].append(raw_block)
    else:
        # Dictionary format (e.g. from middle json or old format)
        pdf_info = raw_output.get("pdf_info", raw_output)

        if isinstance(pdf_info, list):
            pages_list = pdf_info
        else:
            pages_list = pdf_info.get("pages", pdf_info)

        # If pdf_info is a list, it might be the list of pages
        if isinstance(pages_list, list):
            for idx, page in enumerate(pages_list):
                page_idx = page.get("page_idx", page.get("page", idx))
                pages_dict[page_idx] = {
                    "page_idx": page_idx,
                    "blocks": page.get("blocks", page.get("preproc_blocks", [])),
                }

    candidates = []

    for page_idx in sorted(pages_dict.keys()):
        page_data = pages_dict[page_idx]
        raw_blocks = page_data.get("blocks", [])

        blocks: list[BlockCandidate] = []
        assets: list[AssetCandidate] = []

        for idx, raw_block in enumerate(raw_blocks):
            block_type_str = raw_block.get("type", "unknown")
            block_id = raw_block.get("id", f"mineru_p{page_idx}_b{idx}")
            text = raw_block.get("text", "")

            if not text and "lines" in raw_block:
                lines_text = []
                for line in raw_block["lines"]:
                    span_texts = [
                        span.get("content", "")
                        for span in line.get("spans", [])
                        if span.get("content")
                    ]
                    if span_texts:
                        lines_text.append(" ".join(span_texts))
                text = "\n".join(lines_text)

            bbox = raw_block.get("bbox")
            polygon = raw_block.get("polygon")

            source = BlockSource(
                engine="mineru", engine_artifact_ref=artifact_ref, engine_block_ref=block_id
            )

            # Asset extraction
            if block_type_str.lower() in ("image", "figure", "equation"):
                asset_type = (
                    AssetType.EQUATION if block_type_str.lower() == "equation" else AssetType.IMAGE
                )
                assets.append(
                    AssetCandidate(
                        asset_id=f"asset_{block_id}",
                        type=asset_type,
                        page_idx=page_idx,
                        path_or_ref="",
                        bbox_or_poly=bbox or polygon,
                        source=source,
                    )
                )
                if not text:
                    continue

            # Table as asset
            if block_type_str.lower() == "table":
                assets.append(
                    AssetCandidate(
                        asset_id=f"table_render_{block_id}",
                        type=AssetType.TABLE_RENDER,
                        page_idx=page_idx,
                        path_or_ref="",
                        bbox_or_poly=bbox or polygon,
                        source=source,
                    )
                )

            block = BlockCandidate(
                block_id=block_id,
                type=_map_block_type(block_type_str),
                text=text,
                page_idx=page_idx,
                bbox=bbox,
                poly=polygon,
                reading_order_key=f"{idx:05d}",
                source=source,
            )
            blocks.append(block)

        status = ParseStatus.OK if blocks or assets else ParseStatus.EMPTY

        candidate = PageCandidate(
            page_idx=page_idx,
            blocks=blocks,
            assets=assets,
            signals=PageSignals.compute(blocks, assets),
            status=status,
        )
        candidates.append(candidate)

    return candidates
