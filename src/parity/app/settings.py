"""Internal runtime settings for the upload app."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    """Environment-backed runtime configuration."""

    database_url: str
    artifact_root: Path


def load_settings() -> AppSettings:
    """Load app settings from the process environment."""

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set")

    artifact_root = Path(os.environ.get("PARITY_ARTIFACT_ROOT", "data")).resolve()
    return AppSettings(
        database_url=database_url,
        artifact_root=artifact_root,
    )
