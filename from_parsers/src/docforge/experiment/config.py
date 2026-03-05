from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ChunkingConfig:
    target_chars: int = 1200
    overlap_chars: int = 120
    min_chars: int = 250


@dataclass(slots=True)
class PostprocessConfig:
    dehyphenate: bool = True
    dedupe_repeated_lines: bool = True
    strip_blank_lines: bool = True
    strip_repeated_margin_boilerplate: bool = True


@dataclass(slots=True)
class VariantConfig:
    variant_id: str
    extractor: str = "pypdf"
    routing: dict[str, Any] = field(default_factory=dict)
    ocr: dict[str, Any] = field(default_factory=dict)
    tables: dict[str, Any] = field(default_factory=dict)
    postprocess: PostprocessConfig = field(default_factory=PostprocessConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)

    @classmethod
    def from_toml_path(cls, path: Path) -> VariantConfig:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        default_variant_id = path.stem
        return cls.from_mapping(raw, default_variant_id=default_variant_id)

    @classmethod
    def from_mapping(
        cls,
        raw: dict[str, Any],
        *,
        default_variant_id: str = "baseline",
    ) -> VariantConfig:
        variant_id_raw = raw.get("variant_id", default_variant_id)
        extractor_raw = raw.get("extractor", "pypdf")

        postprocess_raw = raw.get("postprocess")
        if not isinstance(postprocess_raw, dict):
            postprocess_raw = {}

        chunking_raw = raw.get("chunking")
        if not isinstance(chunking_raw, dict):
            chunking_raw = {}

        routing_raw = raw.get("routing")
        if not isinstance(routing_raw, dict):
            routing_raw = {}

        ocr_raw = raw.get("ocr")
        if not isinstance(ocr_raw, dict):
            ocr_raw = {}

        tables_raw = raw.get("tables")
        if not isinstance(tables_raw, dict):
            tables_raw = {}

        return cls(
            variant_id=str(variant_id_raw),
            extractor=str(extractor_raw),
            routing=routing_raw,
            ocr=ocr_raw,
            tables=tables_raw,
            postprocess=PostprocessConfig(
                dehyphenate=bool(postprocess_raw.get("dehyphenate", True)),
                dedupe_repeated_lines=bool(postprocess_raw.get("dedupe_repeated_lines", True)),
                strip_blank_lines=bool(postprocess_raw.get("strip_blank_lines", True)),
                strip_repeated_margin_boilerplate=bool(
                    postprocess_raw.get("strip_repeated_margin_boilerplate", True)
                ),
            ),
            chunking=ChunkingConfig(
                target_chars=max(1, int(chunking_raw.get("target_chars", 1200))),
                overlap_chars=max(0, int(chunking_raw.get("overlap_chars", 120))),
                min_chars=max(1, int(chunking_raw.get("min_chars", 250))),
            ),
        )
