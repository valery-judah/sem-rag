from __future__ import annotations

import io

import pytest

from tests.helpers.imports import build_instance, call_with_supported_kwargs


pytestmark = pytest.mark.pipeline


LIFECYCLE_SERVICE_MODULES = ["parity.lifecycle.service"]
LIFECYCLE_SERVICE_CLASSES = ["DocumentLifecycleService"]


def _build_service(document_repo, lifecycle_event_repo, jobs_repo, artifact_store):
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
    )


def test_unsupported_png_is_rejected_explicitly(document_repo, lifecycle_event_repo, jobs_repo, artifact_store):
    service = _build_service(document_repo, lifecycle_event_repo, jobs_repo, artifact_store)
    fileobj = io.BytesIO(b"\x89PNG\r\n\x1a\n")
    fileobj.name = "image.png"
    with pytest.raises(Exception):
        call_with_supported_kwargs(
            service.upload_document,
            workspace_id="ws_1",
            title="not supported",
            file=fileobj,
            filename="image.png",
        )
