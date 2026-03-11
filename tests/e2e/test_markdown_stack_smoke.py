from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

LEGAL_STATUS_PATH = (
    "REGISTERED",
    "EXTRACTING",
    "NORMALIZED",
    "CHUNKED",
    "INDEXED",
    "READY",
)


def _assert_status_subsequence(actual: list[str], expected: tuple[str, ...]) -> None:
    normalized_actual = [status.upper() for status in actual]
    cursor = 0
    for status in normalized_actual:
        if cursor < len(expected) and status == expected[cursor]:
            cursor += 1
    assert cursor == len(expected), f"expected subsequence {expected}, got {actual}"


def test_markdown_fixture_reaches_ready_and_persists_artifacts(e2e_stack) -> None:
    smoke_path = Path(__file__).with_name("fixtures").joinpath("smoke.md")

    with e2e_stack.client() as client, smoke_path.open("rb") as handle:
        upload = client.post(
            "/documents",
            data={"workspace_id": "ws-e2e", "title": "Lifecycle Smoke"},
            files={"file": (smoke_path.name, handle, "text/markdown")},
        )
        upload.raise_for_status()
        doc_id = upload.json()["doc_id"]

        status = e2e_stack.wait_for_document(client, doc_id=doc_id)
        assert status["ingest_status"] == "ready"
        events = e2e_stack.lifecycle_events(doc_id=doc_id)
        _assert_status_subsequence(
            [str(event["to_status"]) for event in events],
            LEGAL_STATUS_PATH,
        )

        document = e2e_stack.document_row(doc_id=doc_id)
        assert document is not None
        assert str(document["ingest_status"]).upper() == "READY"
        assert document["raw_storage_path"]

        snapshot = e2e_stack.vector_snapshot(doc_id=doc_id)
        assert snapshot["chunk_count"] > 0
        assert snapshot["embedding_count"] > 0
        assert snapshot["index_entry_count"] > 0
        assert snapshot["embedding_count"] == snapshot["chunk_count"]
        assert snapshot["index_entry_count"] == snapshot["chunk_count"]

        artifacts = client.get(f"/documents/{doc_id}/artifacts")
        artifacts.raise_for_status()
        payload = artifacts.json()
        assert e2e_stack.host_artifact_path(payload["raw_path"]).exists()
        assert e2e_stack.host_artifact_path(payload["extracted_path"]).exists()
        normalized_path = e2e_stack.host_artifact_path(payload["normalized_path"])
        assert normalized_path.exists()

        query = client.post(
            "/retrieval/query",
            json={"doc_id": doc_id, "query": "retrievable and inspectable", "k": 1},
        )
        query.raise_for_status()
        assert query.json()["hits"][0]["doc_id"] == doc_id
