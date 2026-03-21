# ruff: noqa: B008
# pyright: reportUnusedFunction=false
"""FastAPI app for the local document lifecycle and query service."""

from __future__ import annotations

import importlib.metadata

import structlog
from fastapi import (
    FastAPI,
    Request,
)
from fastapi.responses import JSONResponse

from .logging import configure_logging
from .logging import get_logger as get_app_logger
from .routers import documents, internal, queries, system
from .schemas import ErrorResponse
from .settings import Settings, get_settings


def get_logger() -> structlog.stdlib.BoundLogger:
    return get_app_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the local FastAPI service app."""

    settings = settings or get_settings()

    configure_logging(
        service=settings.service_name,
        environment=settings.environment,
        level=settings.log_level,
    )

    try:
        app_version = importlib.metadata.version("doc_forge")
    except importlib.metadata.PackageNotFoundError:
        app_version = "0.0.0-dev"

    app = FastAPI(
        title="Doc Forge Local API",
        description="Stable localhost document lifecycle and query API.",
        version=app_version,
        docs_url="/docs" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        redoc_url=None,
    )

    app.state.settings = settings

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler for unhandled exceptions."""
        get_logger().exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(detail="Internal server error").model_dump(),
        )

    app.include_router(system.router)
    app.include_router(documents.router)
    app.include_router(queries.router)
    app.include_router(internal.router)

    return app


app = create_app()
