"""Dependency wiring for the internal upload app."""

from __future__ import annotations

from functools import cache, lru_cache
from typing import Annotated

import sqlalchemy as sa
from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.engine import Engine

from parity.artifacts import FilesystemArtifactStore
from parity.lifecycle.service import DocumentLifecycleService
from parity.persistence import SqlDocumentRepository, SqlLifecycleEventRepository
from parity.stages import RegisterDocumentStage

from .settings import AppSettings, load_settings


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Load and cache process-scoped runtime settings."""

    return load_settings()


@cache
def _build_engine(database_url: str) -> Engine:
    engine = sa.create_engine(database_url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
            del connection_record
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    return engine


def get_engine(settings: Annotated[AppSettings, Depends(get_settings)]) -> Engine:
    """Return the shared SQLAlchemy engine for the configured database."""

    return _build_engine(settings.database_url)


@cache
def _build_artifact_store(root: str) -> FilesystemArtifactStore:
    return FilesystemArtifactStore(root)


def get_artifact_store(
    settings: Annotated[AppSettings, Depends(get_settings)],
) -> FilesystemArtifactStore:
    """Return the shared artifact store rooted under the configured path."""

    return _build_artifact_store(str(settings.artifact_root))


def get_document_lifecycle_service(
    engine: Annotated[Engine, Depends(get_engine)],
    artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
) -> DocumentLifecycleService:
    """Build the lifecycle service used by the internal upload route."""

    register_stage = RegisterDocumentStage(
        engine=engine,
        documents=SqlDocumentRepository(engine),
        lifecycle_events=SqlLifecycleEventRepository(engine),
        artifact_store=artifact_store,
    )
    return DocumentLifecycleService(register_stage=register_stage)


def reset_runtime_caches() -> None:
    """Clear cached runtime singletons for tests."""

    get_settings.cache_clear()
    _build_engine.cache_clear()
    _build_artifact_store.cache_clear()
