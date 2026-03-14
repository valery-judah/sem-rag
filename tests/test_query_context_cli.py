from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from doc_forge.devtools import query_context
from doc_forge.identifiers import QueryId
from doc_forge.query import (
    QueryContextAssetPaths,
    QueryContextLogAsset,
    QueryContextManifest,
    QueryContextSourceKind,
)


class _FakeCollector:
    def __init__(self, bundle_root: Path, manifest: QueryContextManifest) -> None:
        self.bundle_root = bundle_root
        self._manifest = manifest
        self.collected_query_ids: list[str] = []
        self.rendered_query_ids: list[str] = []

    def collect(self, query_id: QueryId):
        self.collected_query_ids.append(query_id)

        class _Result:
            def __init__(self, bundle_root: Path) -> None:
                self.bundle_root = bundle_root

        return _Result(self.bundle_root)

    def render_summary(self, query_id: QueryId) -> str:
        self.rendered_query_ids.append(query_id)
        return f"bundle_root={self.bundle_root}\nquery_id={self._manifest.query_id}"


def test_collect_query_context_cli_prints_bundle_root(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    collector = _FakeCollector(
        bundle_root=tmp_path / "data" / "context" / "queries" / "qry-1",
        manifest=QueryContextManifest(
            query_id="qry-1",
            collected_at=datetime(2026, 3, 13, tzinfo=UTC),
            source_kind=QueryContextSourceKind.UNKNOWN,
        ),
    )
    monkeypatch.setattr(query_context, "_build_collector", lambda database_url: collector)

    exit_code = query_context.main(["collect-query-context", "--query-id", "qry-1"])

    assert exit_code == 0
    assert collector.collected_query_ids == ["qry-1"]
    assert capsys.readouterr().out.strip() == str(collector.bundle_root)


show_query_context_cli_prints_summary(monkeypatch, tmp_path: pathlib.Path, capsys) -> None:
    collector = _FakeCollector(
        bundle_root=tmp_path / "data" / "context" / "queries" / "qry-2",
        manifest=QueryContextManifest(
            query_id="qry-2",
            collected_at=datetime(2026, 3, 13, tzinfo=UTC),
            source_kind=QueryContextSourceKind.E2E,
            run_id="sess-1",
            test_id="e2e::test",
            assets=QueryContextAssetPaths(summary="summary.json"),
            log_assets=[
                QueryContextLogAsset(
                    service="api",
                    source_path="/tmp/api.jsonl",
                    bundle_path="logs/api.jsonl",
                    matched_line_count=2,
                )
            ],
        ),
    )
    monkeypatch.setattr(query_context, "_build_collector", lambda database_url: collector)

    exit_code = query_context.main(["show-query-context", "--query-id", "qry-2"])

    assert exit_code == 0
    assert collector.rendered_query_ids == ["qry-2"]
    assert "bundle_root=" in capsys.readouterr().out
