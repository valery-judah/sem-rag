from __future__ import annotations

from fastapi.testclient import TestClient

from doc_forge.app.api import create_app
from doc_forge.app.deps import reset_runtime_caches
from doc_forge.persistence import apply_migrations


def _drain_jobs(client: TestClient, limit: int = 24) -> None:
    for _ in range(limit):
        payload = client.post("/internal/run-next-job").json()
        if payload["job_id"] is None:
            return
    raise AssertionError("worker did not drain queue within limit")


readiness_and_retrieval_smoke_are_document_scoped(tmp_path: pathlib.Path, monkeypatch) -> None:
    database_path = tmp_path / "multi-doc-ready.db"
    artifact_root = tmp_path / "artifacts"
    db_url = f"sqlite+pysqlite:///{database_path}"
    apply_migrations(db_url)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("DOC_FORGE_ARTIFACT_ROOT", str(artifact_root))
    reset_runtime_caches()

    with TestClient(create_app()) as client:
        alpha = client.post(
            "/documents",
            data={"workspace_id": "ws-1", "title": "Alpha Notes"},
            files={
                "file": (
                    "alpha.md",
                    b"# Alpha\n\nalpha content stays with document alpha.\n",
                    "text/markdown",
                )
            },
        )
        beta = client.post(
            "/documents",
            data={"workspace_id": "ws-1", "title": "Beta Notes"},
            files={
                "file": (
                    "beta.md",
                    b"# Beta\n\nbeta content stays with document beta.\n",
                    "text/markdown",
                )
            },
        )
        alpha_doc_id = alpha.json()["doc_id"]
        beta_doc_id = beta.json()["doc_id"]

        _drain_jobs(client)

        alpha_status = client.get(f"/documents/{alpha_doc_id}/status").json()
        beta_status = client.get(f"/documents/{beta_doc_id}/status").json()
        assert alpha_status["ingest_status"] == "ready"
        assert beta_status["ingest_status"] == "ready"

        alpha_query = client.post(
            "/retrieval/query",
            json={"doc_id": alpha_doc_id, "query": "beta content", "k": 1},
        )
        beta_query = client.post(
            "/retrieval/query",
            json={"doc_id": beta_doc_id, "query": "alpha content", "k": 1},
        )

        assert alpha_query.status_code == 200
        assert beta_query.status_code == 200
        assert alpha_query.json()["hits"][0]["doc_id"] == alpha_doc_id
        assert beta_query.json()["hits"][0]["doc_id"] == beta_doc_id

    reset_runtime_caches()
