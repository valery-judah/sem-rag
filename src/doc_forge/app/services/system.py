from __future__ import annotations

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.engine import Engine

from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.indexing.base import VectorStore

from ..logging import get_logger as get_app_logger
from ..schemas import SystemStatusResponse

logger = get_app_logger(__name__)


class SystemAppService:
    """Orchestrates system-level endpoints such as health and readiness checks."""

    def __init__(
        self,
        engine: Engine,
        artifact_store: FilesystemArtifactStore,
        vector_store: VectorStore,
    ) -> None:
        self._engine = engine
        self._artifact_store = artifact_store
        self._vector_store = vector_store

    def get_health(self) -> SystemStatusResponse:
        """Return a basic health check response."""
        return SystemStatusResponse(status="ok")

    def get_readiness(self) -> SystemStatusResponse:
        """Perform a deep readiness check across infrastructure dependencies."""
        logger.info("system.readyz.started")
        try:
            with self._engine.connect() as connection:
                connection.execute(sa.text("SELECT 1"))
            self._artifact_store.ensure_root_writable()
            self._vector_store.smoke_query(doc_id="healthcheck", text="healthcheck", k=1)
        except Exception as e:
            logger.exception(
                "system.readyz.failed",
                http_status=500,
                error_code="ready_check_failed",
            )
            raise HTTPException(
                status_code=500,
                detail="ready_check_failed",
            ) from e

        logger.info("system.readyz.completed", http_status=200, status="ok")
        return SystemStatusResponse(status="ok")
