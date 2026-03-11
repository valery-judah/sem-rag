from __future__ import annotations

import hashlib

import pytest
from fastapi.testclient import TestClient

from parity.app.api import create_app
from parity.app.deps import reset_runtime_caches
from parity.persistence import apply_migrations


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    database_path = tmp_path / "documents-api.db"
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


def test_pdf_upload_registers_successfully(client: TestClient) -> None:
    payload = b"%PDF-1.7\n1 0 obj\n"
    response = client.post(
        "/documents",
        data={"workspace_id": "ws-1", "title": "System Design"},
        files={"file": ("system-design.pdf", payload, "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json() == {
        "doc_id": response.json()["doc_id"],
        "ingest_status": "registered",
        "source_type": "pdf",
        "filename": "system-design.pdf",
        "title": "System Design",
        "uploaded_at": response.json()["uploaded_at"],
        "checksum": f"sha256:{hashlib.sha256(payload).hexdigest()}",
    }


def test_markdown_upload_registers_successfully(client: TestClient) -> None:
    response = client.post(
        "/documents",
        data={"workspace_id": "ws-1", "title": "Ops Notes"},
        files={"file": ("ops-notes.md", b"# Ops\n\nThis is UTF-8 markdown.\n", "text/markdown")},
    )

    body = response.json()

    assert response.status_code == 201
    assert body["ingest_status"] == "registered"
    assert body["source_type"] == "markdown"
    assert body["filename"] == "ops-notes.md"
    assert body["title"] == "Ops Notes"
    assert body["checksum"].startswith("sha256:")


def test_unsupported_extension_is_rejected_explicitly(client: TestClient) -> None:
    response = client.post(
        "/documents",
        data={"workspace_id": "ws-1"},
        files={"file": ("notes.txt", b"plain text", "text/plain")},
    )

    assert response.status_code == 415
    assert "text-based PDF and Markdown" in response.json()["detail"]


def test_fake_pdf_content_with_pdf_extension_is_rejected_explicitly(
    client: TestClient,
) -> None:
    response = client.post(
        "/documents",
        data={"workspace_id": "ws-1"},
        files={"file": ("notes.pdf", b"not really a pdf", "application/pdf")},
    )

    assert response.status_code == 415
    assert "PDF header bytes" in response.json()["detail"]


def test_omitted_title_falls_back_to_filename_stem(client: TestClient) -> None:
    response = client.post(
        "/documents",
        data={"workspace_id": "ws-1"},
        files={"file": ("team-playbook.markdown", b"# Team Playbook\n", "text/markdown")},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "team-playbook"
