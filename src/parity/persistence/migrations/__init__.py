"""Alembic bootstrap helpers for lifecycle metadata schema migrations."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def apply_migrations(database_url: str) -> None:
    """Apply all known migrations to the given database URL."""

    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parent))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
