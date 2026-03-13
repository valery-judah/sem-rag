"""Structured JSON logging configuration for the internal app."""

from __future__ import annotations

import logging
import sys

import structlog

_CONFIGURED = False


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a strongly-typed standard library logger."""
    return structlog.stdlib.get_logger(name)


def configure_logging(*, service: str, environment: str, level: str) -> None:
    """Configure process-wide JSON logging once."""

    global _CONFIGURED
    if _CONFIGURED:
        return

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
        _inject_static_fields(service=service, environment=environment),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level.upper())
    logging.captureWarnings(True)

    for logger_name in (
        "alembic",
        "alembic.runtime.migration",
        "httpx",
        "huggingface_hub",
        "huggingface_hub.utils._http",
        "py.warnings",
        "sentence_transformers",
        "transformers",
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "doc_forge",
    ):
        foreign_logger = logging.getLogger(logger_name)
        foreign_logger.handlers.clear()
        foreign_logger.propagate = True
        foreign_logger.disabled = False
        foreign_logger.setLevel(logging.NOTSET)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )
    _CONFIGURED = True


def reset_logging() -> None:
    """Reset logging configuration for tests."""

    global _CONFIGURED
    logging.getLogger().handlers.clear()
    logging.captureWarnings(False)
    structlog.reset_defaults()
    structlog.contextvars.clear_contextvars()
    _CONFIGURED = False


def _inject_static_fields(*, service: str, environment: str) -> structlog.types.Processor:
    def processor(
        logger: object,
        method_name: str,
        event_dict: structlog.types.EventDict,
    ) -> structlog.types.EventDict:
        del logger, method_name
        event_dict["service"] = service
        event_dict["environment"] = environment
        return event_dict

    return processor
