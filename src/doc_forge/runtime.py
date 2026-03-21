"""Container-friendly runtime entrypoint for API, worker, and migrations."""

from __future__ import annotations

import argparse

import uvicorn

from doc_forge.app.logging import configure_logging
from doc_forge.app.settings import Settings, get_settings
from doc_forge.lifecycle.worker import main as worker_main
from doc_forge.persistence import apply_migrations_with_lock


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m doc_forge.runtime",
        description="Run a doc_forge runtime command.",
    )
    parser.add_argument(
        "command",
        choices=("api", "worker", "migrate"),
        help="Runtime command to execute.",
    )
    return parser


def _configure_runtime_logging(settings: Settings, command: str) -> None:
    default_service_name = {
        "api": "doc_forge-api",
        "worker": "doc_forge-worker",
        "migrate": "doc_forge-migrate",
    }[command]
    service_name = (
        settings.service_name if settings.service_name != "doc_forge-api" else default_service_name
    )
    configure_logging(
        service=service_name,
        environment=settings.environment,
        level=settings.log_level,
    )


def main() -> None:
    args = _build_parser().parse_args()
    settings = get_settings()
    _configure_runtime_logging(settings, args.command)
    if args.command == "api":
        if settings.auto_migrate:
            apply_migrations_with_lock()
        uvicorn.run(
            "doc_forge.app.api:app",
            host="0.0.0.0",
            port=settings.port,
            log_config=None,
        )
        return
    if args.command == "worker":
        if settings.auto_migrate:
            apply_migrations_with_lock()
        worker_main()
        return
    apply_migrations_with_lock()


if __name__ == "__main__":
    main()
