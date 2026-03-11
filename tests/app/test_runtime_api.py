from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from sqlalchemy.engine import Engine

from parity._contracts import ProcessingStatus
from parity.app.api import RetrievalQueryRequest
from parity.app.deps import get_document_lifecycle_service
from parity.artifacts import FilesystemArtifactStore
from parity.lifecycle import FailureCategory, LifecycleStage
from parity.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentJobStatus,
    SqlDocumentJobRepository,
    SqlDocumentRepository,
    SqlLifecycleEventRepository,
)

pytestmark = pytest.mark.anyio


def _route_endpoint(app: FastAPI, *, path: str, method: str):
    for route in app.routes:
        if getattr(route, "path", None) == path and method in route.methods:
            return route.endpoint
    raise AssertionError(f"route {method} {path} was not found")


def _service(sql_engine: Engine, tmp_path):
    return get_document_lifecycle_service(
        engine=sql_engine,
        artifact_store=FilesystemArtifactStore(tmp_path / "artifacts"),
    )


class _WorkerStub:
    def __init__(self, job: DocumentJob | None) -> None:
        self._job = job

    def run_next(self) -> DocumentJob | None:
        return self._job


async def test_status_route_returns_404_for_unknown_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await _route_endpoint(app, path="/documents/{doc_id}/status", method="GET")(
            doc_id="missing",
            service=_service(sql_engine, tmp_path),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "document 'missing' was not found"


async def test_artifacts_route_returns_404_for_unknown_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await _route_endpoint(app, path="/documents/{doc_id}/artifacts", method="GET")(
            doc_id="missing",
            service=_service(sql_engine, tmp_path),
        )

    assert exc_info.value.status_code == 404


async def test_retry_route_returns_404_for_unknown_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await _route_endpoint(app, path="/documents/{doc_id}/retry", method="POST")(
            doc_id="missing",
            service=_service(sql_engine, tmp_path),
        )

    assert exc_info.value.status_code == 404


async def test_retry_route_returns_409_for_ready_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path,
    persisted_document_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            ingest_status=ProcessingStatus.READY,
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        await _route_endpoint(app, path="/documents/{doc_id}/retry", method="POST")(
            doc_id="doc-ready",
            service=_service(sql_engine, tmp_path),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "ready documents cannot be retried"


async def test_retry_route_returns_409_for_non_failed_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path,
    persisted_document_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-registered",
            ingest_status=ProcessingStatus.REGISTERED,
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        await _route_endpoint(app, path="/documents/{doc_id}/retry", method="POST")(
            doc_id="doc-registered",
            service=_service(sql_engine, tmp_path),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "retry is only supported for failed documents"


async def test_retry_route_returns_202_and_queued_stage_for_failed_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path,
    persisted_document_factory,
    lifecycle_event_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    lifecycle_events = SqlLifecycleEventRepository(sql_engine)
    jobs = SqlDocumentJobRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-failed",
            ingest_status=ProcessingStatus.FAILED,
            failure_code="extract_failed",
            failure_detail="parse error",
        )
    )
    lifecycle_events.append(
        lifecycle_event_factory(
            doc_id="doc-failed",
            stage=LifecycleStage.EXTRACT,
            from_status=ProcessingStatus.EXTRACTING,
            to_status=ProcessingStatus.FAILED,
            failure_category=FailureCategory.PROCESSING,
            detail={
                "job_stage": "EXTRACT",
                "error_code": "extract_failed",
                "error_detail": "parse error",
            },
        )
    )

    result = await _route_endpoint(app, path="/documents/{doc_id}/retry", method="POST")(
        doc_id="doc-failed",
        service=_service(sql_engine, tmp_path),
    )

    assert result.model_dump() == {
        "doc_id": "doc-failed",
        "ingest_status": "registered",
        "queued_stage": "EXTRACT",
    }
    queued_jobs = jobs.list_for_document("doc-failed")
    assert len(queued_jobs) == 1
    assert queued_jobs[0].target_stage.value == "EXTRACT"


async def test_retrieval_query_returns_404_for_unknown_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await _route_endpoint(app, path="/retrieval/query", method="POST")(
            request=RetrievalQueryRequest(doc_id="missing", query="consensus", k=2),
            service=_service(sql_engine, tmp_path),
        )

    assert exc_info.value.status_code == 404


def test_retrieval_query_validates_positive_k() -> None:
    with pytest.raises(ValidationError):
        RetrievalQueryRequest(doc_id="doc-1", query="consensus", k=0)


async def test_healthz_returns_ok(app: FastAPI) -> None:
    result = await _route_endpoint(app, path="/healthz", method="GET")()

    assert result == {"status": "ok"}


async def test_readyz_returns_ok_when_dependencies_load(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path,
) -> None:
    result = await _route_endpoint(app, path="/readyz", method="GET")(
        service=_service(sql_engine, tmp_path)
    )

    assert result == {"status": "ok"}


async def test_run_next_job_returns_null_payload_when_no_job_exists(app: FastAPI) -> None:
    result = await _route_endpoint(app, path="/internal/run-next-job", method="POST")(
        worker=_WorkerStub(None)
    )

    assert result == {"job_id": None, "status": None}


async def test_run_next_job_returns_job_metadata_when_job_runs(app: FastAPI) -> None:
    result = await _route_endpoint(app, path="/internal/run-next-job", method="POST")(
        worker=_WorkerStub(
            DocumentJob(
                job_id="job-1",
                doc_id="doc-1",
                target_stage=DocumentJobStage.EXTRACT,
                status=DocumentJobStatus.SUCCEEDED,
            )
        )
    )

    assert result == {"job_id": "job-1", "status": "succeeded"}
