from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy.engine import Connection

from doc_forge.corpus import Chunk, Section, SourceType
from doc_forge.identifiers import DocId, WorkspaceId
from doc_forge.indexing import ChunkEmbedding, IndexEntry, VectorSearchHit
from doc_forge.lifecycle import ProcessingStatus
from doc_forge.lifecycle.models import FailureCategory, LifecycleEvent, LifecycleStage
from doc_forge.persistence import (
    DocumentJob,
    DocumentJobStage,
    DocumentJobStatus,
    PersistedDocument,
)
from doc_forge.stages import RegisterDocumentRequest
from doc_forge.stages.base import StageExecutionError

FIXED_NOW = datetime(2026, 3, 11, 12, 0, tzinfo=UTC)


def make_persisted_document(
    *,
    doc_id: DocId = "doc-1",
    workspace_id: WorkspaceId = "ws-1",
    source_type: SourceType = SourceType.MARKDOWN,
    ingest_status: ProcessingStatus = ProcessingStatus.REGISTERED,
    failure_code: str | None = None,
    failure_detail: str | None = None,
    title: str = "Doc 1",
    filename: str | None = None,
) -> PersistedDocument:
    resolved_filename = filename or (
        f"{doc_id}.pdf" if source_type is SourceType.PDF else f"{doc_id}.md"
    )
    suffix = ".pdf" if source_type is SourceType.PDF else ".md"
    return PersistedDocument(
        doc_id=doc_id,
        workspace_id=workspace_id,
        source_type=source_type,
        title=title,
        filename=resolved_filename,
        uploaded_at=FIXED_NOW,
        ingest_status=ingest_status,
        storage_ref=f"file:///tmp/{doc_id}{suffix}",
        checksum="sha256:test",
        raw_storage_path=f"raw/{workspace_id}/{doc_id}/source{suffix}",
        failure_code=failure_code,
        failure_detail=failure_detail,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )


def make_job(
    *,
    job_id: str = "job-1",
    doc_id: DocId = "doc-1",
    target_stage: DocumentJobStage = DocumentJobStage.EXTRACT,
    status: DocumentJobStatus = DocumentJobStatus.QUEUED,
    attempt_count: int = 0,
) -> DocumentJob:
    return DocumentJob(
        job_id=job_id,
        doc_id=doc_id,
        target_stage=target_stage,
        status=status,
        attempt_count=attempt_count,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )


def make_failure_event(
    *,
    doc_id: DocId = "doc-1",
    job_stage: DocumentJobStage,
    from_status: ProcessingStatus = ProcessingStatus.EXTRACTING,
    event_id: str = "event-1",
) -> LifecycleEvent:
    return LifecycleEvent(
        event_id=event_id,
        doc_id=doc_id,
        stage=LifecycleStage.EXTRACT,
        from_status=from_status,
        to_status=ProcessingStatus.FAILED,
        occurred_at=FIXED_NOW,
        failure_category=FailureCategory.PROCESSING,
        detail={
            "job_stage": job_stage.value,
            "error_code": "synthetic_failure",
            "error_detail": "synthetic detail",
        },
    )


class RecordingRegisterStage:
    def __init__(self) -> None:
        self.requests: list[RegisterDocumentRequest] = []

    def run(self, request: RegisterDocumentRequest) -> PersistedDocument:
        self.requests.append(request)
        return make_persisted_document(
            doc_id=request.doc_id,
            workspace_id=request.workspace_id,
            source_type=request.source_type,
            ingest_status=ProcessingStatus.REGISTERED,
            title=request.title,
            filename=request.filename,
        )


class InMemoryDocumentRepository:
    def __init__(self, documents: list[PersistedDocument] | None = None) -> None:
        self.documents = {document.doc_id: document for document in documents or []}
        self.status_updates: list[dict[str, object]] = []

    def create(self, document: PersistedDocument, *, connection=None) -> None:
        del connection
        self.documents[document.doc_id] = document

    def get(self, doc_id: DocId, *, connection=None) -> PersistedDocument | None:
        del connection
        return self.documents.get(doc_id)

    def list_by_workspace(self, workspace_id: WorkspaceId) -> list[PersistedDocument]:
        return [
            document
            for document in self.documents.values()
            if document.workspace_id == workspace_id
        ]

    def update_status(
        self,
        *,
        doc_id: DocId,
        status: ProcessingStatus,
        failure_code: str | None = None,
        failure_detail: str | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        current = self.documents.get(doc_id)
        if current is None:
            raise LookupError(f"document {doc_id!r} was not found")
        resolved_updated_at = updated_at or FIXED_NOW
        next_failure_code = failure_code if status is ProcessingStatus.FAILED else None
        next_failure_detail = failure_detail if status is ProcessingStatus.FAILED else None
        self.documents[doc_id] = current.model_copy(
            update={
                "ingest_status": status,
                "failure_code": next_failure_code,
                "failure_detail": next_failure_detail,
                "updated_at": resolved_updated_at,
            }
        )
        self.status_updates.append(
            {
                "doc_id": doc_id,
                "status": status,
                "failure_code": next_failure_code,
                "failure_detail": next_failure_detail,
                "updated_at": resolved_updated_at,
            }
        )


class InMemoryLifecycleEventRepository:
    def __init__(self, events: list[LifecycleEvent] | None = None) -> None:
        self._events_by_doc: dict[str, list[LifecycleEvent]] = defaultdict(list)
        for event in events or []:
            self._events_by_doc[event.doc_id].append(event)
        self.appended: list[LifecycleEvent] = []

    def append(self, event: LifecycleEvent, *, connection=None) -> None:
        del connection
        self._events_by_doc[event.doc_id].append(event)
        self.appended.append(event)

    def list_for_document(self, doc_id: DocId) -> list[LifecycleEvent]:
        return list(self._events_by_doc.get(doc_id, []))


class InMemoryJobRepository:
    def __init__(self, jobs: list[DocumentJob] | None = None) -> None:
        self.jobs = {job.job_id: job for job in jobs or []}

    def create(self, job: DocumentJob) -> None:
        self.jobs[job.job_id] = job

    def claim_next(self) -> DocumentJob | None:
        queued = sorted(
            (job for job in self.jobs.values() if job.status is DocumentJobStatus.QUEUED),
            key=lambda job: (job.created_at, job.job_id),
        )
        if not queued:
            return None
        current = queued[0]
        claimed = current.model_copy(
            update={
                "status": DocumentJobStatus.RUNNING,
                "attempt_count": current.attempt_count + 1,
                "updated_at": FIXED_NOW,
                "error_code": None,
                "error_detail": None,
            }
        )
        self.jobs[current.job_id] = claimed
        return claimed

    def get(self, job_id: str) -> DocumentJob | None:
        return self.jobs.get(job_id)

    def list_for_document(self, doc_id: DocId) -> list[DocumentJob]:
        return sorted(
            [job for job in self.jobs.values() if job.doc_id == doc_id],
            key=lambda job: (job.created_at, job.job_id),
        )

    def has_active_job(self, doc_id: DocId) -> bool:
        return any(
            job.doc_id == doc_id
            and job.status in {DocumentJobStatus.QUEUED, DocumentJobStatus.RUNNING}
            for job in self.jobs.values()
        )

    def mark_succeeded(self, job_id: str) -> DocumentJob:
        return self._update_status(job_id, status=DocumentJobStatus.SUCCEEDED)

    def mark_failed(
        self,
        job_id: str,
        *,
        error_code: str,
        error_detail: str,
    ) -> DocumentJob:
        return self._update_status(
            job_id,
            status=DocumentJobStatus.FAILED,
            error_code=error_code,
            error_detail=error_detail,
        )

    def update(self, job: DocumentJob) -> None:
        if job.job_id not in self.jobs:
            raise LookupError(f"document job {job.job_id!r} was not found")
        self.jobs[job.job_id] = job

    def _update_status(
        self,
        job_id: str,
        *,
        status: DocumentJobStatus,
        error_code: str | None = None,
        error_detail: str | None = None,
    ) -> DocumentJob:
        current = self.jobs.get(job_id)
        if current is None:
            raise LookupError(f"document job {job_id!r} was not found")
        updated = current.model_copy(
            update={
                "status": status,
                "updated_at": FIXED_NOW,
                "error_code": error_code if status is DocumentJobStatus.FAILED else None,
                "error_detail": error_detail if status is DocumentJobStatus.FAILED else None,
            }
        )
        self.jobs[job_id] = updated
        return updated


class InMemoryReplaceRepository:
    def __init__(self, initial_by_doc: dict[str, list[object]] | None = None) -> None:
        self.items_by_doc = {
            doc_id: list(items) for doc_id, items in (initial_by_doc or {}).items()
        }
        self.replacements: list[tuple[str, list[object]]] = []

    def list_for_document(self, doc_id: DocId) -> list[object]:
        return list(self.items_by_doc.get(doc_id, []))

    def replace_for_document(self, doc_id: DocId, items: list[object], **kwargs) -> None:
        del kwargs
        self.items_by_doc[doc_id] = list(items)
        self.replacements.append((doc_id, list(items)))


class StubVectorStore:
    def __init__(self, hits: list[VectorSearchHit] | None = None) -> None:
        self.hits = hits or []
        self.calls: list[tuple[str, str, int]] = []

    def publish_document(self, *, doc_id: DocId, chunks: list[Chunk]) -> list[IndexEntry]:
        del doc_id, chunks
        raise NotImplementedError

    def smoke_query(self, *, doc_id: DocId, text: str, k: int = 1) -> list[VectorSearchHit]:
        self.calls.append((doc_id, text, k))
        return self.hits[:k]


class InMemorySectionRepository:
    def __init__(self, initial_by_doc: dict[str, list[Section]] | None = None) -> None:
        self.items_by_doc = {
            doc_id: list(items) for doc_id, items in (initial_by_doc or {}).items()
        }
        self.replacements: list[tuple[str, list[Section]]] = []

    def save(self, sections: list[Section]) -> None:
        for section in sections:
            current = self.items_by_doc.setdefault(section.doc_id, [])
            current.append(section)

    def list_for_document(self, doc_id: DocId) -> list[Section]:
        return list(self.items_by_doc.get(doc_id, []))

    def replace_for_document(self, doc_id: DocId, sections: list[Section]) -> None:
        self.items_by_doc[doc_id] = list(sections)
        self.replacements.append((doc_id, list(sections)))


class InMemoryChunkRepository:
    def __init__(self, initial_by_doc: dict[str, list[Chunk]] | None = None) -> None:
        self.items_by_doc = {
            doc_id: list(items) for doc_id, items in (initial_by_doc or {}).items()
        }
        self.replacements: list[tuple[str, list[Chunk]]] = []

    def save(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            current = self.items_by_doc.setdefault(chunk.doc_id, [])
            current.append(chunk)

    def list_for_document(self, doc_id: DocId) -> list[Chunk]:
        return list(self.items_by_doc.get(doc_id, []))

    def replace_for_document(self, doc_id: DocId, chunks: list[Chunk]) -> None:
        self.items_by_doc[doc_id] = list(chunks)
        self.replacements.append((doc_id, list(chunks)))


class InMemoryIndexEntryRepository:
    def __init__(self, initial_by_doc: dict[str, list[IndexEntry]] | None = None) -> None:
        self.items_by_doc = {
            doc_id: list(items) for doc_id, items in (initial_by_doc or {}).items()
        }
        self.replacements: list[tuple[str, list[IndexEntry]]] = []

    def clock(self) -> datetime:
        return FIXED_NOW

    def list_for_document(self, doc_id: DocId) -> list[IndexEntry]:
        return list(self.items_by_doc.get(doc_id, []))

    def replace_for_document(
        self,
        doc_id: DocId,
        entries: list[IndexEntry],
        *,
        connection: Connection | None = None,
    ) -> None:
        del connection
        self.items_by_doc[doc_id] = list(entries)
        self.replacements.append((doc_id, list(entries)))


class InMemoryChunkEmbeddingRepository:
    def __init__(self, initial_by_doc: dict[str, list[ChunkEmbedding]] | None = None) -> None:
        self.items_by_doc = {
            doc_id: list(items) for doc_id, items in (initial_by_doc or {}).items()
        }
        self.replacements: list[tuple[str, list[ChunkEmbedding]]] = []

    def list_for_document(self, doc_id: DocId) -> list[ChunkEmbedding]:
        return list(self.items_by_doc.get(doc_id, []))

    def replace_for_document(
        self,
        doc_id: DocId,
        embeddings: list[ChunkEmbedding],
        *,
        connection: Connection | None = None,
    ) -> None:
        del connection
        self.items_by_doc[doc_id] = list(embeddings)
        self.replacements.append((doc_id, list(embeddings)))


class SuccessfulStageRunner:
    def __init__(self, *, next_stage: DocumentJobStage | None) -> None:
        self.target_stage = DocumentJobStage.EXTRACT
        self.next_stage = next_stage
        self.calls: list[DocumentJob] = []

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        self.calls.append(job)
        return self.next_stage


class FailingStageRunner:
    target_stage = DocumentJobStage.EXTRACT

    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        del job
        raise self.exc


def make_stage_error(
    *,
    error_code: str = "extract_failed",
    error_detail: str = "stage failed",
    failure_category: FailureCategory = FailureCategory.PROCESSING,
) -> StageExecutionError:
    return StageExecutionError(
        error_code=error_code,
        error_detail=error_detail,
        failure_category=failure_category,
    )
