from __future__ import annotations

import pytest

from tests.helpers.builders import new_document, processing_status
from tests.helpers.imports import build_instance, call_with_supported_kwargs


pytestmark = [pytest.mark.pipeline, pytest.mark.slow]


EXTRACT_STAGE_MODULES = ["parity.stages.extract"]
EXTRACT_STAGE_CLASSES = ["ExtractStage", "ExtractStageRunner"]


def _build_extract_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, fixed_now):
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


def test_malformed_pdf_reaches_failed_with_operator_usable_detail(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, fixed_now):
    doc = new_document(doc_id="doc_bad", source_type="pdf", filename="bad.pdf", status=processing_status("REGISTERED"), ingest_status=processing_status("REGISTERED"))
    document_repo.create(doc)
    extraction_service.raise_error = RuntimeError("malformed pdf")
    runner = _build_extract_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, fixed_now)
    with pytest.raises(Exception):
        call_with_supported_kwargs(runner.run, doc_id="doc_bad")
    assert document_repo.status_updates
    last = document_repo.status_updates[-1]
    assert last["doc_id"] == "doc_bad"


def test_partial_artifacts_do_not_imply_readiness(document_repo, readiness_service):
    doc = new_document(doc_id="doc_partial", source_type="pdf", filename="bad.pdf", status=processing_status("FAILED"), ingest_status=processing_status("FAILED"))
    document_repo.create(doc)
    assert readiness_service.evaluate(doc_id="doc_partial") is False
