from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

REAL_DOC_CASES = (
    (
        Path("docs/workstreams/WS-004-document-lifecycle/21-design-exploration.md"),
        "Design Exploration",
        "Postgres-backed job queue with worker polling",
    ),
    (
        Path("docs/workstreams/WS-004-document-lifecycle/22-staged.md"),
        "Staged Delivery",
        "end-to-end pipeline tests from upload to READY",
    ),
    (
        Path("docs/evergreen/mvp.md"),
        "MVP Scope",
        "Markdown-first beta",
    ),
)

MULTI_DOC_CASES = (
    (
        "Alpha Notes",
        "alpha.md",
        b"# Alpha\n\nalpha content stays with document alpha.\n",
        "beta content",
    ),
    (
        "Beta Notes",
        "beta.md",
        b"# Beta\n\nbeta content stays with document beta.\n",
        "alpha content",
    ),
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _upload_document(
    stack,
    *,
    path: Path,
    title: str,
) -> tuple[str, dict[str, object]]:
    absolute_path = _repo_root() / path
    with stack.client() as client, absolute_path.open("rb") as handle:
        upload = client.post(
            "/documents",
            data={"workspace_id": "ws-docs", "title": title},
            files={"file": (absolute_path.name, handle, "text/markdown")},
        )
        upload.raise_for_status()
        doc_id = upload.json()["doc_id"]
        status = stack.wait_for_document(client, doc_id=doc_id, timeout_seconds=90.0)
        assert status["ingest_status"] == "ready"
        artifacts = client.get(f"/documents/{doc_id}/artifacts")
        artifacts.raise_for_status()
        return doc_id, artifacts.json()


def _upload_markdown_bytes(
    stack,
    *,
    filename: str,
    title: str,
    content: bytes,
) -> tuple[str, dict[str, object]]:
    with stack.client() as client:
        upload = client.post(
            "/documents",
            data={"workspace_id": "ws-docs", "title": title},
            files={"file": (filename, content, "text/markdown")},
        )
        upload.raise_for_status()
        doc_id = upload.json()["doc_id"]
        status = stack.wait_for_document(client, doc_id=doc_id, timeout_seconds=90.0)
        assert status["ingest_status"] == "ready"
        artifacts = client.get(f"/documents/{doc_id}/artifacts")
        artifacts.raise_for_status()
        return doc_id, artifacts.json()


def _assert_vector_snapshot(snapshot: dict[str, object]) -> None:
    assert snapshot["chunk_count"] > 0
    assert snapshot["embedding_count"] > 0
    assert snapshot["index_entry_count"] > 0
    assert snapshot["embedding_count"] == snapshot["chunk_count"]
    assert snapshot["index_entry_count"] == snapshot["chunk_count"]


def test_design_exploration_reaches_ready_and_is_queryable(e2e_stack) -> None:
    path, title, query_text = REAL_DOC_CASES[0]
    doc_id, artifacts = _upload_document(e2e_stack, path=path, title=title)
    snapshot = e2e_stack.vector_snapshot(doc_id=doc_id)

    with e2e_stack.client() as client:
        query = client.post(
            "/retrieval/query",
            json={"doc_id": doc_id, "query": query_text, "k": 1},
        )
        query.raise_for_status()
        assert query.json()["hits"][0]["doc_id"] == doc_id

    _assert_vector_snapshot(snapshot)
    sample_embedding = snapshot["sample_embedding"]
    assert sample_embedding is not None
    assert sample_embedding["embedding_model"]
    assert isinstance(sample_embedding["embedding_vector_json"], list)
    assert sample_embedding["embedding_vector_json"]
    assert e2e_stack.host_artifact_path(artifacts["raw_path"]).exists()
    assert e2e_stack.host_artifact_path(artifacts["extracted_path"]).exists()
    assert e2e_stack.host_artifact_path(artifacts["normalized_path"]).exists()


def test_real_markdown_bundle_reaches_ready_with_artifacts_and_doc_scoped_retrieval(
    e2e_stack,
) -> None:
    uploaded: list[tuple[str, str, dict[str, object]]] = []
    for path, title, query_text in REAL_DOC_CASES:
        doc_id, artifacts = _upload_document(e2e_stack, path=path, title=title)
        uploaded.append((doc_id, query_text, artifacts))

    with e2e_stack.client() as client:
        for doc_id, query_text, artifacts in uploaded:
            snapshot = e2e_stack.vector_snapshot(doc_id=doc_id)
            query = client.post(
                "/retrieval/query",
                json={"doc_id": doc_id, "query": query_text, "k": 1},
            )
            query.raise_for_status()
            assert query.json()["hits"][0]["doc_id"] == doc_id
            _assert_vector_snapshot(snapshot)
            assert e2e_stack.host_artifact_path(artifacts["raw_path"]).exists()
            assert e2e_stack.host_artifact_path(artifacts["extracted_path"]).exists()
            assert e2e_stack.host_artifact_path(artifacts["normalized_path"]).exists()


def test_multi_document_queries_remain_doc_scoped(e2e_stack) -> None:
    uploaded: list[tuple[str, str, dict[str, object]]] = []
    for title, filename, content, cross_query in MULTI_DOC_CASES:
        doc_id, artifacts = _upload_markdown_bytes(
            e2e_stack,
            filename=filename,
            title=title,
            content=content,
        )
        uploaded.append((doc_id, cross_query, artifacts))

    with e2e_stack.client() as client:
        for doc_id, cross_query, artifacts in uploaded:
            snapshot = e2e_stack.vector_snapshot(doc_id=doc_id)
            query = client.post(
                "/retrieval/query",
                json={"doc_id": doc_id, "query": cross_query, "k": 1},
            )
            query.raise_for_status()
            assert query.json()["hits"][0]["doc_id"] == doc_id
            _assert_vector_snapshot(snapshot)
            assert e2e_stack.host_artifact_path(artifacts["normalized_path"]).exists()


def test_ready_chunks_preserve_heading_path_and_coarse_provenance(e2e_stack) -> None:
    path, title, _ = REAL_DOC_CASES[0]
    doc_id, _ = _upload_document(e2e_stack, path=path, title=title)

    chunk_rows = e2e_stack.chunk_rows(doc_id=doc_id)

    assert chunk_rows
    assert any(row["heading_path_json"] for row in chunk_rows)
    assert all(
        row["section_id"] is not None
        or row["page_start"] is not None
        or row["source_start_offset"] is not None
        for row in chunk_rows
    )
