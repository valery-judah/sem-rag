import hashlib
from typing import Any

from docforge.parsers.models import (
    AnchorMap,
    BlockAnchor,
    BlockNode,
    DocNode,
    HeadingNode,
    ParsedDocument,
    ParserBlockType,
    ParserConfig,
    SectionAnchor,
)
from docforge.parsers.pdf_hybrid.models import BlockType
from docforge.parsers.pdf_hybrid.schema import ExtractedPdfDocument


def distill_pdf(
    extracted_doc: ExtractedPdfDocument,
    config: ParserConfig,
    *,
    title: str | None = None,
) -> ParsedDocument:
    # 2.1 Canonical Text Construction
    canonical_text_parts: list[str] = []
    block_nodes: list[tuple[BlockNode, dict[str, Any]]] = []

    current_offset = 0

    # Sort pages sequentially
    sorted_pages = sorted(extracted_doc.pages, key=lambda p: p.page_idx)

    for i, page in enumerate(sorted_pages):
        # Sort blocks sequentially within the page
        sorted_blocks = sorted(page.blocks, key=lambda b: b.reading_order_key)

        for j, block in enumerate(sorted_blocks):
            text = block.text or ""

            # 2.2 Tree Construction setup
            # Map intermediate BlockType to ParserBlockType
            b_type = block.type
            if b_type == BlockType.HEADING:
                p_type = (
                    ParserBlockType.PARA
                )  # Handled specially for HeadingNode, but BlockNode inside may be PARA
            elif b_type == BlockType.CODE:
                p_type = ParserBlockType.CODE
            elif b_type == BlockType.TABLE:
                p_type = ParserBlockType.TABLE
            elif b_type == BlockType.LIST:
                p_type = ParserBlockType.LIST
            else:
                p_type = ParserBlockType.PARA

            start_offset = current_offset
            end_offset = current_offset + len(text)

            # The actual node to add
            node = BlockNode(
                type=p_type,
                range=(start_offset, end_offset),
                metadata={"page_idx": page.page_idx, "reading_order_key": block.reading_order_key},
            )

            block_info = {"original_type": b_type, "text": text}

            block_nodes.append((node, block_info))

            canonical_text_parts.append(text)
            current_offset += len(text)

            # Appending inter-block separator
            if j < len(sorted_blocks) - 1:
                separator = "\n\n"
                canonical_text_parts.append(separator)
                current_offset += len(separator)

        # Appending inter-page separator
        if i < len(sorted_pages) - 1:
            if not sorted_blocks:
                # If page is completely empty, it shouldn't leave multiple
                # newlines without content, but let's follow spec
                pass
            separator = "\n\n\f\n\n"
            canonical_text_parts.append(separator)
            current_offset += len(separator)

    canonical_text = "".join(canonical_text_parts)

    # 2.2 Tree Construction & 2.3 Anchor Map and Determinism
    doc_id = extracted_doc.doc_id
    doc_anchor = hashlib.sha256(doc_id.encode("utf-8")).hexdigest()[:32]

    root_node = DocNode()
    stack: list[DocNode | HeadingNode] = [root_node]

    section_anchors: list[SectionAnchor] = []
    block_anchors: list[BlockAnchor] = []

    # Tracking for determinism
    heading_counts_at_level: dict[int, dict[str, int]] = {}
    current_section_path = ""
    block_ordinal_within_section = 0
    root_sec_anchor: str | None = None

    # Initialize heading counts
    for level in range(1, 7):
        heading_counts_at_level[level] = {}

    for node, block_info in block_nodes:
        original_type = block_info["original_type"]
        text = block_info["text"]

        if original_type == BlockType.HEADING:
            # determine level
            level = 1
            if text.startswith("#"):
                level = min(6, len(text) - len(text.lstrip("#")))

            # Pop stack
            while len(stack) > 1:
                top = stack[-1]
                if isinstance(top, HeadingNode) and top.level >= level:
                    stack.pop()
                else:
                    break

            # Deduplicate text
            clean_text = text.lstrip("#").strip()
            if not clean_text:
                clean_text = "heading"

            count = heading_counts_at_level.get(level, {}).get(clean_text, 0)
            if count > 0:
                heading_text = f"{clean_text}_{count - 1}"
            else:
                heading_text = clean_text

            if level not in heading_counts_at_level:
                heading_counts_at_level[level] = {}
            heading_counts_at_level[level][clean_text] = count + 1

            # Reset deeper level counts
            for level_idx in range(level + 1, 7):
                heading_counts_at_level[level_idx] = {}

            new_heading = HeadingNode(level=level, text=heading_text)
            stack[-1].children.append(new_heading)
            stack.append(new_heading)

            # Update path
            path_parts = []
            for item in stack[1:]:  # Skip DocNode
                if isinstance(item, HeadingNode):
                    path_parts.append(item.text)
            current_section_path = ">".join(path_parts)

            sec_anchor = hashlib.sha256(
                (doc_id + current_section_path).encode("utf-8")
            ).hexdigest()[:32]
            section_anchors.append(
                SectionAnchor(section_path=current_section_path, sec_anchor=sec_anchor)
            )

            block_ordinal_within_section = 0

        else:
            stack[-1].children.append(node)

            effective_path = current_section_path or "root"

            if effective_path == "root":
                if root_sec_anchor is None:
                    root_sec_anchor = hashlib.sha256(
                        (doc_id + effective_path).encode("utf-8")
                    ).hexdigest()[:32]
                    section_anchors.append(
                        SectionAnchor(section_path=effective_path, sec_anchor=root_sec_anchor)
                    )
                sec_anchor = root_sec_anchor
            else:
                sec_anchor = hashlib.sha256((doc_id + effective_path).encode("utf-8")).hexdigest()[
                    :32
                ]
            pass_anchor = hashlib.sha256(
                f"{sec_anchor}{node.type.value}{block_ordinal_within_section}".encode()
            ).hexdigest()[:32]

            block_anchors.append(
                BlockAnchor(
                    type=node.type,
                    section_path=effective_path,
                    pass_anchor=pass_anchor,
                    range=node.range,
                )
            )

            block_ordinal_within_section += 1

    # 2.4 Provenance and Metadata
    selected_engine_counts: dict[str, int] = {}
    for p in extracted_doc.pages:
        if p.selected_engine:
            selected_engine_counts[p.selected_engine] = (
                selected_engine_counts.get(p.selected_engine, 0) + 1
            )

    engine_runs_meta = [{"engine": r.engine, "status": r.status} for r in extracted_doc.engine_runs]

    metadata = {
        "parser_version": config.parser_version,
        "pdf_pipeline_version": extracted_doc.pipeline.pipeline_version,
        "selected_engine_counts": selected_engine_counts,
        "engine_runs": engine_runs_meta,
        "has_textual_content": bool(canonical_text.strip()),
    }

    # Remove duplicates from section anchors
    unique_sections = []
    seen_paths = set()
    for sa in section_anchors:
        if sa.section_path not in seen_paths:
            unique_sections.append(sa)
            seen_paths.add(sa.section_path)

    resolved_title = title
    if not resolved_title:
        title_meta = extracted_doc.source_pdf.metadata.get("title")
        if isinstance(title_meta, str) and title_meta:
            resolved_title = title_meta
        else:
            resolved_title = doc_id

    return ParsedDocument(
        doc_id=doc_id,
        title=resolved_title,
        canonical_text=canonical_text,
        structure_tree=root_node,
        anchors=AnchorMap(doc_anchor=doc_anchor, sections=unique_sections, blocks=block_anchors),
        metadata=metadata,
    )
