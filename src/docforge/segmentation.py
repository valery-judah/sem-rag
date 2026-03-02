import enum
from dataclasses import dataclass


class BlockType(enum.StrEnum):
    TABLE = "table"
    CODE = "code"
    PARA = "para"
    LIST = "list"
    HEADING = "heading"


class SegmentType(enum.StrEnum):
    PASSAGE = "PASSAGE"


@dataclass
class TextSpan:
    start_char_offset: int
    end_char_offset: int


@dataclass
class BlockAnchor:
    block_type: BlockType
    ref: str
    span: TextSpan


@dataclass
class PassageSegment:
    type: SegmentType
    text: str
    start_char_offset: int
    end_char_offset: int


def segment_document(canonical_text: str, blocks: list[BlockAnchor]) -> list[PassageSegment]:
    """
    Produce PASSAGE segments from a document based on character offset blocks.

    This is the M0 minimal segmenter.
    """
    segments = []

    text_len = len(canonical_text)

    for block in blocks:
        # Clamp bounds
        actual_start = max(0, block.span.start_char_offset)
        actual_end = min(text_len, block.span.end_char_offset)

        if actual_start >= actual_end:
            continue

        text = canonical_text[actual_start:actual_end]

        # Avoid empty or whitespace-only passages
        if not text.strip():
            continue

        segments.append(
            PassageSegment(
                type=SegmentType.PASSAGE,
                text=text,
                start_char_offset=actual_start,
                end_char_offset=actual_end,
            )
        )

    return segments
