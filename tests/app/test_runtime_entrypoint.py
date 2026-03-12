from __future__ import annotations

import sys

import pytest

from parity import runtime


def test_api_command_auto_applies_migrations_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []

    monkeypatch.setenv("PARITY_AUTO_MIGRATE", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///tmp/runtime.db")
    monkeypatch.setattr(sys, "argv", ["python", "api"])
    monkeypatch.setattr(
        "parity.runtime.apply_migrations_with_lock",
        lambda database_url=None: calls.append(("migrate", database_url or "")),
    )
    monkeypatch.setattr(
        "parity.runtime.uvicorn.run",
        lambda *args, **kwargs: calls.append(("api", args[0])),
    )

    runtime.main()

    assert calls == [
        ("migrate", ""),
        ("api", "parity.app.api:app"),
    ]


def test_worker_command_skips_auto_migrate_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    monkeypatch.delenv("PARITY_AUTO_MIGRATE", raising=False)
    monkeypatch.setattr(sys, "argv", ["python", "worker"])
    monkeypatch.setattr(
        "parity.runtime.apply_migrations_with_lock",
        lambda database_url=None: calls.append("migrate"),
    )
    monkeypatch.setattr("parity.runtime.worker_main", lambda: calls.append("worker"))

    runtime.main()

    assert calls == ["worker"]


def test_migrate_command_uses_locked_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(sys, "argv", ["python", "migrate"])
    monkeypatch.setattr(
        "parity.runtime.apply_migrations_with_lock",
        lambda database_url=None: calls.append(database_url or "env"),
    )

    runtime.main()

    assert calls == ["env"]
