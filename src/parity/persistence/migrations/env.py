"""Alembic environment for lifecycle metadata migrations."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from parity.persistence.jobs import document_jobs_table
from parity.persistence.models import metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata
_ = document_jobs_table


def _configured_database_url() -> str:
    configured = config.get_main_option("sqlalchemy.url")
    if configured:
        return configured
    env_value = os.environ.get("DATABASE_URL")
    if env_value:
        return env_value
    raise RuntimeError("DATABASE_URL must be set for Alembic migrations")


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = _configured_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _configured_database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
