from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from parity.app.api import create_app
from parity.app.deps import reset_runtime_caches
from parity.persistence import apply_migrations


class _FakePdfPage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakePdfReader:
    def __init__(self, pages: list[str]) -> None:
        self.pages = [_FakePdfPage(text) for text in pages]


def _drain_jobs(client: TestClient, limit: int = 12) -> None:
    for _ in range(limit):
        payload = client.post("/internal/run-next-job").json()
        if payload["job_id"] is None:
            return
    raise AssertionError("worker did not drain queue within limit")


def test_retry_recovers_failed_extract_stage(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    database_path = tmp_path / "retry.db"
    artifact_root = tmp_path / "artifacts"
    db_url = f"sqlite+pysqlite:///{database_path}"
    apply_migrations(db_url)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("PARITY_ARTIFACT_ROOT", str(artifact_root))
    reset_runtime_caches()

    with TestClient(create_app()) as client:
        upload = client.post(
            "/documents",
            data={"workspace_id": "ws-1"},
            files={"file": ("retry.pdf", b"%PDF-1.7\nbroken", "application/pdf")},
        )
        doc_id = upload.json()["doc_id"]

        monkeypatch.setattr(
            "parity.extractors.pdf.PdfReader",
            lambda _: (_ for _ in ()).throw(ValueError("broken pdf")),
        )
        client.post("/internal/run-next-job")

        failed = client.get(f"/documents/{doc_id}/status").json()
        assert failed["ingest_status"] == "failed"
        assert failed["failure_code"] == "extract_failed"

        monkeypatch.setattr(
            "parity.extractors.pdf.PdfReader",
            lambda _: _FakePdfReader(
                [
                    "1 Introduction\n\nConsensus keeps nodes aligned.",
                    "2 Retries\n\nRetries clear derived artifacts.",
                ]
            ),
        )
        retry = client.post(f"/documents/{doc_id}/retry")
        assert retry.status_code == 202
        assert retry.json()["queued_stage"] == "EXTRACT"

        _drain_jobs(client)

        recovered = client.get(f"/documents/{doc_id}/status").json()
        assert recovered["ingest_status"] == "ready"

    reset_runtime_caches()
