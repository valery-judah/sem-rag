"""Operator CLI for loading query/eval bundle metadata into the observability store."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from doc_forge.observability import EvalOpsLoader


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan query bundles into the central eval/log observability store."
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Optional observability database URL override.",
    )
    parser.add_argument(
        "--context-root",
        default=None,
        help="Optional query bundle root override. Defaults to data/context/queries.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-schema", help="Create observability metadata tables.")

    scan = subparsers.add_parser("scan", help="Scan existing query bundles into the store.")
    scan.add_argument(
        "--loop",
        action="store_true",
        help="Keep scanning forever instead of exiting after one pass.",
    )
    scan.add_argument(
        "--interval-seconds",
        type=float,
        default=10.0,
        help="Polling interval when --loop is enabled.",
    )
    return parser.parse_args(list(argv))


def _build_loader(database_url: str | None, context_root: str | None) -> EvalOpsLoader:
    return EvalOpsLoader.from_database_url(
        database_url=database_url,
        context_root=None if context_root is None else Path(context_root),
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    loader = _build_loader(args.database_url, args.context_root)

    if args.command == "init-schema":
        loader.create_schema()
        return 0

    if args.loop:
        loader.scan_forever(interval_seconds=args.interval_seconds)
        return 0

    stats = loader.scan_once()
    print(
        f"scanned_bundles={stats.scanned_bundles} indexed_bundles={stats.indexed_bundles}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
