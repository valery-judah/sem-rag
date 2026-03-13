from __future__ import annotations

from doc_forge.devtools import evalops_loader


class _FakeLoader:
    def __init__(self) -> None:
        self.created_schema = False
        self.scan_once_calls = 0
        self.scan_forever_calls: list[float] = []

    def create_schema(self) -> None:
        self.created_schema = True

    def scan_once(self):
        self.scan_once_calls += 1

        class _Stats:
            scanned_bundles = 2
            indexed_bundles = 2

        return _Stats()

    def scan_forever(self, *, interval_seconds: float) -> None:
        self.scan_forever_calls.append(interval_seconds)


def test_init_schema_command(monkeypatch) -> None:
    loader = _FakeLoader()
    monkeypatch.setattr(evalops_loader, "_build_loader", lambda *_: loader)

    exit_code = evalops_loader.main(["init-schema"])

    assert exit_code == 0
    assert loader.created_schema is True


def test_scan_once_command(monkeypatch, capsys) -> None:
    loader = _FakeLoader()
    monkeypatch.setattr(evalops_loader, "_build_loader", lambda *_: loader)

    exit_code = evalops_loader.main(["scan"])

    assert exit_code == 0
    assert loader.scan_once_calls == 1
    assert capsys.readouterr().out.strip() == "scanned_bundles=2 indexed_bundles=2"


def test_scan_loop_command(monkeypatch) -> None:
    loader = _FakeLoader()
    monkeypatch.setattr(evalops_loader, "_build_loader", lambda *_: loader)

    exit_code = evalops_loader.main(["scan", "--loop", "--interval-seconds", "3"])

    assert exit_code == 0
    assert loader.scan_forever_calls == [3.0]
