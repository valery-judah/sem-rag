from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ParseStatus(StrEnum):
    OK = "ok"
    EMPTY = "empty"
    ERROR = "error"
    TIMEOUT = "timeout"


class BlockType(StrEnum):
    HEADING = "heading"
    PARA = "para"
    LIST = "list"
    TABLE = "table"
    CODE = "code"
    CAPTION = "caption"
    FOOTER = "footer"
    HEADER = "header"
    UNKNOWN = "unknown"


class BlockSource(BaseModel):
    engine: str
    engine_artifact_ref: str
    engine_block_ref: str | None = None


class BlockCandidate(BaseModel):
    block_id: str
    type: BlockType
    text: str
    page_idx: int
    bbox: tuple[float, float, float, float] | None = None
    poly: list[tuple[float, float]] | None = None
    reading_order_key: str
    source: BlockSource
    confidence: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssetType(StrEnum):
    IMAGE = "image"
    FIGURE = "figure"
    EQUATION = "equation"
    TABLE_RENDER = "table_render"


class AssetCandidate(BaseModel):
    asset_id: str
    type: AssetType
    page_idx: int
    path_or_ref: str
    bbox_or_poly: Any = None
    source: BlockSource
    metadata: dict[str, Any] = Field(default_factory=dict)


class PageSignals(BaseModel):
    char_count: int = 0
    block_count: int = 0
    line_count: int = 0
    duplicate_line_ratio: float = 0.0
    heading_like_count: int = 0
    has_coords: bool = False
    asset_count: int = 0

    @classmethod
    def compute(cls, blocks: list[BlockCandidate], assets: list[AssetCandidate]) -> "PageSignals":
        char_count = 0
        block_count = len(blocks)
        lines = []
        heading_like_count = 0
        coords_count = 0

        for block in blocks:
            text = block.text or ""
            # Char count excluding whitespace
            char_count += len("".join(text.split()))

            # Line splitting
            block_lines = [line.strip() for line in text.split("\n") if line.strip()]
            lines.extend(block_lines)

            # Heading heuristics
            if block.type == BlockType.HEADING or (text.strip().startswith("#")):
                heading_like_count += 1

            # Coords check
            if block.bbox is not None or block.poly is not None:
                coords_count += 1

        line_count = len(lines)
        unique_lines = len(set(lines))
        duplicate_line_ratio = 0.0
        if line_count > 0:
            duplicate_line_ratio = (line_count - unique_lines) / line_count

        has_coords = coords_count > (block_count / 2) if block_count > 0 else False

        return cls(
            char_count=char_count,
            block_count=block_count,
            line_count=line_count,
            duplicate_line_ratio=duplicate_line_ratio,
            heading_like_count=heading_like_count,
            has_coords=has_coords,
            asset_count=len(assets),
        )


class PageCandidate(BaseModel):
    page_idx: int
    blocks: list[BlockCandidate] = Field(default_factory=list)
    assets: list[AssetCandidate] = Field(default_factory=list)
    signals: PageSignals = Field(default_factory=PageSignals)
    status: ParseStatus

    @classmethod
    def empty(cls, page_idx: int) -> "PageCandidate":
        return cls(
            page_idx=page_idx,
            blocks=[],
            assets=[],
            status=ParseStatus.EMPTY,
            signals=PageSignals(),
        )

    @classmethod
    def placeholder_error(cls, page_idx: int, message: str | None = None) -> "PageCandidate":
        block = BlockCandidate(
            block_id=f"placeholder_p{page_idx}",
            type=BlockType.UNKNOWN,
            text=message or f"[UNPARSEABLE PAGE {page_idx}]",
            page_idx=page_idx,
            reading_order_key="0",
            source=BlockSource(
                engine="pipeline",
                engine_artifact_ref="none",
                engine_block_ref="none",
            ),
        )
        return cls(
            page_idx=page_idx,
            blocks=[block],
            assets=[],
            status=ParseStatus.ERROR,
            signals=PageSignals(),
        )
