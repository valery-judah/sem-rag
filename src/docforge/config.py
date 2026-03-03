from __future__ import annotations

from pathlib import Path
from typing import Any

import tomllib
from pydantic import BaseModel, Field

from docforge.models import KnownContentType


class SourceConfig(BaseModel):
    type: str
    path: str
    doc_id: str | None = None
    url: str | None = None
    content_type: KnownContentType | str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    acl_scope: dict[str, Any] = Field(default_factory=dict)


class DocforgeConfig(BaseModel):
    sources: list[SourceConfig]


def load_config(path: Path | str) -> DocforgeConfig:
    config_path = Path(path)
    with config_path.open("rb") as file_obj:
        data = tomllib.load(file_obj)
    return DocforgeConfig.model_validate(data)
