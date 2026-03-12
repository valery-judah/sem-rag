"""Alembic bootstrap helpers for lifecycle metadata schema migrations."""

from __future__ import annotations

import os
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

_ALEMBIC_INI_PATH = Path(__file__).resolve().parents[4] / "alembic.ini"
_POSTGRES_ADVISORY_LOCK_KEY = (24032026, 1)


def build_alembic_config(database_url: str | None = None) -> Config:
    """Build an Alembic config rooted at the repo-level `alembic.ini`."""

    config = Config(str(_ALEMBIC_INI_PATH))
    if database_url is not None:
        config.set_main_option("sqlalchemy.url", database_url)
    return config


def resolve_database_url(database_url: str | None = None) -> str:
    """Resolve the migration database URL from an explicit value or `DATABASE_URL`."""

    if database_url is not None:
        return database_url
    env_value = os.environ.get("DATABASE_URL")
    if env_value:
        return env_value
    raise RuntimeError("DATABASE_URL must be set for Alembic migrations")


def apply_migrations(database_url: str | None = None) -> None:
    """Apply all known migrations to the given database URL."""

    config = build_alembic_config(resolve_database_url(database_url))
    command.upgrade(config, "head")


def apply_migrations_with_lock(database_url: str | None = None) -> None:
    """Apply migrations, serializing concurrent PostgreSQL upgrades with an advisory lock."""

    resolved_database_url = resolve_database_url(database_url)
    config = build_alembic_config(resolved_database_url)
    engine = sa.create_engine(resolved_database_url)
    try:
        if engine.dialect.name != "postgresql":
            command.upgrade(config, "head")
            return
        with engine.connect() as connection:
            key_one, key_two = _POSTGRES_ADVISORY_LOCK_KEY
            connection.exec_driver_sql(f"SELECT pg_advisory_lock({key_one}, {key_two})")
            try:
                command.upgrade(config, "head")
            finally:
                connection.exec_driver_sql(f"SELECT pg_advisory_unlock({key_one}, {key_two})")
    finally:
        engine.dispose()
