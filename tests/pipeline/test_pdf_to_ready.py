from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from doc_forge.app.api import create_app
from doc_forge.app.deps import reset_runtime_caches
from doc_forge.persistence import apply_migrations


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


def test_pdf_document_reaches_ready(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "pdf-ready.db"
    artifact_root = tmp_path / "artifacts"
    db_url = f"sqlite+pysqlite:///{database_path}"
    apply_migrations(db_url)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("DOC_FORGE_ARTIFACT_ROOT", str(artifact_root))
    monkeypatch.setattr(
        "doc_forge.extractors.pdf.PdfReader",
        lambda _: _FakePdfReader(
            [
                "1 Introduction\n\nConsensus keeps nodes aligned.",
                "2 Retries\n\nRetries clear derived artifacts.",
            ]
        ),
    )
    reset_runtime_caches()

    with TestClient(create_app()) as client:
        upload = client.post(
            "/documents",
            data={"workspace_id": "ws-1", "title": "Ops Guide"},
            files={"file": ("ops.pdf", b"%PDF-1.7\nfake", "application/pdf")},
        )
        doc_id = upload.json()["doc_id"]
        _drain_jobs(client)

        status_after = client.get(f"/documents/{doc_id}/status").json()
        assert status_after["ingest_status"] == "ready"
        query = client.post(
            "/retrieval/query",
            json={"doc_id": doc_id, "query": "How do retries work?", "k": 1},
        )
        assert query.status_code == 200
        assert query.json()["hits"][0]["doc_id"] == doc_id

    reset_runtime_caches()
