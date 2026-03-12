"""Text-layer PDF extraction using pypdf."""

from __future__ import annotations

import re
from io import BytesIO

from pypdf import PdfReader

from doc_forge.artifacts import ExtractedArtifact, ExtractedArtifactBlock, ExtractedArtifactPage
from doc_forge.corpus import SourceType

from .base import ExtractionError, NoRecoverableTextError

_PARAGRAPH_SPLIT_PATTERN = re.compile(r"\n\s*\n+")


class PdfExtractor:
    """Extract page-aware text blocks from text-based PDFs."""

    VERSION = "pdf-v1"

    def extract(self, *, doc_id: str, raw_content: bytes) -> ExtractedArtifact:
        try:
            reader = PdfReader(BytesIO(raw_content))
        except Exception as exc:
            raise ExtractionError("pdf extraction failed to parse the source file") from exc

        pages: list[ExtractedArtifactPage] = []
        warnings: list[str] = []
        found_recoverable_text = False
        offset = 0

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            normalized_text = text.strip()
            if not normalized_text:
                warnings.append(f"page {page_number} contains no recoverable text")
                pages.append(ExtractedArtifactPage(page_number=page_number, blocks=[]))
                offset += len(text)
                continue

            if len(normalized_text) < 40:
                warnings.append(f"page {page_number} has a sparse text layer")

            blocks = self._page_blocks(text=text, page_number=page_number, start_offset=offset)
            if blocks:
                found_recoverable_text = True
            pages.append(ExtractedArtifactPage(page_number=page_number, blocks=blocks))
            offset += len(text)

        if not found_recoverable_text:
            raise NoRecoverableTextError("pdf extraction found no recoverable text layer")

        return ExtractedArtifact(
            doc_id=doc_id,
            source_type=SourceType.PDF,
            extractor_version=self.VERSION,
            pages=pages,
            warnings=warnings,
        )

    def _page_blocks(
        self,
        *,
        text: str,
        page_number: int,
        start_offset: int,
    ) -> list[ExtractedArtifactBlock]:
        blocks: list[ExtractedArtifactBlock] = []
        running_offset = start_offset

        for raw_block in _PARAGRAPH_SPLIT_PATTERN.split(text):
            block_text = raw_block.strip()
            block_length = len(raw_block)
            if not block_text:
                running_offset += block_length
                continue

            blocks.append(
                ExtractedArtifactBlock(
                    kind="text",
                    text=block_text,
                    order_index=len(blocks),
                    source_start_offset=running_offset,
                    source_end_offset=running_offset + len(block_text),
                    meta={"page_number": str(page_number)},
                )
            )
            running_offset += block_length

        if blocks:
            return blocks

        # Fallback to line-level recovery when paragraph splitting yields nothing useful.
        fallback_blocks: list[ExtractedArtifactBlock] = []
        line_offset = start_offset
        for raw_line in text.splitlines(keepends=True):
            stripped = raw_line.strip()
            if not stripped:
                line_offset += len(raw_line)
                continue
            fallback_blocks.append(
                ExtractedArtifactBlock(
                    kind="text",
                    text=stripped,
                    order_index=len(fallback_blocks),
                    source_start_offset=line_offset,
                    source_end_offset=line_offset + len(stripped),
                    meta={"page_number": str(page_number)},
                )
            )
            line_offset += len(raw_line)
        return fallback_blocks
