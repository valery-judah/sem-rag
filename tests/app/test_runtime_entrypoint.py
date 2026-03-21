from __future__ import annotations

import sys

import pytest

from doc_forge import runtime
from doc_forge.app.deps import reset_runtime_caches


def test_api_command_auto_applies_migrations_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []

    reset_runtime_caches()
    monkeypatch.setenv("DOC_FORGE_AUTO_MIGRATE", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///tmp/runtime.db")
    monkeypatch.setattr(sys, "argv", ["python", "api"])
    monkeypatch.setattr(
        "doc_forge.runtime.apply_migrations_with_lock",
        lambda database_url=None: calls.append(("migrate", database_url or "")),
    )
    monkeypatch.setattr(
        "doc_forge.runtime.uvicorn.run",
        lambda *args, **kwargs: calls.append(("api", args[0])),
    )

    runtime.main()

    assert calls == [
        ("migrate", ""),
        ("api", "doc_forge.app.api:app"),
    ]


def test_worker_command_skips_auto_migrate_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    reset_runtime_caches()
    monkeypatch.delenv("DOC_FORGE_AUTO_MIGRATE", raising=False)
    monkeypatch.setattr(sys, "argv", ["python", "worker"])
    monkeypatch.setattr(
        "doc_forge.runtime.apply_migrations_with_lock",
        lambda database_url=None: calls.append("migrate"),
    )
    monkeypatch.setattr("doc_forge.runtime.worker_main", lambda: calls.append("worker"))

    runtime.main()

    assert calls == ["worker"]


def test_migrate_command_uses_locked_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    reset_runtime_caches()
    monkeypatch.setattr(sys, "argv", ["python", "migrate"])
    monkeypatch.setattr(
        "doc_forge.runtime.apply_migrations_with_lock",
        lambda database_url=None: calls.append(database_url or "env"),
    )

    runtime.main()

    assert calls == ["env"]
