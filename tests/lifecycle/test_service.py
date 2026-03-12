from __future__ import annotations

from typing import cast

import pytest

from doc_forge.artifacts import (
    ExtractedArtifact,
    FilesystemArtifactStore,
    NormalizedArtifact,
)
from doc_forge.corpus import SourceType
from doc_forge.indexing import VectorSearchHit
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.lifecycle.orchestrator import DocumentLifecycleOrchestrator
from doc_forge.lifecycle.service import (
    DocumentLifecycleService,
    DocumentNotFoundError,
    RetryNotAllowedError,
    UnsupportedDocumentError,
)
from doc_forge.persistence import DocumentJobStage, DocumentJobStatus
from doc_forge.stages import RegisterDocumentStage
from tests.lifecycle.support import (
    InMemoryChunkEmbeddingRepository,
    InMemoryChunkRepository,
    InMemoryDocumentRepository,
    InMemoryIndexEntryRepository,
    InMemoryJobRepository,
    InMemoryLifecycleEventRepository,
    InMemorySectionRepository,
    RecordingRegisterStage,
    StubVectorStore,
    make_failure_event,
    make_job,
    make_persisted_document,
)


def _register_stage() -> RegisterDocumentStage:
    return cast(RegisterDocumentStage, RecordingRegisterStage())


def test_upload_document_enqueues_extract_when_orchestrator_is_configured() -> None:
    register_stage = RecordingRegisterStage()
    jobs = InMemoryJobRepository()
    service = DocumentLifecycleService(
        register_stage=cast(RegisterDocumentStage, register_stage),
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
    )

    result = service.upload_document(
        workspace_id="ws-1",
        title="Architecture Notes",
        filename="architecture.md",
        content=b"# Architecture\n",
    )

    assert result.ingest_status is ProcessingStatus.REGISTERED
    assert register_stage.requests[0].source_type is SourceType.MARKDOWN
    assert jobs.list_for_document(result.doc_id)[0].target_stage is DocumentJobStage.EXTRACT


def test_upload_document_accepts_markdown_and_resolves_title_fallback() -> None:
    register_stage = RecordingRegisterStage()
    service = DocumentLifecycleService(register_stage=cast(RegisterDocumentStage, register_stage))

    result = service.upload_document(
        workspace_id="ws-1",
        title="  ",
        filename="team-playbook.markdown",
        content=b"# Team Playbook\n",
    )

    assert result.source_type is SourceType.MARKDOWN
    assert result.title == "team-playbook"
    assert register_stage.requests[0].title == "team-playbook"


def test_upload_document_rejects_missing_filename() -> None:
    service = DocumentLifecycleService(register_stage=_register_stage())

    with pytest.raises(UnsupportedDocumentError, match="must include a filename"):
        service.upload_document(
            workspace_id="ws-1",
            title="Ignored",
            filename="  ",
            content=b"# Notes\n",
        )


def test_upload_document_rejects_non_utf8_markdown() -> None:
    service = DocumentLifecycleService(register_stage=_register_stage())

    with pytest.raises(UnsupportedDocumentError, match="valid UTF-8 text"):
        service.upload_document(
            workspace_id="ws-1",
            title="Broken",
            filename="broken.md",
            content=b"\xff\xfe\x00",
        )


def test_get_document_status_reports_first_active_job_stage() -> None:
    document = make_persisted_document(doc_id="doc-1")
    jobs = InMemoryJobRepository(
        [
            make_job(
                job_id="job-succeeded",
                doc_id=document.doc_id,
                target_stage=DocumentJobStage.EXTRACT,
                status=DocumentJobStatus.SUCCEEDED,
            ),
            make_job(
                job_id="job-active",
                doc_id=document.doc_id,
                target_stage=DocumentJobStage.NORMALIZE,
                status=DocumentJobStatus.QUEUED,
            ),
        ]
    )
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=InMemoryDocumentRepository([document]),
        jobs=jobs,
    )

    result = service.get_document_status(doc_id=document.doc_id)

    assert result.doc_id == document.doc_id
    assert result.active_job_stage is DocumentJobStage.NORMALIZE


def test_get_document_status_raises_for_unknown_document() -> None:
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=InMemoryDocumentRepository(),
    )

    with pytest.raises(DocumentNotFoundError, match="was not found"):
        service.get_document_status(doc_id="missing")


def test_query_document_raises_for_unknown_document() -> None:
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=InMemoryDocumentRepository(),
    )

    with pytest.raises(DocumentNotFoundError, match="was not found"):
        service.query_document(doc_id="missing", text="query")


def test_query_document_requires_vector_store_configuration() -> None:
    document = make_persisted_document(doc_id="doc-1")
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=InMemoryDocumentRepository([document]),
    )

    with pytest.raises(RuntimeError, match="vector store is not configured"):
        service.query_document(doc_id=document.doc_id, text="query")


def test_retry_document_rejects_ready_document() -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.READY,
    )
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=InMemoryDocumentRepository([document]),
    )

    with pytest.raises(RetryNotAllowedError, match="ready documents cannot be retried"):
        service.retry_document(doc_id=document.doc_id)


def test_retry_document_rejects_non_failed_document() -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.REGISTERED,
    )
    jobs = InMemoryJobRepository()
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=InMemoryDocumentRepository([document]),
        jobs=jobs,
        lifecycle_events=InMemoryLifecycleEventRepository(),
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
    )

    with pytest.raises(RetryNotAllowedError, match="only supported for failed documents"):
        service.retry_document(doc_id=document.doc_id)


def test_retry_document_rejects_when_active_job_exists() -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.FAILED,
        failure_code="extract_failed",
        failure_detail="parse error",
    )
    jobs = InMemoryJobRepository(
        [
            make_job(
                doc_id=document.doc_id,
                status=DocumentJobStatus.QUEUED,
            )
        ]
    )
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=InMemoryDocumentRepository([document]),
        jobs=jobs,
        lifecycle_events=InMemoryLifecycleEventRepository(
            [make_failure_event(doc_id=document.doc_id, job_stage=DocumentJobStage.EXTRACT)]
        ),
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
    )

    with pytest.raises(RetryNotAllowedError, match="queued or running work"):
        service.retry_document(doc_id=document.doc_id)


def test_retry_document_rejects_when_failed_event_has_no_job_stage() -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.FAILED,
        failure_code="extract_failed",
        failure_detail="parse error",
    )
    event = make_failure_event(doc_id=document.doc_id, job_stage=DocumentJobStage.EXTRACT)
    event = event.model_copy(update={"detail": {"error_code": "extract_failed"}})
    jobs = InMemoryJobRepository()
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=InMemoryDocumentRepository([document]),
        jobs=jobs,
        lifecycle_events=InMemoryLifecycleEventRepository([event]),
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
    )

    with pytest.raises(RetryNotAllowedError, match="does not identify a retry stage"):
        service.retry_document(doc_id=document.doc_id)


def test_retry_document_resets_to_registered_for_extract_retry(tmp_path) -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.FAILED,
        failure_code="extract_failed",
        failure_detail="parse error",
    )
    jobs = InMemoryJobRepository()
    documents = InMemoryDocumentRepository([document])
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=documents,
        jobs=jobs,
        lifecycle_events=InMemoryLifecycleEventRepository(
            [make_failure_event(doc_id=document.doc_id, job_stage=DocumentJobStage.EXTRACT)]
        ),
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        artifact_store=FilesystemArtifactStore(tmp_path / "artifacts"),
    )

    result = service.retry_document(doc_id=document.doc_id)

    assert result.ingest_status is ProcessingStatus.REGISTERED
    assert result.queued_stage is DocumentJobStage.EXTRACT
    retried = documents.get(document.doc_id)
    assert retried is not None
    assert retried.ingest_status is ProcessingStatus.REGISTERED
    assert jobs.list_for_document(document.doc_id)[0].target_stage is DocumentJobStage.EXTRACT


def test_retry_document_resets_to_extracting_for_normalize_retry(tmp_path) -> None:
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.FAILED,
        failure_code="normalize_failed",
        failure_detail="normalize error",
    )
    jobs = InMemoryJobRepository()
    documents = InMemoryDocumentRepository([document])
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=documents,
        jobs=jobs,
        lifecycle_events=InMemoryLifecycleEventRepository(
            [make_failure_event(doc_id=document.doc_id, job_stage=DocumentJobStage.NORMALIZE)]
        ),
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        artifact_store=FilesystemArtifactStore(tmp_path / "artifacts"),
    )

    result = service.retry_document(doc_id=document.doc_id)

    assert result.ingest_status is ProcessingStatus.EXTRACTING
    assert result.queued_stage is DocumentJobStage.NORMALIZE
    retried = documents.get(document.doc_id)
    assert retried is not None
    assert retried.ingest_status is ProcessingStatus.EXTRACTING


@pytest.mark.parametrize(
    ("stage", "expected_status", "expect_extracted", "expect_normalized", "expected_counts"),
    [
        (
            DocumentJobStage.EXTRACT,
            ProcessingStatus.REGISTERED,
            False,
            False,
            {"sections": 1, "chunks": 1, "index_entries": 1, "chunk_embeddings": 1},
        ),
        (
            DocumentJobStage.NORMALIZE,
            ProcessingStatus.EXTRACTING,
            True,
            False,
            {"sections": 1, "chunks": 1, "index_entries": 1, "chunk_embeddings": 1},
        ),
        (
            DocumentJobStage.SECTIONIZE,
            ProcessingStatus.NORMALIZED,
            True,
            True,
            {"sections": 1, "chunks": 1, "index_entries": 1, "chunk_embeddings": 1},
        ),
        (
            DocumentJobStage.CHUNK,
            ProcessingStatus.NORMALIZED,
            True,
            True,
            {"sections": 0, "chunks": 1, "index_entries": 1, "chunk_embeddings": 1},
        ),
        (
            DocumentJobStage.INDEX,
            ProcessingStatus.CHUNKED,
            True,
            True,
            {"sections": 0, "chunks": 0, "index_entries": 1, "chunk_embeddings": 1},
        ),
    ],
    ids=[
        "extract-retry-cleans-extracted-normalized-and-derived-state",
        "normalize-retry-cleans-normalized-and-derived-state",
        "sectionize-retry-cleans-only-derived-state",
        "chunk-retry-cleans-only-chunk-and-index-state",
        "index-retry-cleans-only-index-state",
    ],
)
def test_retry_document_cleans_expected_downstream_state(
    tmp_path,
    stage: DocumentJobStage,
    expected_status: ProcessingStatus,
    expect_extracted: bool,
    expect_normalized: bool,
    expected_counts: dict[str, int],
) -> None:
    artifact_store = FilesystemArtifactStore(tmp_path / "artifacts")
    document = make_persisted_document(
        doc_id="doc-1",
        ingest_status=ProcessingStatus.FAILED,
        failure_code="stage_failed",
        failure_detail="stage detail",
    )
    docs = InMemoryDocumentRepository([document])
    jobs = InMemoryJobRepository()
    sections = InMemorySectionRepository({document.doc_id: []})
    chunks = InMemoryChunkRepository({document.doc_id: []})
    index_entries = InMemoryIndexEntryRepository({document.doc_id: []})
    chunk_embeddings = InMemoryChunkEmbeddingRepository({document.doc_id: []})
    artifact_store.write_raw(
        workspace_id=document.workspace_id,
        doc_id=document.doc_id,
        source_type=document.source_type,
        content=b"# source\n",
    )
    artifact_store.write_extracted(
        workspace_id=document.workspace_id,
        artifact=ExtractedArtifact(
            doc_id=document.doc_id,
            source_type=document.source_type,
            extractor_version="test-v1",
        ),
    )
    artifact_store.write_normalized(
        workspace_id=document.workspace_id,
        artifact=NormalizedArtifact(
            doc_id=document.doc_id,
            source_type=document.source_type,
            normalizer_version="test-v1",
        ),
    )
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=docs,
        jobs=jobs,
        lifecycle_events=InMemoryLifecycleEventRepository(
            [make_failure_event(doc_id=document.doc_id, job_stage=stage)]
        ),
        orchestrator=DocumentLifecycleOrchestrator(jobs=jobs),
        artifact_store=artifact_store,
        sections=sections,
        chunks=chunks,
        index_entries=index_entries,
        chunk_embeddings=chunk_embeddings,
    )

    result = service.retry_document(doc_id=document.doc_id)

    assert result.ingest_status is expected_status
    assert (
        artifact_store.extracted_path(
            workspace_id=document.workspace_id,
            doc_id=document.doc_id,
        ).exists()
        is expect_extracted
    )
    assert (
        artifact_store.normalized_path(
            workspace_id=document.workspace_id,
            doc_id=document.doc_id,
        ).exists()
        is expect_normalized
    )
    assert len(sections.replacements) == expected_counts["sections"]
    assert len(chunks.replacements) == expected_counts["chunks"]
    assert len(index_entries.replacements) == expected_counts["index_entries"]
    assert len(chunk_embeddings.replacements) == expected_counts["chunk_embeddings"]


def test_get_artifact_refs_returns_existing_and_missing_paths_correctly(tmp_path) -> None:
    artifact_store = FilesystemArtifactStore(tmp_path / "artifacts")
    document = make_persisted_document(doc_id="doc-1")
    artifact_store.write_raw(
        workspace_id=document.workspace_id,
        doc_id=document.doc_id,
        source_type=document.source_type,
        content=b"# Source\n",
    )
    artifact_store.write_extracted(
        workspace_id=document.workspace_id,
        artifact=ExtractedArtifact(
            doc_id=document.doc_id,
            source_type=document.source_type,
            extractor_version="test-v1",
        ),
    )
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=InMemoryDocumentRepository([document]),
        artifact_store=artifact_store,
    )

    result = service.get_artifact_refs(doc_id=document.doc_id)

    assert result.raw_path.endswith("raw/ws-1/doc-1/source.md")
    assert result.extracted_path is not None
    assert result.extracted_path.endswith("extracted/ws-1/doc-1/extracted.json")
    assert result.normalized_path is None


def test_query_document_returns_vector_hits() -> None:
    document = make_persisted_document(doc_id="doc-1")
    vector_store = StubVectorStore(
        hits=[
            VectorSearchHit(chunk_id="chunk-1", doc_id=document.doc_id, score=0.75),
            VectorSearchHit(chunk_id="chunk-2", doc_id=document.doc_id, score=0.5),
        ]
    )
    service = DocumentLifecycleService(
        register_stage=_register_stage(),
        documents=InMemoryDocumentRepository([document]),
        vector_store=vector_store,
    )

    result = service.query_document(doc_id=document.doc_id, text="consensus", k=1)

    assert vector_store.calls == [(document.doc_id, "consensus", 1)]
    assert result.hits == [VectorSearchHit(chunk_id="chunk-1", doc_id=document.doc_id, score=0.75)]
