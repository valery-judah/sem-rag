from __future__ import annotations

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from parity.persistence import apply_migrations
from parity.persistence.migrations import build_alembic_config, resolve_database_url

pytestmark = pytest.mark.persistence


def test_initial_migration_creates_lifecycle_metadata_tables(db_url: str) -> None:
    apply_migrations(db_url)
    engine = sa.create_engine(db_url)
    try:
        inspector = sa.inspect(engine)
        assert set(inspector.get_table_names()) >= {
            "alembic_version",
            "chunks",
            "document_jobs",
            "documents",
            "lifecycle_events",
            "query_runs",
            "query_snapshots",
            "query_stage_traces",
            "query_answers",
            "sections",
        }
        query_run_columns = {column["name"] for column in inspector.get_columns("query_runs")}
        assert {"completed_at", "terminal_failure_json"}.issubset(query_run_columns)
    finally:
        engine.dispose()


def test_apply_migrations_still_works_as_helper(db_url: str) -> None:
    apply_migrations(db_url)
    engine = sa.create_engine(db_url)
    try:
        inspector = sa.inspect(engine)
        assert "documents" in inspector.get_table_names()
    finally:
        engine.dispose()


def test_build_alembic_config_uses_repo_alembic_ini(db_url: str) -> None:
    config = build_alembic_config(db_url)

    assert isinstance(config, Config)
    assert config.config_file_name is not None
    assert config.config_file_name.endswith("alembic.ini")
    assert config.get_main_option("script_location") == "src/parity/persistence/migrations"


def test_initial_revision_supports_downgrade_and_reupgrade(db_url: str) -> None:
    config = build_alembic_config(db_url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = sa.create_engine(db_url)
    try:
        inspector = sa.inspect(engine)
        assert "documents" not in inspector.get_table_names()
    finally:
        engine.dispose()

    command.upgrade(config, "head")

    engine = sa.create_engine(db_url)
    try:
        inspector = sa.inspect(engine)
        assert "documents" in inspector.get_table_names()
    finally:
        engine.dispose()


def test_resolve_database_url_reads_database_url_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///tmp/example.db")

    assert resolve_database_url() == "sqlite+pysqlite:///tmp/example.db"


def test_resolve_database_url_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL must be set"):
        resolve_database_url()
