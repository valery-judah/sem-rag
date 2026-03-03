from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from docforge.models import KnownContentType


class SourceConfig(BaseModel):
    type: str
    path: str
    # Internal/runtime-only: resolved filesystem path used for file IO.
    # This must not affect `source_ref`, which preserves `path` as configured.
    path_resolved: str | None = None
    doc_id: str | None = None
    url: str | None = None
    content_type: KnownContentType | str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    acl_scope: dict[str, Any] = Field(default_factory=dict)


class ParsingConfig(BaseModel):
    preserve_tables: bool = True
    preserve_code_blocks: bool = True


class SegmentationConfig(BaseModel):
    passage_tokens_target: int = Field(default=600, ge=300, le=800)
    overlap_ratio: float = Field(default=0.1, ge=0.0, le=0.15)


class DocforgeConfig(BaseModel):
    sources: list[SourceConfig]
    parsing: ParsingConfig = Field(default_factory=ParsingConfig)
    segmentation: SegmentationConfig = Field(default_factory=SegmentationConfig)


def load_config(path: Path | str) -> DocforgeConfig:
    config_path = Path(path)
    with config_path.open("rb") as file_obj:
        data = tomllib.load(file_obj)
    config = DocforgeConfig.model_validate(data)

    # Resolve relative `path` values relative to the TOML config's directory for IO,
    # while preserving `source_ref` as the configured path string.
    base_dir = config_path.resolve().parent
    for source in config.sources:
        source_path = Path(source.path)
        if source_path.is_absolute():
            source.path_resolved = source.path
        else:
            source.path_resolved = str(base_dir / source.path)

    return config
