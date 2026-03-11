"""Derive chunks from normalized artifacts and recovered sections."""

from __future__ import annotations

from collections import defaultdict

from parity._contracts import Chunk, Section
from parity.artifacts import NormalizedArtifact, NormalizedArtifactBlock
from parity.chunking.policy import MAX_TOKENS_PER_CHUNK, count_tokens
from parity.persistence import PersistedDocument


class ChunkingService:
    """Produce section-aware retrieval chunks."""

    def derive(
        self,
        *,
        document: PersistedDocument,
        artifact: NormalizedArtifact,
        sections: list[Section],
    ) -> list[Chunk]:
        section_by_path = {tuple(section.heading_path): section for section in sections}
        blocks_by_section: defaultdict[str, list[NormalizedArtifactBlock]] = defaultdict(list)
        for block in sorted(artifact.blocks, key=lambda item: item.order_index):
            if block.kind == "heading":
                continue
            key = tuple(block.heading_path or [document.title])
            section = section_by_path.get(key)
            if section is None:
                fallback_key = next(
                    (
                        tuple(section.heading_path)
                        for section in sections
                        if key[: len(section.heading_path)] == tuple(section.heading_path)
                    ),
                    tuple(sections[0].heading_path),
                )
                section = section_by_path[fallback_key]
            blocks_by_section[section.section_id].append(block)

        chunks: list[Chunk] = []
        ordinal = 0
        for section in sections:
            section_blocks = blocks_by_section.get(section.section_id, [])
            if not section_blocks:
                continue
            for text, page_start, page_end, start_offset, end_offset in self._split_blocks(
                section_blocks
            ):
                token_count = count_tokens(text)
                chunks.append(
                    Chunk(
                        chunk_id=f"{document.doc_id}:chunk:{ordinal}",
                        doc_id=document.doc_id,
                        section_id=section.section_id,
                        text=text,
                        ordinal=ordinal,
                        heading_path=section.heading_path,
                        page_start=page_start,
                        page_end=page_end,
                        source_start_offset=start_offset,
                        source_end_offset=end_offset,
                        lineage={"chunker_version": "v1"},
                        debug_metadata={"token_count": str(token_count)},
                    )
                )
                ordinal += 1
        return chunks

    def _split_blocks(
        self,
        blocks: list[NormalizedArtifactBlock],
    ) -> list[tuple[str, int | None, int | None, int | None, int | None]]:
        chunks: list[tuple[str, int | None, int | None, int | None, int | None]] = []
        parts: list[str] = []
        page_start: int | None = None
        page_end: int | None = None
        offset_start: int | None = None
        offset_end: int | None = None
        current_tokens = 0

        def flush() -> None:
            nonlocal parts, page_start, page_end, offset_start, offset_end, current_tokens
            if not parts:
                return
            chunks.append(("\n\n".join(parts), page_start, page_end, offset_start, offset_end))
            parts = []
            page_start = None
            page_end = None
            offset_start = None
            offset_end = None
            current_tokens = 0

        for block in blocks:
            block_text = block.text.strip()
            if not block_text:
                continue
            block_tokens = count_tokens(block_text)
            if parts and (
                current_tokens + block_tokens > MAX_TOKENS_PER_CHUNK or block.kind == "code"
            ):
                flush()
            if page_start is None:
                page_start = block.page_number
            page_end = block.page_number if block.page_number is not None else page_end
            if offset_start is None:
                offset_start = block.source_start_offset
            offset_end = block.source_end_offset
            parts.append(block_text)
            current_tokens += block_tokens
            if block.kind == "code":
                flush()

        flush()
        return chunks
