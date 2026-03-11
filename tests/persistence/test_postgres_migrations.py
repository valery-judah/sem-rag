from __future__ import annotations

import pytest
import sqlalchemy as sa

from parity.persistence import apply_migrations

pytestmark = pytest.mark.persistence


def test_initial_migration_creates_lifecycle_metadata_tables(db_url: str) -> None:
    apply_migrations(db_url)
    engine = sa.create_engine(db_url)
    try:
        inspector = sa.inspect(engine)
        assert set(inspector.get_table_names()) >= {
            "alembic_version",
            "document_jobs",
            "documents",
            "lifecycle_events",
        }
    finally:
        engine.dispose()
