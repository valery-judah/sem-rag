"""Container-friendly runtime entrypoint for API, worker, and migrations."""

from __future__ import annotations

import argparse
import os

import uvicorn

from parity.lifecycle.worker import main as worker_main
from parity.persistence import apply_migrations


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


def main() -> None:
    args = _build_parser().parse_args()
    if args.command == "api":
        uvicorn.run(
            "parity.app.api:app",
            host="0.0.0.0",
            port=int(os.environ.get("PORT", "8000")),
        )
        return
    if args.command == "worker":
        worker_main()
        return
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set")
    apply_migrations(database_url)


if __name__ == "__main__":
    main()
