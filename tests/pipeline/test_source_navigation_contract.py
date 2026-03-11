from __future__ import annotations

import sqlalchemy as sa
from fastapi.testclient import TestClient

from parity.app.api import create_app
from parity.app.deps import reset_runtime_caches
from parity.persistence import SqlChunkRepository, apply_migrations


def _drain_jobs(client: TestClient, limit: int = 12) -> None:
    for _ in range(limit):
        payload = client.post("/internal/run-next-job").json()
        if payload["job_id"] is None:
            return
    raise AssertionError("worker did not drain queue within limit")


def test_ready_chunks_are_traceable_to_document_and_coarse_location(
    tmp_path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "source-navigation.db"
    artifact_root = tmp_path / "artifacts"
    db_url = f"sqlite+pysqlite:///{database_path}"
    apply_migrations(db_url)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("PARITY_ARTIFACT_ROOT", str(artifact_root))
    reset_runtime_caches()

    with TestClient(create_app()) as client:
        upload = client.post(
            "/documents",
            data={"workspace_id": "ws-1", "title": "Traceability Notes"},
            files={
                "file": (
                    "traceability.md",
                    b"# Overview\n\nChunks retain enough provenance for inspection.\n",
                    "text/markdown",
                )
            },
        )
        doc_id = upload.json()["doc_id"]
        _drain_jobs(client)

        engine = sa.create_engine(db_url)
        try:
            chunk = SqlChunkRepository(engine).list_for_document(doc_id)[0]
        finally:
            engine.dispose()

        assert chunk.doc_id == doc_id
        assert chunk.heading_path
        assert (
            chunk.section_id is not None
            or chunk.page_start is not None
            or chunk.source_start_offset is not None
        )

    reset_runtime_caches()
