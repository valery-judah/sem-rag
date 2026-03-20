# ruff: noqa: B008
# pyright: reportUnusedFunction=false
from __future__ import annotations

from typing import Annotated

import sqlalchemy as sa
import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy.engine import Engine

from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.indexing.base import VectorStore

from ..api_examples import HEALTHZ_ENDPOINT_DESCRIPTION, READYZ_ENDPOINT_DESCRIPTION
from ..deps import get_artifact_store, get_engine, get_vector_store
from ..logging import get_logger as get_app_logger
from ..schemas import ErrorResponse, SystemStatusResponse


def get_logger() -> structlog.stdlib.BoundLogger:
    return get_app_logger(__name__)


router = APIRouter(tags=["System"])


@router.get(
    "/healthz",
    response_model=SystemStatusResponse,
    summary="Health Check",
    description=HEALTHZ_ENDPOINT_DESCRIPTION,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
def healthz() -> SystemStatusResponse:
    return SystemStatusResponse(status="ok")


@router.get(
    "/readyz",
    response_model=SystemStatusResponse,
    summary="Readiness Check",
    description=READYZ_ENDPOINT_DESCRIPTION,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Readiness check failed due to unreachable dependencies",
        },
    },
)
def readyz(
    engine: Annotated[Engine, Depends(get_engine)],
    artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
    logger: structlog.stdlib.BoundLogger = Depends(get_logger),
) -> SystemStatusResponse:
    logger.info("system.readyz.started")
    try:
        with engine.connect() as connection:
            connection.execute(sa.text("SELECT 1"))
        artifact_store.ensure_root_writable()
        vector_store.smoke_query(doc_id="healthcheck", text="healthcheck", k=1)
    except Exception:
        logger.exception(
            "system.readyz.failed",
            http_status=500,
            error_code="ready_check_failed",
        )
        raise
    logger.info("system.readyz.completed", http_status=200, status="ok")
    return SystemStatusResponse(status="ok")
