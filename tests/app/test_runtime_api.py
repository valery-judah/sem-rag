from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from sqlalchemy.engine import Engine

from parity._contracts import ProcessingStatus
from parity.app.api import QuerySubmissionResult, RetrievalQueryRequest
from parity.app.deps import (
    get_document_lifecycle_service,
    get_query_service,
    get_queryable_corpus_read_model,
)
from parity.artifacts import FilesystemArtifactStore
from parity.indexing import DeterministicEmbeddingAdapter, SqlVectorStore
from parity.lifecycle import FailureCategory, LifecycleStage
from parity.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentJobStatus,
    SqlChunkRepository,
    SqlDocumentJobRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlLifecycleEventRepository,
)
from parity.query import QueryRequest
from parity.query.persistence import SqlQuerySnapshotStore, SqlQueryTraceStore

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


def _query_service(sql_engine: Engine):
    return get_query_service(
        engine=sql_engine,
        corpus_read_model=get_queryable_corpus_read_model(engine=sql_engine),
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


async def test_queries_route_returns_stage5_result_and_persists_traces(
    app: FastAPI,
    sql_engine: Engine,
    persisted_document_factory,
    chunk_factory,
) -> None:
    documents = SqlDocumentRepository(sql_engine)
    chunks = SqlChunkRepository(sql_engine)
    snapshot_store = SqlQuerySnapshotStore(sql_engine)
    trace_store = SqlQueryTraceStore(sql_engine)
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

    result = await _route_endpoint(app, path="/queries", method="POST")(
        request=QueryRequest(
            question="What uses embeddings to retrieve related passages?",
            workspace_id="ws-1",
        ),
        service=_query_service(sql_engine),
    )

    assert isinstance(result, QuerySubmissionResult)
    assert result.workspace_id == "ws-1"
    assert result.status.value == "running"
    assert result.snapshot.eligible_doc_ids == ["doc-ready"]
    assert result.interpreted_query.request_type.value == "fact_lookup"
    assert len(result.retrieved_candidates) == 1
    assert result.retrieved_candidates[0].chunk_id == "chunk-ready"
    assert len(result.selected_candidates) == 1
    assert result.selected_candidates[0].chunk_id == "chunk-ready"
    assert len(result.evidence_sets) == 1
    assert result.evidence_sets[0].evidence_units[0].candidate.chunk_id == "chunk-ready"
    assert result.context_manifest.included_evidence_set_ids == ["es-1"]
    assert result.context_manifest.context_items[0].evidence_set_id == "es-1"
    assert result.support_assessment.support_state.value == "sufficient"
    assert result.answer_mode_decision.answer_mode.value == "direct_answer"
    assert (
        result.message == "query support assessment completed; grounded generation and "
        "citation rendering are not implemented yet"
    )
    persisted_snapshot = snapshot_store.get_snapshot(result.query_id)
    persisted_traces = trace_store.list_stage_traces(result.query_id)
    assert persisted_snapshot is not None
    assert persisted_snapshot.model_dump() == result.snapshot.model_dump()
    assert len(persisted_traces) == 6
    assert persisted_traces[0].stage_name.value == "interpret"
    assert persisted_traces[1].stage_name.value == "retrieve"
    assert persisted_traces[2].stage_name.value == "select"
    assert persisted_traces[3].stage_name.value == "assemble_context"
    assert persisted_traces[4].stage_name.value == "assess_support"
    assert persisted_traces[5].stage_name.value == "decide_answer_mode"


async def test_queries_route_allows_empty_snapshot(
    app: FastAPI,
    sql_engine: Engine,
) -> None:
    result = await _route_endpoint(app, path="/queries", method="POST")(
        request=QueryRequest(
            question="What is available in the corpus?",
            workspace_id="empty-ws",
        ),
        service=_query_service(sql_engine),
    )

    assert result.snapshot.eligible_doc_ids == []
    assert result.interpreted_query.request_type.value == "fact_lookup"
    assert result.selected_candidates == []
    assert result.evidence_sets == []
    assert result.context_manifest.included_evidence_set_ids == []
    assert result.context_manifest.context_items == []
    assert result.support_assessment.support_state.value == "insufficient"
    assert result.answer_mode_decision.answer_mode.value == "full_abstention"


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
