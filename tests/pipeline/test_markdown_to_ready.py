from __future__ import annotations

from fastapi.testclient import TestClient

from doc_forge.app.api import create_app
from doc_forge.app.deps import reset_runtime_caches
from doc_forge.persistence import apply_migrations


def _drain_jobs(client: TestClient, limit: int = 12) -> list[dict[str, str | None]]:
    runs: list[dict[str, str | None]] = []
    for _ in range(limit):
        response = client.post("/internal/run-next-job")
        payload = response.json()
        runs.append(payload)
        if payload["job_id"] is None:
            break
    return runs


markdown_document_reaches_ready(tmp_path: pathlib.Path, monkeypatch) -> None:
    database_path = tmp_path / "markdown-ready.db"
    artifact_root = tmp_path / "artifacts"
    db_url = f"sqlite+pysqlite:///{database_path}"
    apply_migrations(db_url)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("DOC_FORGE_ARTIFACT_ROOT", str(artifact_root))
    reset_runtime_caches()

    with TestClient(create_app()) as client:
        upload = client.post(
            "/documents",
            data={"workspace_id": "ws-1", "title": "Distributed Notes"},
            files={
                "file": (
                    "notes.md",
                    (
                        b"# Overview\n\nConsensus keeps replicas aligned.\n\n"
                        b"## Retries\n\nRetries clear derived artifacts.\n"
                    ),
                    "text/markdown",
                )
            },
        )
        doc_id = upload.json()["doc_id"]

        status_before = client.get(f"/documents/{doc_id}/status").json()
        assert status_before["ingest_status"] == "registered"
        assert status_before["active_job_stage"] == "EXTRACT"

        runs = _drain_jobs(client)
        assert [run["status"] for run in runs[:-1]] == ["succeeded"] * 6
        assert runs[-1]["job_id"] is None

        status_after = client.get(f"/documents/{doc_id}/status").json()
        assert status_after["ingest_status"] == "ready"
        artifacts = client.get(f"/documents/{doc_id}/artifacts").json()
        assert artifacts["raw_path"].endswith("source.md")
        assert artifacts["extracted_path"].endswith("extracted.json")
        assert artifacts["normalized_path"].endswith("normalized.json")
        query = client.post(
            "/retrieval/query",
            json={"doc_id": doc_id, "query": "What keeps replicas aligned?", "k": 1},
        )
        assert query.status_code == 200
        assert query.json()["hits"][0]["doc_id"] == doc_id

    reset_runtime_caches()
