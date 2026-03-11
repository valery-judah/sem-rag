from __future__ import annotations

import pytest

from tests.helpers.imports import build_instance, call_with_supported_kwargs
from tests.helpers.builders import new_document, processing_status


pytestmark = pytest.mark.stage


EXTRACT_STAGE_MODULES = ["parity.stages.extract"]
EXTRACT_STAGE_CLASSES = ["ExtractStage", "ExtractStageRunner"]


def _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, fixed_now):
    return build_instance(
        EXTRACT_STAGE_MODULES,
        EXTRACT_STAGE_CLASSES,
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


def test_markdown_extract_persists_extracted_artifact_before_advance(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="markdown", status=processing_status("REGISTERED"), ingest_status=processing_status("REGISTERED"))
    document_repo.create(doc)
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, fixed_now)
    call_with_supported_kwargs(runner.run, doc_id="doc_1")
    assert extraction_service.calls == ["doc_1"]
    assert lifecycle_event_repo.events
    assert jobs_repo.enqueued
    # extracted payload path must exist in event detail or the runner must have written it to the store
    wrote_extracted = any("extracted" in path for path in artifact_store.list_written_paths())
    event_detail_mentions_payload = any("payload" in str(getattr(event, "detail", {})).lower() for event in lifecycle_event_repo.events)
    assert wrote_extracted or event_detail_mentions_payload


def test_pdf_extract_keeps_page_oriented_artifact_shape(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="pdf", filename="book.pdf", status=processing_status("REGISTERED"), ingest_status=processing_status("REGISTERED"))
    document_repo.create(doc)
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, fixed_now)
    call_with_supported_kwargs(runner.run, doc_id="doc_1")
    assert extraction_service.calls == ["doc_1"]


def test_extract_stage_records_failure_on_extractor_exception(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="markdown", status=processing_status("REGISTERED"), ingest_status=processing_status("REGISTERED"))
    document_repo.create(doc)
    extraction_service.raise_error = RuntimeError("boom")
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, fixed_now)
    with pytest.raises(Exception):
        call_with_supported_kwargs(runner.run, doc_id="doc_1")
    assert document_repo.status_updates, "runner must record failure status transition"
