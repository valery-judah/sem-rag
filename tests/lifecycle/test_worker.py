from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from parity.app.api import create_app
from parity.app.deps import reset_runtime_caches
from parity.persistence import apply_migrations


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    database_path = tmp_path / "worker.db"
    artifact_root = tmp_path / "artifacts"
    db_url = f"sqlite+pysqlite:///{database_path}"
    apply_migrations(db_url)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("PARITY_ARTIFACT_ROOT", str(artifact_root))
    reset_runtime_caches()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_runtime_caches()


def test_worker_records_failed_extract_stage(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "parity.extractors.pdf.PdfReader",
        lambda _: (_ for _ in ()).throw(ValueError("broken pdf")),
    )
    response = client.post(
        "/documents",
        data={"workspace_id": "ws-1"},
        files={"file": ("broken.pdf", b"%PDF-1.7\nbroken", "application/pdf")},
    )
    doc_id = response.json()["doc_id"]

    run = client.post("/internal/run-next-job")

    assert run.status_code == 200
    status_response = client.get(f"/documents/{doc_id}/status")
    body = status_response.json()
    assert body["ingest_status"] == "failed"
    assert body["failure_code"] == "extract_failed"
    assert "pdf extraction failed to parse the source file" in body["failure_detail"]
    artifacts_response = client.get(f"/documents/{doc_id}/artifacts")
    artifacts = artifacts_response.json()
    assert artifacts["raw_path"].endswith("source.pdf")
    assert artifacts["extracted_path"] is None
    assert artifacts["normalized_path"] is None
