from __future__ import annotations

import pytest

from tests.helpers.imports import build_instance, call_with_supported_kwargs
from tests.helpers.builders import new_document, processing_status


pytestmark = pytest.mark.stage


READY_STAGE_MODULES = ["parity.stages.ready"]
READY_STAGE_CLASSES = ["ReadyStage", "ReadyStageRunner"]


def _build_runner(document_repo, lifecycle_event_repo, jobs_repo, readiness_service, fixed_now):
    return build_instance(
        READY_STAGE_MODULES,
        READY_STAGE_CLASSES,
        document_repository=document_repo,
        documents=document_repo,
        lifecycle_event_repository=lifecycle_event_repo,
        lifecycle_events=lifecycle_event_repo,
        jobs=jobs_repo,
        jobs_repository=jobs_repo,
        readiness_service=readiness_service,
        clock=lambda: fixed_now,
        now=lambda: fixed_now,
    )


def test_ready_stage_sets_ready_only_when_readiness_service_passes(document_repo, lifecycle_event_repo, jobs_repo, readiness_service, fixed_now):
    doc = new_document(doc_id="doc_ready", source_type="markdown", status=processing_status("INDEXED"), ingest_status=processing_status("INDEXED"))
    document_repo.create(doc)
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, readiness_service, fixed_now)
    with pytest.raises(Exception):
        call_with_supported_kwargs(runner.run, doc_id="doc_ready")
    # without seeded readiness artifacts, this should fail


def test_ready_stage_appends_final_lifecycle_event(document_repo, lifecycle_event_repo, jobs_repo, readiness_service, ready_document_bundle, fixed_now):
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, readiness_service, fixed_now)
    call_with_supported_kwargs(runner.run, doc_id="doc_ready")
    assert lifecycle_event_repo.events
