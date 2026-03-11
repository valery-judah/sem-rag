from __future__ import annotations

import pytest

from tests.helpers.builders import new_chunk, new_document, new_index_entry, new_section, processing_status
from tests.helpers.fakes import FakeReadinessService
from tests.helpers.imports import build_instance, call_with_supported_kwargs


pytestmark = [pytest.mark.pipeline, pytest.mark.slow]


def test_retry_after_index_failure_can_reach_ready(
    document_repo,
    lifecycle_event_repo,
    jobs_repo,
    artifact_store,
    index_publication_service,
    section_repo,
    chunk_repo,
    index_entry_repo,
    vector_index,
    readiness_view,
    fixed_now,
):
    doc = new_document(doc_id="doc_retry", source_type="markdown", status=processing_status("CHUNKED"), ingest_status=processing_status("CHUNKED"))
    document_repo.create(doc)
    section_repo.replace_for_document("doc_retry", [new_section(section_id="sec_1", doc_id="doc_retry", heading_path=["Intro"], heading_text="Intro")])
    chunk_repo.replace_for_document("doc_retry", [new_chunk(chunk_id="chk_1", doc_id="doc_retry", section_id="sec_1", heading_path=["Intro"], text="retry path content", source_offset_start=0, source_offset_end=20)])

    # Simulate failed first attempt.
    index_publication_service.raise_error = RuntimeError("transient publish failure")
    runner = build_instance(
        ["parity.stages.index"],
        ["IndexStage", "IndexStageRunner"],
        document_repository=document_repo,
        documents=document_repo,
        lifecycle_event_repository=lifecycle_event_repo,
        lifecycle_events=lifecycle_event_repo,
        jobs=jobs_repo,
        jobs_repository=jobs_repo,
        index_publication_service=index_publication_service,
        publisher=index_publication_service,
        chunks=chunk_repo,
        chunk_repository=chunk_repo,
        index_entries=index_entry_repo,
        index_entry_repository=index_entry_repo,
        vector_index=vector_index,
        clock=lambda: fixed_now,
        now=lambda: fixed_now,
    )
    with pytest.raises(Exception):
        call_with_supported_kwargs(runner.run, doc_id="doc_retry")

    # Retry with healthy publisher.
    index_publication_service.raise_error = None
    call_with_supported_kwargs(runner.run, doc_id="doc_retry")
    readiness_view.normalized_docs.add("doc_retry")
    assert FakeReadinessService(readiness_view).evaluate(doc_id="doc_retry") is True
