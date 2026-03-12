"""Container-friendly runtime entrypoint for API, worker, and migrations."""

from __future__ import annotations

import argparse
import os

import uvicorn

from parity.lifecycle.worker import main as worker_main
from parity.persistence import apply_migrations_with_lock


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m parity.runtime",
        description="Run a parity runtime command.",
    )
    parser.add_argument(
        "command",
        choices=("api", "worker", "migrate"),
        help="Runtime command to execute.",
    )
    return parser


def _auto_migrate_enabled() -> bool:
    return os.environ.get("PARITY_AUTO_MIGRATE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _maybe_apply_migrations() -> None:
    if not _auto_migrate_enabled():
        return
    apply_migrations_with_lock()


def main() -> None:
    args = _build_parser().parse_args()
    if args.command == "api":
        _maybe_apply_migrations()
        uvicorn.run(
            "parity.app.api:app",
            host="0.0.0.0",
            port=int(os.environ.get("PORT", "8000")),
        )
        return
    if args.command == "worker":
        _maybe_apply_migrations()
        worker_main()
        return
    apply_migrations_with_lock()


if __name__ == "__main__":
    main()
