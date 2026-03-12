"""Markdown normalization that preserves headings and block boundaries."""

from __future__ import annotations

import re

from doc_forge.artifacts import ExtractedArtifact, NormalizedArtifact, NormalizedArtifactBlock

from .base import NormalizationError

_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_ITEM_PATTERN = re.compile(r"^([-*+]|\d+\.)\s+")


class MarkdownNormalizer:
    """Convert extracted Markdown blocks into canonical normalized blocks."""

    VERSION = "markdown-v1"

    def normalize(self, *, extracted: ExtractedArtifact) -> NormalizedArtifact:
        if not extracted.pages:
            raise NormalizationError("markdown normalization requires extracted content")

        blocks: list[NormalizedArtifactBlock] = []
        current_headings: list[str] = []

        for page in extracted.pages:
            for extracted_block in page.blocks:
                text = extracted_block.text.strip("\n")
                if not text:
                    continue

                kind = "paragraph"
                heading_level: int | None = None
                heading_path = list(current_headings)

                heading_match = _HEADING_PATTERN.match(text)
                if extracted_block.kind == "heading" and heading_match is not None:
                    heading_level = len(heading_match.group(1))
                    heading_text = heading_match.group(2).strip()
                    current_headings = current_headings[: heading_level - 1] + [heading_text]
                    heading_path = list(current_headings)
                    text = heading_text
                    kind = "heading"
                elif extracted_block.kind == "code":
                    kind = "code"
                elif _LIST_ITEM_PATTERN.match(text):
                    kind = "list_item"
                elif text.startswith(">"):
                    kind = "quote"

                blocks.append(
                    NormalizedArtifactBlock(
                        kind=kind,
                        text=text,
                        order_index=len(blocks),
                        heading_level=heading_level,
                        heading_path=heading_path,
                        page_number=page.page_number,
                        source_start_offset=extracted_block.source_start_offset,
                        source_end_offset=extracted_block.source_end_offset,
                        meta={"source_kind": extracted_block.kind},
                    )
                )

        return NormalizedArtifact(
            doc_id=extracted.doc_id,
            source_type=extracted.source_type,
            normalizer_version=self.VERSION,
            blocks=blocks,
            warnings=list(extracted.warnings),
            meta={"heading_count": str(sum(block.kind == "heading" for block in blocks))},
        )
