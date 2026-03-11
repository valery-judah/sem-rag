from __future__ import annotations

import pytest

from tests.helpers.imports import build_instance, call_with_supported_kwargs
from tests.helpers.fakes import make_upload_context
from tests.helpers.builders import processing_status


pytestmark = pytest.mark.stage


REGISTER_STAGE_MODULES = ["parity.stages.register"]
REGISTER_STAGE_CLASSES = ["RegisterStage", "RegisterStageRunner"]


def _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, fixed_now):
    return build_instance(
        REGISTER_STAGE_MODULES,
        REGISTER_STAGE_CLASSES,
        document_repository=document_repo,
        documents=document_repo,
        lifecycle_event_repository=lifecycle_event_repo,
        lifecycle_events=lifecycle_event_repo,
        jobs=jobs_repo,
        jobs_repository=jobs_repo,
        artifact_store=artifact_store,
        clock=lambda: fixed_now,
        now=lambda: fixed_now,
        id_generator=lambda prefix="doc": f"{prefix}_generated",
    )


def test_register_stage_creates_durable_document_record(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, fixed_now):
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, fixed_now)
    upload = make_upload_context(filename="simple.md", title="Simple", source_type="markdown")
    call_with_supported_kwargs(runner.run, upload=upload, upload_context=upload)
    assert len(document_repo.list()) == 1
    doc = document_repo.list()[0]
    assert getattr(doc, "workspace_id") == "ws_1"
    assert getattr(doc, "filename") == "simple.md"
    status = getattr(doc, "status", getattr(doc, "ingest_status"))
    assert getattr(status, "name", str(status)) in {"REGISTERED", "ProcessingStatus.REGISTERED"}


def test_register_stage_persists_raw_artifact_linkage(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, fixed_now):
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, fixed_now)
    upload = make_upload_context(filename="simple.md", title="Simple", source_type="markdown")
    call_with_supported_kwargs(runner.run, upload=upload, upload_context=upload)
    doc = document_repo.list()[0]
    storage_ref = getattr(doc, "raw_storage_path", getattr(doc, "storage_ref", None))
    assert storage_ref
    assert str(storage_ref).endswith(".md")


def test_register_stage_appends_lifecycle_event(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, fixed_now):
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, fixed_now)
    upload = make_upload_context(filename="simple.md", title="Simple", source_type="markdown")
    call_with_supported_kwargs(runner.run, upload=upload, upload_context=upload)
    assert lifecycle_event_repo.events, "registration must append a lifecycle event"


def test_register_stage_enqueues_extract_job(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, fixed_now):
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, fixed_now)
    upload = make_upload_context(filename="simple.md", title="Simple", source_type="markdown")
    call_with_supported_kwargs(runner.run, upload=upload, upload_context=upload)
    assert jobs_repo.enqueued, "registration must enqueue downstream work"
    assert jobs_repo.enqueued[-1]["target_stage"] in {"extract", "EXTRACT", "extracting"}


def test_register_stage_is_idempotent_for_same_active_upload_context(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, fixed_now):
    runner = _build_runner(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, fixed_now)
    upload = make_upload_context(filename="simple.md", title="Simple", source_type="markdown")
    call_with_supported_kwargs(runner.run, upload=upload, upload_context=upload)
    with pytest.raises(Exception):
        call_with_supported_kwargs(runner.run, upload=upload, upload_context=upload)
