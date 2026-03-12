from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e


def test_pdf_fixture_reaches_ready_and_preserves_page_provenance(e2e_stack) -> None:
    pdf_path = Path(__file__).with_name("fixtures").joinpath("ready_text_pdf.pdf")
    e2e_stack.log("uploading pdf fixture", path=str(pdf_path))

    with e2e_stack.client() as client, pdf_path.open("rb") as handle:
        upload = client.post(
            "/documents",
            data={"workspace_id": "ws-e2e", "title": "Lifecycle PDF"},
            files={"file": (pdf_path.name, handle, "application/pdf")},
        )
        upload.raise_for_status()
        doc_id = upload.json()["doc_id"]
        e2e_stack.log("uploaded pdf fixture", doc_id=doc_id)

        status = e2e_stack.wait_for_document(client, doc_id=doc_id)
        assert status["ingest_status"] == "ready"

        artifacts = client.get(f"/documents/{doc_id}/artifacts")
        artifacts.raise_for_status()
        payload = artifacts.json()
        assert e2e_stack.host_artifact_path(payload["raw_path"]).exists()
        assert e2e_stack.host_artifact_path(payload["extracted_path"]).exists()
        assert e2e_stack.host_artifact_path(payload["normalized_path"]).exists()

        query = client.post(
            "/retrieval/query",
            json={"doc_id": doc_id, "query": "tokenization", "k": 1},
        )
        query.raise_for_status()
        e2e_stack.log(
            "pdf retrieval query completed",
            doc_id=doc_id,
            top_hit=query.json()["hits"][0]["doc_id"],
        )
        assert query.json()["hits"][0]["doc_id"] == doc_id

        document = e2e_stack.document_row(doc_id=doc_id)
        assert document is not None
        assert str(document["ingest_status"]).upper() == "READY"
        assert document["source_type"] == "pdf"

        snapshot = e2e_stack.vector_snapshot(doc_id=doc_id)
        assert snapshot["chunk_count"] > 0
        assert snapshot["embedding_count"] > 0
        assert snapshot["index_entry_count"] > 0
        assert snapshot["embedding_count"] == snapshot["chunk_count"]
        assert snapshot["index_entry_count"] == snapshot["chunk_count"]

        chunk_rows = e2e_stack.chunk_rows(doc_id=doc_id)
        assert chunk_rows
        assert any(
            row["page_start"] is not None or row["page_end"] is not None for row in chunk_rows
        )


def test_malformed_pdf_reaches_failed_without_published_retrieval_artifacts(e2e_stack) -> None:
    malformed_path = Path(__file__).with_name("fixtures").joinpath("malformed.pdf")
    e2e_stack.log("uploading malformed pdf fixture", path=str(malformed_path))

    with e2e_stack.client() as client, malformed_path.open("rb") as handle:
        upload = client.post(
            "/documents",
            data={"workspace_id": "ws-e2e", "title": "Malformed PDF"},
            files={"file": (malformed_path.name, handle, "application/pdf")},
        )
        upload.raise_for_status()
        doc_id = upload.json()["doc_id"]
        e2e_stack.log("uploaded malformed pdf fixture", doc_id=doc_id)

        status = e2e_stack.wait_for_document(client, doc_id=doc_id)
        assert status["ingest_status"] == "failed"
        assert status["failure_code"]
        assert status["failure_detail"]

        document = e2e_stack.document_row(doc_id=doc_id)
        assert document is not None
        assert str(document["ingest_status"]).upper() == "FAILED"
        assert document["failure_code"]
        assert document["failure_detail"]

        events = e2e_stack.lifecycle_events(doc_id=doc_id)
        assert "FAILED" in [str(event["to_status"]).upper() for event in events]

        snapshot = e2e_stack.vector_snapshot(doc_id=doc_id)
        assert snapshot["chunk_count"] == 0
        assert snapshot["embedding_count"] == 0
        assert snapshot["index_entry_count"] == 0
        assert snapshot["sample_embedding"] is None
