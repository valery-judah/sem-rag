"""Operator CLI for query-centric context bundles."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from doc_forge.query.context_archive import QueryContextCollector


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect or inspect a query context bundle.")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Optional database URL override. Defaults to DATABASE_URL/.env settings.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser(
        "collect-query-context",
        help="Collect persisted review, replay, and log context for a query.",
    )
    collect.add_argument("--query-id", required=True, help="Query identifier to collect.")

    show = subparsers.add_parser(
        "show-query-context",
        help="Show the paths and high-signal metadata for an existing query bundle.",
    )
    show.add_argument("--query-id", required=True, help="Query identifier to inspect.")
    return parser.parse_args(list(argv))


def _build_collector(database_url: str | None) -> QueryContextCollector:
    return QueryContextCollector.from_database_url(database_url=database_url)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    collector = _build_collector(args.database_url)

    if args.command == "collect-query-context":
        result = collector.collect(args.query_id)
        print(result.bundle_root)
        return 0

    print(collector.render_summary(args.query_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
