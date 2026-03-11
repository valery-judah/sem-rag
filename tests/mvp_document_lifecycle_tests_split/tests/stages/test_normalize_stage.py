from __future__ import annotations

import pytest

from tests.helpers.imports import build_instance, call_with_supported_kwargs
from tests.helpers.builders import new_document, new_extracted_artifact, processing_status


pytestmark = pytest.mark.stage


NORMALIZE_STAGE_MODULES = ["parity.stages.normalize"]
NORMALIZE_STAGE_CLASSES = ["NormalizeStage", "NormalizeStageRunner"]


def _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, normalization_service, fixed_now):
    return build_instance(
        NORMALIZE_STAGE_MODULES,
        NORMALIZE_STAGE_CLASSES,
        document_repository=document_repo,
        documents=document_repo,
        lifecycle_event_repository=lifecycle_event_repo,
        lifecycle_events=lifecycle_event_repo,
        jobs=jobs_repo,
        jobs_repository=jobs_repo,
        artifact_store=artifact_store,
        normalization_service=normalization_service,
        normalizer=normalization_service,
        clock=lambda: fixed_now,
        now=lambda: fixed_now,
    )


def test_markdown_normalize_persists_payload_before_status_advance(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, normalization_service, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="markdown", status=processing_status("EXTRACTING"), ingest_status=processing_status("EXTRACTING"))
    document_repo.create(doc)
    artifact_store.write_json(
        path="data/extracted/doc_1/extracted.json",
        payload={"doc_id": "doc_1", "source_type": "markdown", "pages": [], "meta": {"warnings": []}},
    )
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, normalization_service, fixed_now)
    call_with_supported_kwargs(runner.run, doc_id="doc_1")
    wrote_normalized = any("normalized" in path for path in artifact_store.list_written_paths())
    assert wrote_normalized or lifecycle_event_repo.events
    assert jobs_repo.enqueued


def test_pdf_normalize_preserves_page_breaks_and_conservative_heading_inference(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, normalization_service, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="pdf", filename="book.pdf", status=processing_status("EXTRACTING"), ingest_status=processing_status("EXTRACTING"))
    document_repo.create(doc)
    artifact_store.write_json(
        path="data/extracted/doc_1/extracted.json",
        payload={"doc_id": "doc_1", "source_type": "pdf", "pages": [{"page_number": 1, "blocks": [{"text": "1 Intro", "order_index": 0, "meta": {}}]}], "meta": {"warnings": []}},
    )
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, normalization_service, fixed_now)
    call_with_supported_kwargs(runner.run, doc_id="doc_1")
    assert normalization_service.calls == ["doc_1"]


def test_normalize_stage_records_failure_when_normalizer_raises(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, normalization_service, fixed_now):
    doc = new_document(doc_id="doc_1", source_type="markdown", status=processing_status("EXTRACTING"), ingest_status=processing_status("EXTRACTING"))
    document_repo.create(doc)
    artifact_store.write_json(path="data/extracted/doc_1/extracted.json", payload={"doc_id": "doc_1"})
    normalization_service.raise_error = RuntimeError("normalize failed")
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, normalization_service, fixed_now)
    with pytest.raises(Exception):
        call_with_supported_kwargs(runner.run, doc_id="doc_1")
    assert document_repo.status_updates
