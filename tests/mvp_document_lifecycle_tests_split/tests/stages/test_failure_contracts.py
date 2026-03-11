from __future__ import annotations

import pytest

from tests.helpers.builders import new_document, processing_status
from tests.helpers.imports import build_instance, call_with_supported_kwargs


pytestmark = pytest.mark.stage


def test_extract_failure_does_not_make_document_ready(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, fixed_now, readiness_service):
    extraction_service.raise_error = RuntimeError("extract failed")
    runner = build_instance(
        ["parity.stages.extract"],
        ["ExtractStage", "ExtractStageRunner"],
        document_repository=document_repo,
        documents=document_repo,
        lifecycle_event_repository=lifecycle_event_repo,
        lifecycle_events=lifecycle_event_repo,
        jobs=jobs_repo,
        jobs_repository=jobs_repo,
        artifact_store=artifact_store,
        extraction_service=extraction_service,
        extractor=extraction_service,
        clock=lambda: fixed_now,
        now=lambda: fixed_now,
    )
    doc = new_document(doc_id="doc_fail", source_type="pdf", filename="bad.pdf", status=processing_status("REGISTERED"), ingest_status=processing_status("REGISTERED"))
    document_repo.create(doc)
    with pytest.raises(Exception):
        call_with_supported_kwargs(runner.run, doc_id="doc_fail")
    assert readiness_service.evaluate(doc_id="doc_fail") is False


def test_index_failure_does_not_leave_stale_publication_entries(document_repo, lifecycle_event_repo, jobs_repo, index_publication_service, chunk_repo, index_entry_repo, vector_index, chunk_factory, fixed_now):
    index_publication_service.raise_error = RuntimeError("publish failed")
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
    doc = new_document(doc_id="doc_fail", source_type="markdown", status=processing_status("CHUNKED"), ingest_status=processing_status("CHUNKED"))
    document_repo.create(doc)
    chunk_repo.replace_for_document("doc_fail", [chunk_factory(chunk_id="chk_1", doc_id="doc_fail", section_id="sec_1")])
    with pytest.raises(Exception):
        call_with_supported_kwargs(runner.run, doc_id="doc_fail")
    assert index_entry_repo.list_for_document("doc_fail") == []
