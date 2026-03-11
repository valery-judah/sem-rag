"""Markdown extraction that preserves structural cues and offsets."""

from __future__ import annotations

import re

from parity._contracts import SourceType
from parity.artifacts import ExtractedArtifact, ExtractedArtifactBlock, ExtractedArtifactPage

from .base import ExtractionError

_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+\S")
_CODE_FENCE_PATTERN = re.compile(r"^\s*```")


class MarkdownExtractor:
    """Extract Markdown into ordered inspectable blocks."""

    VERSION = "markdown-v1"

    def extract(self, *, doc_id: str, raw_content: bytes) -> ExtractedArtifact:
        try:
            text = raw_content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ExtractionError("markdown extraction requires valid UTF-8 input") from exc

        blocks: list[ExtractedArtifactBlock] = []
        current_lines: list[str] = []
        current_kind = "text"
        current_start: int | None = None
        in_code_block = False
        offset = 0

        def flush_current() -> None:
            nonlocal current_lines, current_kind, current_start
            if not current_lines or current_start is None:
                current_lines = []
                current_start = None
                current_kind = "text"
                return

            joined = "".join(current_lines)
            trimmed = joined.rstrip("\n")
            if trimmed:
                blocks.append(
                    ExtractedArtifactBlock(
                        kind=current_kind,
                        text=trimmed,
                        order_index=len(blocks),
                        source_start_offset=current_start,
                        source_end_offset=current_start + len(trimmed),
                    )
                )

            current_lines = []
            current_start = None
            current_kind = "text"

        for line in text.splitlines(keepends=True):
            stripped = line.strip()
            is_heading = not in_code_block and bool(_HEADING_PATTERN.match(line))
            is_code_fence = bool(_CODE_FENCE_PATTERN.match(line))

            if is_code_fence and not in_code_block:
                flush_current()
                current_kind = "code"
                current_start = offset
                current_lines.append(line)
                in_code_block = True
            elif is_code_fence and in_code_block:
                current_lines.append(line)
                flush_current()
                in_code_block = False
            elif in_code_block:
                current_lines.append(line)
            elif not stripped:
                flush_current()
            elif is_heading:
                flush_current()
                heading_text = line.rstrip("\n")
                blocks.append(
                    ExtractedArtifactBlock(
                        kind="heading",
                        text=heading_text,
                        order_index=len(blocks),
                        source_start_offset=offset,
                        source_end_offset=offset + len(heading_text),
                    )
                )
            else:
                if current_start is None:
                    current_start = offset
                current_lines.append(line)

            offset += len(line)

        flush_current()

        return ExtractedArtifact(
            doc_id=doc_id,
            source_type=SourceType.MARKDOWN,
            extractor_version=self.VERSION,
            pages=[ExtractedArtifactPage(page_number=1, blocks=blocks)],
        )
