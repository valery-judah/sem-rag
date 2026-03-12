from __future__ import annotations

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from parity.persistence import apply_migrations
from parity.persistence.migrations import (
    apply_migrations_with_lock,
    build_alembic_config,
    resolve_database_url,
)

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


def test_apply_migrations_with_lock_is_idempotent(db_url: str) -> None:
    apply_migrations_with_lock(db_url)
    apply_migrations_with_lock(db_url)
    engine = sa.create_engine(db_url)
    try:
        inspector = sa.inspect(engine)
        assert "documents" in inspector.get_table_names()
    finally:
        engine.dispose()


def test_apply_migrations_with_lock_uses_postgres_advisory_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executed_sql: list[str] = []
    upgrade_calls: list[Config] = []

    class _FakeConnection:
        def exec_driver_sql(self, statement: str) -> None:
            executed_sql.append(statement)

        def __enter__(self) -> _FakeConnection:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            del exc_type, exc, tb

    class _FakeEngine:
        dialect = type("Dialect", (), {"name": "postgresql"})()

        def connect(self) -> _FakeConnection:
            return _FakeConnection()

        def dispose(self) -> None:
            return None

    monkeypatch.setattr(
        "parity.persistence.migrations.sa.create_engine",
        lambda url: _FakeEngine(),
    )

    def _fake_upgrade(config: Config, revision: str) -> None:
        assert revision == "head"
        upgrade_calls.append(config)

    monkeypatch.setattr("parity.persistence.migrations.command.upgrade", _fake_upgrade)

    apply_migrations_with_lock("postgresql+psycopg://user:pass@localhost:5432/parity")

    assert upgrade_calls
    assert executed_sql == [
        "SELECT pg_advisory_lock(24032026, 1)",
        "SELECT pg_advisory_unlock(24032026, 1)",
    ]


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
