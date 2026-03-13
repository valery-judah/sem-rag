"""Container-friendly runtime entrypoint for API, worker, and migrations."""

from __future__ import annotations

import argparse
import os

import uvicorn

from doc_forge.app.logging import configure_logging
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


def _auto_migrate_enabled() -> bool:
    return os.environ.get("DOC_FORGE_AUTO_MIGRATE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _maybe_apply_migrations() -> None:
    if not _auto_migrate_enabled():
        return
    apply_migrations_with_lock()


def _configure_runtime_logging(command: str) -> None:
    default_service_name = {
        "api": "doc_forge-api",
        "worker": "doc_forge-worker",
        "migrate": "doc_forge-migrate",
    }[command]
    configure_logging(
        service=os.environ.get("DOC_FORGE_SERVICE_NAME", default_service_name),
        environment=os.environ.get("DOC_FORGE_ENVIRONMENT", "prod"),
        level=os.environ.get("DOC_FORGE_LOG_LEVEL", "INFO"),
    )


def main() -> None:
    args = _build_parser().parse_args()
    _configure_runtime_logging(args.command)
    if args.command == "api":
        _maybe_apply_migrations()
        uvicorn.run(
            "doc_forge.app.api:app",
            host="0.0.0.0",
            port=int(os.environ.get("PORT", "8000")),
            log_config=None,
        )
        return
    if args.command == "worker":
        _maybe_apply_migrations()
        worker_main()
        return
    apply_migrations_with_lock()


if __name__ == "__main__":
    main()
