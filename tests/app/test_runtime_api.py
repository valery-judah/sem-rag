from __future__ import annotations

import functools
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute
from pydantic import ValidationError
from sqlalchemy.engine import Engine

from doc_forge.app.deps import (
    get_answer_generator,
    get_document_lifecycle_service,
    get_document_lifecycle_worker,
    get_embedding_adapter,
    get_query_review_service,
    get_query_service,
    get_queryable_corpus_read_model,
)
from doc_forge.app.logging import get_logger
from doc_forge.app.schemas import QueryAnswerResponse, RetrievalQueryRequest, WorkerJobResult
from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.indexing import DeterministicEmbeddingAdapter, SqlVectorStore
from doc_forge.lifecycle import FailureCategory, LifecycleStage, ProcessingStatus
from doc_forge.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentJobStatus,
    SqlChunkRepository,
    SqlDocumentJobRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlLifecycleEventRepository,
)
from doc_forge.query import QueryRequest
from doc_forge.query.contracts import QueryRun, QueryRunStatus, QueryStageName, QueryTerminalFailure
from doc_forge.query.errors import QueryExecutionFailedError
from doc_forge.query.persistence import (
    SqlQueryAnswerStore,
    SqlQueryRunStore,
    SqlQuerySnapshotStore,
    SqlQueryTraceStore,
)

pytestmark = pytest.mark.anyio


def _route_endpoint(app: FastAPI, *, path: str, method: str):
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path and method in route.methods:
            # For testing direct route calls, we strip logger dependency injection manually
            # if the route has it, except for routes that no longer take a logger in the router.
            import inspect

            sig = inspect.signature(route.endpoint)
            if "logger" in sig.parameters:
                return functools.partial(route.endpoint, logger=get_logger())
            return route.endpoint
    raise AssertionError(f"route {method} {path} was not found")


def _service(sql_engine: Engine, tmp_path: Path):
    from doc_forge.app.services.documents import DocumentsAppService

    lifecycle_service = get_document_lifecycle_service(
        engine=sql_engine,
        artifact_store=FilesystemArtifactStore(tmp_path / "artifacts"),
        embedding_adapter=get_embedding_adapter(),
    )
    return DocumentsAppService(lifecycle_service=lifecycle_service)


def _query_service(sql_engine: Engine):
    from doc_forge.app.services.queries import QueriesAppService

    query_service = get_query_service(
        engine=sql_engine,
        corpus_read_model=get_queryable_corpus_read_model(engine=sql_engine),
        embedding_adapter=get_embedding_adapter(),
        answer_generator=get_answer_generator(),
    )
    review_service = get_query_review_service(engine=sql_engine)
    return QueriesAppService(query_service=query_service, review_service=review_service)


def _query_review_service(sql_engine: Engine):
    from doc_forge.app.services.queries import QueriesAppService

    query_service = get_query_service(
        engine=sql_engine,
        corpus_read_model=get_queryable_corpus_read_model(engine=sql_engine),
        embedding_adapter=get_embedding_adapter(),
        answer_generator=get_answer_generator(),
    )
    review_service = get_query_review_service(engine=sql_engine)
    return QueriesAppService(query_service=query_service, review_service=review_service)


def _structured_logs(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [
        cast(dict[str, Any], record.msg)  # type: ignore
        for record in caplog.records
        if isinstance(record.msg, dict)
    ]


class _WorkerStub:
    def __init__(self, job: DocumentJob | None) -> None:
        self._job = job

    def run_next(self) -> DocumentJob | None:
        return self._job


async def test_status_route_returns_404_for_unknown_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path: Path,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _route_endpoint(app, path="/documents/{doc_id}/status", method="GET")(
            doc_id="missing",
            service=_service(sql_engine, tmp_path),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "document 'missing' was not found"


async def test_status_route_returns_job_stage_for_known_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path: Path,
    persisted_document_factory: Any,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    jobs = SqlDocumentJobRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-readying",
            ingest_status=ProcessingStatus.INDEXED,
        )
    )
    jobs.create(
        DocumentJob(
            job_id="job-1",
            doc_id="doc-readying",
            target_stage=DocumentJobStage.READY_CHECK,
            status=DocumentJobStatus.RUNNING,
        )
    )

    result = _route_endpoint(app, path="/documents/{doc_id}/status", method="GET")(
        doc_id="doc-readying",
        service=_service(sql_engine, tmp_path),
    )

    assert result.model_dump() == {
        "doc_id": "doc-readying",
        "ingest_status": "indexed",
        "source_type": "pdf",
        "title": "Title for doc-readying",
        "filename": "doc-readying.pdf",
        "failure_code": None,
        "failure_detail": None,
        "active_job_stage": "READY_CHECK",
    }


async def test_artifacts_route_returns_404_for_unknown_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path: Path,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _route_endpoint(app, path="/documents/{doc_id}/artifacts", method="GET")(
            doc_id="missing",
            service=_service(sql_engine, tmp_path),
        )

    assert exc_info.value.status_code == 404


async def test_retry_route_returns_404_for_unknown_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path: Path,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _route_endpoint(app, path="/documents/{doc_id}/retry", method="POST")(
            doc_id="missing",
            service=_service(sql_engine, tmp_path),
        )

    assert exc_info.value.status_code == 404


async def test_retry_route_returns_409_for_ready_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path: Path,
    persisted_document_factory: Any,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            ingest_status=ProcessingStatus.READY,
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        _route_endpoint(app, path="/documents/{doc_id}/retry", method="POST")(
            doc_id="doc-ready",
            service=_service(sql_engine, tmp_path),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "ready documents cannot be retried"


async def test_retry_route_returns_409_for_non_failed_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path: Path,
    persisted_document_factory: Any,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-registered",
            ingest_status=ProcessingStatus.REGISTERED,
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        _route_endpoint(app, path="/documents/{doc_id}/retry", method="POST")(
            doc_id="doc-registered",
            service=_service(sql_engine, tmp_path),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "retry is only supported for failed documents"


async def test_retry_route_returns_202_and_queued_stage_for_failed_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path: Path,
    persisted_document_factory: Any,
    lifecycle_event_factory: Any,
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
                "job_stage": "SECTIONIZE",
                "error_code": "extract_failed",
                "error_detail": "parse error",
            },
        )
    )

    result = _route_endpoint(app, path="/documents/{doc_id}/retry", method="POST")(
        doc_id="doc-failed",
        service=_service(sql_engine, tmp_path),
    )

    assert result.model_dump() == {
        "doc_id": "doc-failed",
        "ingest_status": "normalized",
        "queued_stage": "SECTIONIZE",
    }
    queued_jobs = jobs.list_for_document("doc-failed")
    assert len(queued_jobs) == 1
    assert queued_jobs[0].target_stage.value == "SECTIONIZE"


async def test_retrieval_query_returns_404_for_unknown_document(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path: Path,
) -> None:
    from doc_forge.app.services.internal import InternalRetrievalAppService

    with pytest.raises(HTTPException) as exc_info:
        _route_endpoint(app, path="/retrieval/query", method="POST")(
            request=RetrievalQueryRequest(doc_id="missing", query="consensus", k=2),
            service=InternalRetrievalAppService(
                lifecycle_service=get_document_lifecycle_service(
                    engine=sql_engine,
                    artifact_store=FilesystemArtifactStore(tmp_path / "artifacts"),
                    embedding_adapter=get_embedding_adapter(),
                ),
            ),
        )

    assert exc_info.value.status_code == 404


def test_retrieval_query_validates_positive_k() -> None:
    with pytest.raises(ValidationError):
        RetrievalQueryRequest(doc_id="doc-1", query="consensus", k=0)


async def test_queries_route_returns_final_answer_and_persists_artifacts(
    app: FastAPI,
    sql_engine: Engine,
    persisted_document_factory: Any,
    chunk_factory: Any,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    snapshot_store = SqlQuerySnapshotStore(sql_engine)
    trace_store = SqlQueryTraceStore(sql_engine)
    answer_store = SqlQueryAnswerStore(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    ready_chunk = chunk_factory(
        doc_id="doc-ready",
        chunk_id="chunk-ready",
        text="vector search uses embeddings to retrieve related passages",
    )
    chunks.save([ready_chunk])
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
    ).publish_document(doc_id="doc-ready", chunks=[ready_chunk])

    result = _route_endpoint(app, path="/queries", method="POST")(
        request=QueryRequest(
            question="What uses embeddings to retrieve related passages?",
            workspace_id="ws-1",
        ),
        service=_query_service(sql_engine),
    )

    assert isinstance(result, QueryAnswerResponse)
    assert (
        "vector search uses embeddings to retrieve related passages"
        in result.answer.answer_text.lower()
    )
    assert result.support_state.value == "sufficient"
    assert result.answer_mode.value == "direct_answer"
    assert result.answer.visible_limitations == []
    assert len(result.citations.citations) == 1
    assert result.citations.material_doc_ids == ["doc-ready"]
    assert (
        result.message == "query answer completed with grounded generation and rendered citations"
    )
    persisted_snapshot = snapshot_store.get_snapshot(result.query_id)
    persisted_traces = trace_store.list_stage_traces(result.query_id)
    persisted_answer = answer_store.get_answer_artifacts(result.query_id)
    assert persisted_snapshot is not None
    assert persisted_snapshot.eligible_doc_ids == ["doc-ready"]
    assert persisted_answer is not None
    assert persisted_answer.answer.answer_text == result.answer.answer_text
    assert len(persisted_traces) == 8
    assert persisted_traces[0].stage_name.value == "interpret"
    assert persisted_traces[1].stage_name.value == "retrieve"
    assert persisted_traces[2].stage_name.value == "select"
    assert persisted_traces[3].stage_name.value == "assemble_context"
    assert persisted_traces[4].stage_name.value == "assess_support"
    assert persisted_traces[5].stage_name.value == "decide_answer_mode"
    assert persisted_traces[6].stage_name.value == "generate"
    assert persisted_traces[7].stage_name.value == "render_citations"


async def test_queries_route_allows_empty_snapshot(
    app: FastAPI,
    sql_engine: Engine,
) -> None:
    result = _route_endpoint(app, path="/queries", method="POST")(
        request=QueryRequest(
            question="What is available in the corpus?",
            workspace_id="empty-ws",
        ),
        service=_query_service(sql_engine),
    )

    assert result.support_state.value == "insufficient"
    assert result.answer_mode.value == "full_abstention"
    assert "does not provide enough support" in result.answer.answer_text
    assert result.citations.citations == []


async def test_healthz_returns_ok(app: FastAPI) -> None:
    from doc_forge.app.services.system import SystemAppService

    result = _route_endpoint(app, path="/healthz", method="GET")(
        service=SystemAppService(
            engine=None,  # type: ignore
            artifact_store=None,  # type: ignore
            vector_store=None,  # type: ignore
        )
    )

    assert result.model_dump() == {"status": "ok"}


async def test_readyz_returns_ok_when_dependencies_load(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path: Path,
) -> None:
    from doc_forge.app.services.system import SystemAppService
    from doc_forge.indexing.embeddings import DeterministicEmbeddingAdapter
    from doc_forge.indexing.vector_store import SqlVectorStore

    vector_store = SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
    )

    result = _route_endpoint(app, path="/readyz", method="GET")(
        service=SystemAppService(
            engine=sql_engine,
            artifact_store=FilesystemArtifactStore(tmp_path / "artifacts"),
            vector_store=vector_store,
        )
    )

    assert result.model_dump() == {"status": "ok"}


async def test_readyz_creates_artifact_root_when_missing(
    app: FastAPI,
    sql_engine: Engine,
    tmp_path: Path,
) -> None:
    artifact_root = tmp_path / "missing-artifacts"

    from doc_forge.app.services.system import SystemAppService
    from doc_forge.indexing.embeddings import DeterministicEmbeddingAdapter
    from doc_forge.indexing.vector_store import SqlVectorStore

    vector_store = SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
    )

    result = _route_endpoint(app, path="/readyz", method="GET")(
        service=SystemAppService(
            engine=sql_engine,
            artifact_store=FilesystemArtifactStore(artifact_root),
            vector_store=vector_store,
        )
    )

    assert result.model_dump() == {"status": "ok"}
    assert artifact_root.exists()


async def test_run_next_job_returns_null_payload_when_no_job_exists(app: FastAPI) -> None:
    from doc_forge.app.services.internal import InternalWorkerAppService

    result = _route_endpoint(app, path="/internal/run-next-job", method="POST")(
        service=InternalWorkerAppService(
            worker=_WorkerStub(None),  # type: ignore
        )
    )

    assert isinstance(result, WorkerJobResult)
    assert result.job_id is None
    assert result.status is None


async def test_run_next_job_returns_job_metadata_when_job_runs(app: FastAPI) -> None:
    from doc_forge.app.services.internal import InternalWorkerAppService

    result = _route_endpoint(app, path="/internal/run-next-job", method="POST")(
        service=InternalWorkerAppService(
            worker=_WorkerStub(  # type: ignore
                DocumentJob(
                    job_id="job-1",
                    doc_id="doc-1",
                    target_stage=DocumentJobStage.EXTRACT,
                    status=DocumentJobStatus.SUCCEEDED,
                )
            ),
        )
    )

    assert isinstance(result, WorkerJobResult)
    assert result.job_id == "job-1"
    assert result.status == "succeeded"


async def test_query_summary_route_returns_persisted_review_view(
    app: FastAPI,
    sql_engine: Engine,
    persisted_document_factory: Any,
    chunk_factory: Any,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    ready_chunk = chunk_factory(
        doc_id="doc-ready",
        chunk_id="chunk-ready",
        text="vector search uses embeddings to retrieve related passages",
    )
    chunks.save([ready_chunk])
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
    ).publish_document(doc_id="doc-ready", chunks=[ready_chunk])

    submitted = _route_endpoint(app, path="/queries", method="POST")(
        request=QueryRequest(
            question="What uses embeddings to retrieve related passages?",
            workspace_id="ws-1",
        ),
        service=_query_service(sql_engine),
    )

    summary = _route_endpoint(app, path="/queries/{query_id}", method="GET")(
        query_id=submitted.query_id,
        service=_query_review_service(sql_engine),
    )

    assert summary.query_id == submitted.query_id
    assert summary.status.value == "succeeded"
    assert summary.has_answer is True
    assert summary.support_state.value == "sufficient"
    assert summary.answer_mode.value == "direct_answer"
    assert summary.snapshot_summary is not None
    assert summary.snapshot_summary.eligible_doc_ids == ["doc-ready"]
    assert summary.trace_summary.trace_count == 8
    assert summary.completed_at is not None


async def test_query_trace_route_returns_ordered_persisted_traces(
    app: FastAPI,
    sql_engine: Engine,
    persisted_document_factory: Any,
    chunk_factory: Any,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    ready_chunk = chunk_factory(
        doc_id="doc-ready",
        chunk_id="chunk-ready",
        text="semantic retrieval uses embeddings for passage search",
    )
    chunks.save([ready_chunk])
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
    ).publish_document(doc_id="doc-ready", chunks=[ready_chunk])

    submitted = _route_endpoint(app, path="/queries", method="POST")(
        request=QueryRequest(
            question="What uses embeddings for passage search?",
            workspace_id="ws-1",
        ),
        service=_query_service(sql_engine),
    )

    review = _route_endpoint(app, path="/queries/{query_id}/trace", method="GET")(
        query_id=submitted.query_id,
        service=_query_review_service(sql_engine),
    )

    assert review.summary.query_id == submitted.query_id
    assert [trace.stage_name.value for trace in review.trace_bundle.stage_traces] == [
        "interpret",
        "retrieve",
        "select",
        "assemble_context",
        "assess_support",
        "decide_answer_mode",
        "generate",
        "render_citations",
    ]
    assert review.final_artifacts is not None
    assert review.final_artifacts.answer.answer_text == submitted.answer.answer_text


async def test_query_citations_route_reads_persisted_answer_state(
    app: FastAPI,
    sql_engine: Engine,
    persisted_document_factory: Any,
    chunk_factory: Any,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    ready_chunk = chunk_factory(
        doc_id="doc-ready",
        chunk_id="chunk-ready",
        text="vector search uses embeddings to retrieve related passages",
    )
    chunks.save([ready_chunk])
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
    ).publish_document(doc_id="doc-ready", chunks=[ready_chunk])

    submitted = _route_endpoint(app, path="/queries", method="POST")(
        request=QueryRequest(
            question="What uses embeddings to retrieve related passages?",
            workspace_id="ws-1",
        ),
        service=_query_service(sql_engine),
    )

    citations = _route_endpoint(app, path="/queries/{query_id}/citations", method="GET")(
        query_id=submitted.query_id,
        service=_query_review_service(sql_engine),
    )

    assert citations.query_id == submitted.query_id
    assert citations.support_state.value == "sufficient"
    assert citations.answer_mode.value == "direct_answer"
    assert citations.citations.material_doc_ids == ["doc-ready"]
    assert citations.model_dump().keys() == {
        "query_id",
        "support_state",
        "answer_mode",
        "trust_failure_labels",
        "citations",
    }


async def test_query_summary_route_returns_failed_run_review_view(
    app: FastAPI,
    sql_engine: Engine,
) -> None:
    run_store = SqlQueryRunStore(sql_engine)
    failed_run = run_store.create_query_run(
        QueryRun(
            query_id="qry-failed",
            workspace_id="ws-1",
            question="What failed?",
            submitted_at=datetime(2026, 3, 11, 12, 0, tzinfo=UTC),
            status=QueryRunStatus.FAILED,
            policy_snapshot={"retrieval_candidate_cap": 24},
            completed_at=datetime(2026, 3, 11, 12, 0, 1, tzinfo=UTC),
            terminal_failure=QueryTerminalFailure(
                error_code="query_stage_contract_violation",
                error_class="QueryStageContractViolationError",
                stage_name=QueryStageName.RENDER_CITATIONS,
                message="non-abstaining answers must not complete without citations",
            ),
        )
    )

    summary = _route_endpoint(app, path="/queries/{query_id}", method="GET")(
        query_id=failed_run.query_id,
        service=_query_review_service(sql_engine),
    )

    assert summary.query_id == "qry-failed"
    assert summary.status.value == "failed"
    assert summary.has_answer is False
    assert summary.terminal_failure is not None
    assert summary.terminal_failure.stage_name.value == "render_citations"


async def test_queries_route_returns_failed_query_id_when_execution_fails(
    app: FastAPI,
) -> None:
    from doc_forge.app.services.queries import QueriesAppService

    class _FailingQueryService:
        def execute_until_answer(self, request: QueryRequest):
            del request
            raise QueryExecutionFailedError(
                query_id="qry-failed-route",
                terminal_failure=QueryTerminalFailure(
                    error_code="query_stage_contract_violation",
                    error_class="QueryStageContractViolationError",
                    stage_name=QueryStageName.RENDER_CITATIONS,
                    message="non-abstaining answers must not complete without citations",
                ),
            )

    with pytest.raises(HTTPException) as exc_info:
        _route_endpoint(app, path="/queries", method="POST")(
            request=QueryRequest(
                question="What failed?",
                workspace_id="ws-1",
            ),
            service=QueriesAppService(
                query_service=_FailingQueryService(),  # type: ignore
                review_service=None,  # type: ignore
            ),
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "query execution failed"


async def test_http_and_query_logs_are_json_and_correlated(
    app: FastAPI,
    sql_engine: Engine,
    persisted_document_factory: Any,
    chunk_factory: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-ready",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    ready_chunk = chunk_factory(
        doc_id="doc-ready",
        chunk_id="chunk-ready",
        text="vector search uses embeddings to retrieve related passages",
    )
    chunks.save([ready_chunk])
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
    ).publish_document(doc_id="doc-ready", chunks=[ready_chunk])

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/queries",
            json={
                "question": "What uses embeddings to retrieve related passages?",
                "workspace_id": "ws-1",
            },
        )

    assert response.status_code == 200
    structured_logs = _structured_logs(caplog)

    assert any(log["event"] == "query.api.started" for log in structured_logs)
    assert any(log["event"] == "query.api.completed" for log in structured_logs)
    assert any(log["event"] == "query.run.started" for log in structured_logs)
    assert any(log["event"] == "query.stage.completed" for log in structured_logs)
    assert any("query_id" in log for log in structured_logs if log["event"] == "query.run.started")
    assert "vector search uses embeddings to retrieve related passages" not in caplog.text


async def test_document_upload_logs_success_and_rejection(
    app: FastAPI,
    caplog: pytest.LogCaptureFixture,
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        accepted = await client.post(
            "/documents",
            data={"workspace_id": "ws-1", "title": "Private Notes"},
            files={"file": ("private.md", b"# Internal Notes\n")},
        )
        rejected = await client.post(
            "/documents",
            data={"workspace_id": "ws-1", "title": "Broken"},
            files={"file": ("broken.txt", b"not supported")},
        )

    assert accepted.status_code == 201
    assert rejected.status_code == 415
    structured_logs = _structured_logs(caplog)

    assert any(
        log["event"] == "document.upload.accepted"
        and log["doc_id"].startswith("doc_")
        and log["http_status"] == 201
        for log in structured_logs
    )
    assert any(
        log["event"] == "document.upload.rejected"
        and log["error_code"] == "unsupported_source_type"
        and log["http_status"] == 415
        for log in structured_logs
    )
    assert "# Internal Notes" not in caplog.text


async def test_retry_delete_and_retrieval_logs_are_structured(
    app: FastAPI,
    sql_engine: Engine,
    persisted_document_factory: Any,
    lifecycle_event_factory: Any,
    chunk_factory: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    lifecycle_events = SqlLifecycleEventRepository(sql_engine)
    jobs = SqlDocumentJobRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    documents.create(
        persisted_document_factory(
            doc_id="doc-retry",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.FAILED,
        )
    )
    lifecycle_events.append(
        lifecycle_event_factory(
            doc_id="doc-retry",
            stage=LifecycleStage.EXTRACT,
            from_status=ProcessingStatus.EXTRACTING,
            to_status=ProcessingStatus.FAILED,
            failure_category=FailureCategory.PROCESSING,
            detail={"job_stage": "EXTRACT", "error_code": "extract_failed"},
        )
    )
    documents.create(
        persisted_document_factory(
            doc_id="doc-ready-reject",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    documents.create(
        persisted_document_factory(
            doc_id="doc-delete",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.REGISTERED,
        )
    )
    documents.create(
        persisted_document_factory(
            doc_id="doc-search",
            workspace_id="ws-1",
            ingest_status=ProcessingStatus.READY,
        )
    )
    ready_chunk = chunk_factory(
        doc_id="doc-search",
        chunk_id="chunk-search",
        text="vector search uses embeddings to retrieve related passages",
    )
    chunks.save([ready_chunk])
    SqlVectorStore(
        engine=sql_engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
        index_entries=SqlIndexEntryRepository(sql_engine),
    ).publish_document(doc_id="doc-search", chunks=[ready_chunk])

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        retry_success = await client.post("/documents/doc-retry/retry")
        retry_reject = await client.post("/documents/doc-ready-reject/retry")
        delete_success = await client.delete("/documents/doc-delete")
        delete_reject = await client.delete("/documents/missing-delete")
        retrieval_success = await client.post(
            "/retrieval/query",
            json={"doc_id": "doc-search", "query": "embeddings", "k": 1},
        )
        retrieval_reject = await client.post(
            "/retrieval/query",
            json={"doc_id": "missing-doc", "query": "embeddings", "k": 1},
        )

    assert retry_success.status_code == 202
    assert retry_reject.status_code == 409
    assert delete_success.status_code == 204
    assert delete_reject.status_code == 404
    assert retrieval_success.status_code == 200
    assert retrieval_reject.status_code == 404
    assert jobs.list_for_document("doc-retry")
    structured_logs = _structured_logs(caplog)

    assert any(
        log["event"] == "document.retry.queued" and log["http_status"] == 202
        for log in structured_logs
    )
    assert any(
        log["event"] == "document.retry.rejected"
        and log["error_code"] == "ready_document"
        and log["http_status"] == 409
        for log in structured_logs
    )
    assert any(
        log["event"] == "document.delete.completed" and log["http_status"] == 204
        for log in structured_logs
    )
    assert any(
        log["event"] == "document.delete.rejected"
        and log["error_code"] == "document_not_found"
        and log["http_status"] == 404
        for log in structured_logs
    )
    assert any(
        log["event"] == "retrieval.smoke.completed"
        and log["hit_count"] == 1
        and log["top_hit_chunk_id"] == "chunk-search"
        for log in structured_logs
    )
    assert any(
        log["event"] == "retrieval.smoke.rejected"
        and log["error_code"] == "document_not_found"
        and log["http_status"] == 404
        for log in structured_logs
    )
    assert "vector search uses embeddings to retrieve related passages" not in caplog.text


async def test_query_api_failure_review_lookup_and_worker_idle_logs(
    app: FastAPI,
    caplog: pytest.LogCaptureFixture,
) -> None:
    class _FailingQueryService:
        def execute_until_answer(self, request: QueryRequest):
            del request
            raise QueryExecutionFailedError(
                query_id="qry-failed-route",
                terminal_failure=QueryTerminalFailure(
                    error_code="query_stage_contract_violation",
                    error_class="QueryStageContractViolationError",
                    stage_name=QueryStageName.RENDER_CITATIONS,
                    message="non-abstaining answers must not complete without citations",
                ),
            )

    app.dependency_overrides[get_query_service] = lambda: _FailingQueryService()
    app.dependency_overrides[get_document_lifecycle_worker] = lambda: _WorkerStub(None)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            failed_query = await client.post(
                "/queries",
                json={"question": "What failed?", "workspace_id": "ws-1"},
            )
            missing_review = await client.get("/queries/missing-query")
            idle_worker = await client.post("/internal/run-next-job")
    finally:
        app.dependency_overrides.clear()

    assert failed_query.status_code == 500
    assert missing_review.status_code == 404
    assert idle_worker.status_code == 200
    structured_logs = _structured_logs(caplog)

    assert any(
        log["event"] == "query.api.rejected"
        and log["query_id"] == "qry-failed-route"
        and log["error_code"] == "query_stage_contract_violation"
        and log["http_status"] == 500
        for log in structured_logs
    )
    assert any(
        log["event"] == "query.review.lookup_failed"
        and log["review_type"] == "summary"
        and log["http_status"] == 404
        for log in structured_logs
    )
    assert any(log["event"] == "worker.run_next.invoked" for log in structured_logs)
    assert any(
        log["event"] == "worker.run_next.idle" and log["http_status"] == 200
        for log in structured_logs
    )
