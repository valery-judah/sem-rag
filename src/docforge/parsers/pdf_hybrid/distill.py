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

    # Pre-flatten blocks to handle cross-page merging
    flat_blocks: list[tuple[int, Any]] = [] # (page_idx, block)
    for page in sorted_pages:
        for block in sorted(page.blocks, key=lambda b: b.reading_order_key):
            flat_blocks.append((page.page_idx, block))

    # Apply heuristic to merge broken paragraphs across pages
    merged_blocks: list[tuple[int, Any]] = []
    for page_idx, block in flat_blocks:
        if not merged_blocks:
            merged_blocks.append((page_idx, block))
            continue
            
        prev_page_idx, prev_block = merged_blocks[-1]
        
        # Check if we should merge with the previous block
        # Criteria:
        # 1. Blocks are on different pages (specifically, adjacent pages)
        # 2. Both blocks are PARA type
        # 3. Previous block does not end with terminal punctuation
        # 4. Current block starts with lowercase letter
        
        should_merge = False
        if (page_idx > prev_page_idx and 
            prev_block.type == BlockType.PARA and 
            block.type == BlockType.PARA):
            
            prev_text = (prev_block.text or "").strip()
            curr_text = (block.text or "").strip()
            
            if prev_text and curr_text:
                if not prev_text[-1] in (".", "?", "!", ":", '"', "'"):
                    if curr_text[0].islower():
                        should_merge = True

        if should_merge:
            # Merge current block into previous block
            prev_block.text = f"{prev_block.text.rstrip()} {block.text.lstrip()}"
            # Extend polygon/bbox if necessary (omitted here as it's complex and not strictly needed for text extraction)
        else:
            merged_blocks.append((page_idx, block))

        for i, (page_idx, block) in enumerate(merged_blocks):
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
            metadata={"page_idx": page_idx, "reading_order_key": block.reading_order_key},
        )

        block_info = {"original_type": b_type, "text": text}

        block_nodes.append((node, block_info))

        canonical_text_parts.append(text)
        current_offset += len(text)

        # Determine separator
        if i < len(merged_blocks) - 1:
            next_page_idx, _ = merged_blocks[i + 1]
            if next_page_idx == page_idx:
                separator = "\n\n"
            else:
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
