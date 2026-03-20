# ruff: noqa: B008
# pyright: reportUnusedFunction=false
"""FastAPI app for the local document lifecycle and query service."""

from __future__ import annotations

import importlib.metadata
import os
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

import structlog
from fastapi import (
    FastAPI,
    Request,
    Response,
)
from fastapi.responses import JSONResponse
from structlog.contextvars import bind_contextvars, clear_contextvars

from .logging import configure_logging
from .logging import get_logger as get_app_logger
from .routers import documents, internal, queries, system
from .schemas import ErrorResponse


def get_logger() -> structlog.stdlib.BoundLogger:
    return get_app_logger(__name__)


def create_app() -> FastAPI:
    """Create the local FastAPI service app."""

    environment = os.environ.get("DOC_FORGE_ENVIRONMENT", "prod")
    configure_logging(
        service=os.environ.get("DOC_FORGE_SERVICE_NAME", "doc_forge-api"),
        environment=environment,
        level=os.environ.get("DOC_FORGE_LOG_LEVEL", "INFO"),
    )

    enable_swagger_env = os.environ.get("DOC_FORGE_ENABLE_SWAGGER", "false").lower() == "true"
    enable_swagger = environment == "dev" or enable_swagger_env

    try:
        app_version = importlib.metadata.version("doc_forge")
    except importlib.metadata.PackageNotFoundError:
        app_version = "0.0.0-dev"

    app = FastAPI(
        title="Doc Forge Local API",
        description="Stable localhost document lifecycle and query API.",
        version=app_version,
        docs_url="/docs" if enable_swagger else None,
        openapi_url="/openapi.json" if enable_swagger else None,
        redoc_url=None,
    )

    @app.middleware("http")
    async def request_logging_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = f"req-{uuid4().hex}"
        bind_contextvars(request_id=request_id)
        started_at = perf_counter()
        get_logger().info(
            "http.request.started",
            method=request.method,
            path=request.url.path,
        )

        unhandled_exception = False
        try:
            response = await call_next(request)
        except Exception:
            unhandled_exception = True
            duration_ms = int((perf_counter() - started_at) * 1000)
            get_logger().exception(
                "http.request.completed",
                method=request.method,
                path=request.url.path,
                http_status=500,
                status=500,
                duration_ms=duration_ms,
            )
            response = JSONResponse(
                status_code=500,
                content=ErrorResponse(detail="Internal server error").model_dump(),
            )

        duration_ms = int((perf_counter() - started_at) * 1000)
        response.headers["x-request-id"] = request_id

        if not unhandled_exception:
            get_logger().info(
                "http.request.completed",
                method=request.method,
                path=request.url.path,
                http_status=response.status_code,
                status=response.status_code,
                duration_ms=duration_ms,
            )

        clear_contextvars()
        return response

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
