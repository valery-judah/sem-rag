from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

BBox = tuple[float, float, float, float]


@dataclass(slots=True)
class ParsedBlock:
    type: str
    text: str
    bbox: BBox | None = None
    order: int | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedTable:
    rendered: str
    canonical_rows: list[str]
    cells: list[list[str]] | None = None


@dataclass(slots=True)
class ParsedPage:
    page_index: int
    canonical_text: str
    width: float | None = None
    height: float | None = None
    blocks: list[ParsedBlock] = field(default_factory=list)
    tables: list[ParsedTable] = field(default_factory=list)


@dataclass(slots=True)
class ParsedChunk:
    chunk_id: str
    page_start: int
    page_end: int
    text: str
    heading_path: list[str] = field(default_factory=list)
    type: str = "passage"
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedDocument:
    doc_id: str
    source_uri: str
    page_count: int
    pages: list[ParsedPage]
    chunks: list[ParsedChunk]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
