from __future__ import annotations

import io

import pytest

from tests.helpers.builders import processing_status
from tests.helpers.imports import build_instance, call_with_supported_kwargs


pytestmark = [pytest.mark.pipeline, pytest.mark.slow]


LIFECYCLE_SERVICE_MODULES = ["parity.lifecycle.service"]
LIFECYCLE_SERVICE_CLASSES = ["DocumentLifecycleService"]


def _build_service(
    document_repo,
    lifecycle_event_repo,
    jobs_repo,
    artifact_store,
    extraction_service,
    normalization_service,
    structure_service,
    chunking_service,
    index_publication_service,
    readiness_service,
):
    return build_instance(
        LIFECYCLE_SERVICE_MODULES,
        LIFECYCLE_SERVICE_CLASSES,
        document_repository=document_repo,
        documents=document_repo,
        lifecycle_event_repository=lifecycle_event_repo,
        lifecycle_events=lifecycle_event_repo,
        jobs=jobs_repo,
        jobs_repository=jobs_repo,
        artifact_store=artifact_store,
        extraction_service=extraction_service,
        normalization_service=normalization_service,
        structure_service=structure_service,
        chunking_service=chunking_service,
        index_publication_service=index_publication_service,
        readiness_service=readiness_service,
    )


def test_markdown_fixture_upload_enqueues_registration(document_repo, lifecycle_event_repo, jobs_repo, artifact_store, extraction_service, normalization_service, structure_service, chunking_service, index_publication_service, readiness_service):
    service = _build_service(
        document_repo,
        lifecycle_event_repo,
        jobs_repo,
        artifact_store,
        extraction_service,
        normalization_service,
        structure_service,
        chunking_service,
        index_publication_service,
        readiness_service,
    )
    fileobj = io.BytesIO(b"# Intro\n\nDocument lifecycle preserves persisted evidence.\n")
    fileobj.name = "simple.md"
    call_with_supported_kwargs(service.upload_document, workspace_id="ws_1", title="Simple", file=fileobj, filename="simple.md")
    assert jobs_repo.enqueued, "upload should enqueue registration job or equivalent orchestration record"


def test_markdown_ready_document_is_queryable_after_publication(ready_document_bundle, readiness_service):
    assert readiness_service.evaluate(doc_id="doc_ready") is True
