"""Conservative PDF normalization with optional heading inference."""

from __future__ import annotations

import re

from doc_forge.artifacts import ExtractedArtifact, NormalizedArtifact, NormalizedArtifactBlock

from .base import NormalizationError

_NUMBERED_HEADING_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+)$")


class PdfNormalizer:
    """Convert extracted PDF blocks into conservative normalized blocks."""

    VERSION = "pdf-v1"
    HEADING_THRESHOLD = 0.8

    def normalize(self, *, extracted: ExtractedArtifact) -> NormalizedArtifact:
        if not extracted.pages:
            raise NormalizationError("pdf normalization requires extracted content")

        blocks: list[NormalizedArtifactBlock] = []
        current_headings: list[str] = []
        inferred_heading_count = 0

        for page_index, page in enumerate(extracted.pages):
            if page_index > 0:
                blocks.append(
                    NormalizedArtifactBlock(
                        kind="page_break",
                        text="",
                        order_index=len(blocks),
                        heading_path=list(current_headings),
                        page_number=page.page_number,
                    )
                )

            for extracted_block in page.blocks:
                text = " ".join(line.strip() for line in extracted_block.text.splitlines()).strip()
                if not text:
                    continue

                heading_level, confidence = self._infer_heading(text)
                if heading_level is not None and confidence >= self.HEADING_THRESHOLD:
                    current_headings = current_headings[: heading_level - 1] + [text]
                    inferred_heading_count += 1
                    blocks.append(
                        NormalizedArtifactBlock(
                            kind="heading",
                            text=text,
                            order_index=len(blocks),
                            heading_level=heading_level,
                            heading_path=list(current_headings),
                            page_number=page.page_number,
                            source_start_offset=extracted_block.source_start_offset,
                            source_end_offset=extracted_block.source_end_offset,
                            meta={
                                "heading_confidence": f"{confidence:.2f}",
                                "inferred": "true",
                            },
                        )
                    )
                    continue

                blocks.append(
                    NormalizedArtifactBlock(
                        kind="paragraph",
                        text=text,
                        order_index=len(blocks),
                        heading_path=list(current_headings),
                        page_number=page.page_number,
                        source_start_offset=extracted_block.source_start_offset,
                        source_end_offset=extracted_block.source_end_offset,
                        meta={"heading_confidence": f"{confidence:.2f}"},
                    )
                )

        meta: dict[str, str] = {"inferred_heading_count": str(inferred_heading_count)}
        if inferred_heading_count == 0:
            meta["section_fallback"] = "synthetic_required"

        return NormalizedArtifact(
            doc_id=extracted.doc_id,
            source_type=extracted.source_type,
            normalizer_version=self.VERSION,
            blocks=blocks,
            warnings=list(extracted.warnings),
            meta=meta,
        )

    def _infer_heading(self, text: str) -> tuple[int | None, float]:
        if text.endswith((".", "?", "!", ";", ":")):
            return None, 0.1

        numbered_match = _NUMBERED_HEADING_PATTERN.match(text)
        if numbered_match is not None:
            depth = numbered_match.group(1).count(".") + 1
            return depth, 0.95

        words = text.split()
        if not words or len(words) > 10:
            return None, 0.2

        if text.isupper():
            return 1, 0.85

        capitalized_ratio = sum(word[:1].isupper() for word in words) / len(words)
        if capitalized_ratio >= 0.8 and len(words) <= 6:
            return 1, 0.8

        return None, 0.35
