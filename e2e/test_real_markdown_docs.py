"""
End-to-end coverage for markdown ingestion and retrieval.

The scenarios in this module focus on the behaviors the suite actually proves:
1. Markdown documents reach the terminal "ready" state and become queryable.
2. Ready documents publish raw, extracted, and normalized artifacts on disk.
3. Ready documents preserve strict 1:1:1 chunk, embedding, and index-entry mapping.
4. Doc-scoped retrieval stays isolated for sequential and concurrent uploads.
5. Duplicate uploads resolve safely without corrupting the original document state.
6. Early upload validation rejects invalid markdown before async processing begins.
7. Retrieval ordering returns the semantically relevant chunk ahead of distractors.
8. Chunk provenance survives normalization and chunking for real markdown documents.
"""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest

from e2e.conftest import RunningStack
from e2e.support import E2EReadyDocument, SystemDriver

pytestmark = pytest.mark.e2e


@dataclass(frozen=True)
class RealDocCase:
    path: Path
    title: str
    query_text: str


@dataclass(frozen=True)
class MultiDocCase:
    title: str
    filename: str
    content: bytes
    own_query: str
    cross_query: str


@dataclass(frozen=True)
class ConcurrentDocCase:
    filename: str
    title: str
    marker: str
    content: bytes


REAL_DOC_CASES = (
    RealDocCase(
        path=Path("docs/workstreams/WS-004-document-lifecycle/21-design-exploration.md"),
        title="Design Exploration",
        query_text="Postgres-backed job queue with worker polling",
    ),
    RealDocCase(
        path=Path("docs/workstreams/WS-004-document-lifecycle/22-staged.md"),
        title="Staged Delivery",
        query_text="end-to-end pipeline tests from upload to READY",
    ),
    RealDocCase(
        path=Path("docs/evergreen/mvp.md"),
        title="MVP Scope",
        query_text="Markdown-first beta",
    ),
)

MULTI_DOC_CASES = (
    MultiDocCase(
        title="Alpha Notes",
        filename="alpha.md",
        content=(
            b"# Alpha\n\n"
            b"alpha ownership marker stays with document alpha and never appears in beta.\n"
        ),
        own_query="alpha ownership marker",
        cross_query="beta ownership marker",
    ),
    MultiDocCase(
        title="Beta Notes",
        filename="beta.md",
        content=(
            b"# Beta\n\n"
            b"beta ownership marker stays with document beta and never appears in alpha.\n"
        ),
        own_query="beta ownership marker",
        cross_query="alpha ownership marker",
    ),
)


def _single_chunk_row(e2e_stack: RunningStack, *, doc_id: str) -> dict[str, object]:
    chunk_rows = e2e_stack.chunk_rows(doc_id=doc_id)
    assert len(chunk_rows) == 1
    return chunk_rows[0]


def _chunk_text_by_id(e2e_stack: RunningStack, *, doc_id: str) -> dict[str, str]:
    return {str(row["chunk_id"]): str(row["text"]) for row in e2e_stack.chunk_rows(doc_id=doc_id)}


def _build_concurrent_cases(count: int = 5) -> tuple[ConcurrentDocCase, ...]:
    cases: list[ConcurrentDocCase] = []
    for index in range(count):
        marker = f"concurrency-marker-{index}"
        cases.append(
            ConcurrentDocCase(
                filename=f"concurrent-{index}.md",
                title=f"Concurrent Markdown {index}",
                marker=marker,
                content=(
                    f"# Concurrent {index}\n\n"
                    f"{marker} belongs only to document {index}. "
                    f"{marker} should never leak into any other document.\n"
                ).encode(),
            )
        )
    return tuple(cases)


@pytest.mark.parametrize("case", REAL_DOC_CASES, ids=lambda c: c.title)
def test_given_single_markdown_when_uploaded_then_ready_and_queryable(
    e2e_stack: RunningStack,
    case: RealDocCase,
) -> None:
    driver = SystemDriver(e2e_stack)

    uploaded = driver.ingest_document(path=case.path, title=case.title)

    uploaded.assert_strict_vector_mapping(e2e_stack)
    uploaded.assert_artifacts_exist(e2e_stack)

    result = driver.query(doc_id=uploaded.doc_id, text=case.query_text, k=1)

    assert result.top_hit is not None
    assert result.top_hit.doc_id == uploaded.doc_id


def test_given_ready_document_when_deleted_then_artifacts_and_vectors_are_removed(
    e2e_stack: RunningStack,
) -> None:
    driver = SystemDriver(e2e_stack)
    case = REAL_DOC_CASES[0]

    uploaded = driver.ingest_document(path=case.path, title=case.title)
    uploaded.assert_strict_vector_mapping(e2e_stack)
    uploaded.assert_artifacts_exist(e2e_stack)

    driver.delete_document(doc_id=uploaded.doc_id)

    uploaded.assert_artifacts_deleted(e2e_stack)
    uploaded.assert_vectors_deleted(e2e_stack)


def test_given_multiple_docs_when_query_scoped_then_returns_isolated_results(
    e2e_stack: RunningStack,
) -> None:
    driver = SystemDriver(e2e_stack)
    uploaded_items: list[tuple[MultiDocCase, E2EReadyDocument]] = []

    for case in MULTI_DOC_CASES:
        uploaded = driver.ingest_markdown_bytes(
            filename=case.filename,
            title=case.title,
            content=case.content,
        )
        uploaded_items.append((case, uploaded))

    for case, document in uploaded_items:
        document.assert_strict_vector_mapping(e2e_stack)
        document.assert_artifacts_exist(e2e_stack)

        chunk_row = _single_chunk_row(e2e_stack, doc_id=document.doc_id)
        chunk_text = str(chunk_row["text"])

        assert case.own_query in chunk_text
        assert case.cross_query not in chunk_text

        own_result = driver.query(doc_id=document.doc_id, text=case.own_query, k=1)
        assert own_result.top_hit is not None
        assert own_result.top_hit.doc_id == document.doc_id
        assert own_result.top_hit.chunk_id == chunk_row["chunk_id"]

        cross_result = driver.query(doc_id=document.doc_id, text=case.cross_query, k=1)
        assert cross_result.top_hit is not None
        assert cross_result.top_hit.doc_id == document.doc_id
        assert cross_result.top_hit.chunk_id == chunk_row["chunk_id"]


def test_given_duplicate_uploads_when_ingested_then_preserves_original_consistency(
    e2e_stack: RunningStack,
) -> None:
    driver = SystemDriver(e2e_stack)
    case = MULTI_DOC_CASES[0]

    first_receipt = driver.submit_markdown_bytes(
        filename=case.filename,
        title=case.title,
        content=case.content,
    )
    original = driver.wait_for_ready_document(first_receipt.doc_id)
    original.assert_strict_vector_mapping(e2e_stack)
    original.assert_artifacts_exist(e2e_stack)

    second_document: E2EReadyDocument | None = None
    try:
        second_receipt = driver.submit_markdown_bytes(
            filename=case.filename,
            title=case.title,
            content=case.content,
        )
    except httpx.HTTPStatusError as exc:
        assert exc.response.status_code == 409
    else:
        second_document = driver.wait_for_ready_document(second_receipt.doc_id)
        second_document.assert_strict_vector_mapping(e2e_stack)
        second_document.assert_artifacts_exist(e2e_stack)
        assert second_document.doc_id != original.doc_id

    original_query = driver.query(doc_id=original.doc_id, text=case.own_query, k=1)
    assert original_query.top_hit is not None
    assert original_query.top_hit.doc_id == original.doc_id

    if second_document is not None:
        duplicate_query = driver.query(doc_id=second_document.doc_id, text=case.own_query, k=1)
        assert duplicate_query.top_hit is not None
        assert duplicate_query.top_hit.doc_id == second_document.doc_id


def test_given_invalid_utf8_markdown_when_uploaded_then_rejected_before_registration(
    e2e_stack: RunningStack,
) -> None:
    driver = SystemDriver(e2e_stack)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        driver.submit_markdown_bytes(
            filename="invalid-markdown.md",
            title="Invalid Markdown",
            content=b"\xff\xfe\x00broken-markdown",
        )

    assert exc_info.value.response.status_code == 415
    assert "valid UTF-8 text" in exc_info.value.response.json()["detail"]


def test_given_concurrent_uploads_when_processed_then_chunks_and_queries_stay_isolated(
    e2e_stack: RunningStack,
) -> None:
    cases = _build_concurrent_cases()
    uploaded_by_marker: dict[str, E2EReadyDocument] = {}

    def worker(case: ConcurrentDocCase) -> tuple[str, E2EReadyDocument]:
        driver = SystemDriver(e2e_stack)
        document = driver.ingest_markdown_bytes(
            filename=case.filename,
            title=case.title,
            content=case.content,
        )
        return case.marker, document

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        future_map = {executor.submit(worker, case): case for case in cases}
        for future in concurrent.futures.as_completed(future_map):
            marker, document = future.result()
            uploaded_by_marker[marker] = document

    assert len(uploaded_by_marker) == len(cases)

    driver = SystemDriver(e2e_stack)
    for index, case in enumerate(cases):
        document = uploaded_by_marker[case.marker]
        document.assert_strict_vector_mapping(e2e_stack)
        document.assert_artifacts_exist(e2e_stack)

        chunk_row = _single_chunk_row(e2e_stack, doc_id=document.doc_id)
        chunk_text = str(chunk_row["text"])
        assert case.marker in chunk_text

        for other_case in cases:
            if other_case.marker != case.marker:
                assert other_case.marker not in chunk_text

        own_result = driver.query(doc_id=document.doc_id, text=case.marker, k=1)
        assert own_result.top_hit is not None
        assert own_result.top_hit.doc_id == document.doc_id
        assert own_result.top_hit.chunk_id == chunk_row["chunk_id"]

        other_case = cases[(index + 1) % len(cases)]
        cross_result = driver.query(doc_id=document.doc_id, text=other_case.marker, k=1)
        assert cross_result.top_hit is not None
        assert cross_result.top_hit.doc_id == document.doc_id
        assert cross_result.top_hit.chunk_id == chunk_row["chunk_id"]


def test_given_semantic_query_when_executed_then_relevant_chunk_ranks_above_distractors(
    e2e_stack: RunningStack,
) -> None:
    driver = SystemDriver(e2e_stack)
    uploaded = driver.ingest_markdown_bytes(
        filename="topics.md",
        title="Topics",
        content=(
            b"```text\n"
            b"apple banana orange fruit tree orchard\n"
            b"```\n\n"
            b"```sql\n"
            b"postgresql database server transaction table index\n"
            b"```\n\n"
            b"```text\n"
            b"guitar piano drums music song melody\n"
            b"```\n"
        ),
    )

    result = driver.query(
        doc_id=uploaded.doc_id,
        text="postgresql transaction table index",
        k=3,
    )
    chunk_text_by_id = _chunk_text_by_id(e2e_stack, doc_id=uploaded.doc_id)
    ordered_texts = [chunk_text_by_id[hit.chunk_id] for hit in result.hits]

    assert len(result.hits) == 3
    assert len(chunk_text_by_id) == 3
    assert all(
        result.hits[index].score >= result.hits[index + 1].score
        for index in range(len(result.hits) - 1)
    )
    assert "postgresql database server transaction table index" in ordered_texts[0]
    assert any("apple banana orange fruit tree orchard" in text for text in ordered_texts[1:])
    assert any("guitar piano drums music song melody" in text for text in ordered_texts[1:])


@pytest.mark.parametrize("case", REAL_DOC_CASES, ids=lambda c: c.title)
def test_given_ready_document_when_chunked_then_preserves_provenance(
    e2e_stack: RunningStack,
    case: RealDocCase,
) -> None:
    driver = SystemDriver(e2e_stack)

    uploaded = driver.ingest_document(path=case.path, title=case.title)
    chunk_rows = e2e_stack.chunk_rows(doc_id=uploaded.doc_id)

    assert chunk_rows
    assert any(row["heading_path_json"] for row in chunk_rows)
    assert all(
        row["section_id"] is not None
        or row["page_start"] is not None
        or row["source_start_offset"] is not None
        for row in chunk_rows
    )
