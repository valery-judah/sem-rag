"""Index publication stage for chunked documents."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from doc_forge.identifiers import DocId
from doc_forge.indexing import VectorStore
from doc_forge.lifecycle import LifecycleEvent, LifecycleStage, ProcessingStatus
from doc_forge.persistence import (
    ChunkEmbeddingRepository,
    ChunkRepository,
    DocumentJob,
    DocumentJobStage,
    DocumentRepository,
    IndexEntryRepository,
    LifecycleEventRepository,
)
from doc_forge.stages.base import StageExecutionError, StageRunner


class IndexDocumentStage(StageRunner):
    """Publish persisted chunks to the internal vector store."""

    target_stage = DocumentJobStage.INDEX

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        chunks: ChunkRepository,
        lifecycle_events: LifecycleEventRepository,
        vector_store: VectorStore,
        index_entries: IndexEntryRepository | None = None,
        chunk_embeddings: ChunkEmbeddingRepository | None = None,
    ) -> None:
        self._documents = documents
        self._chunks = chunks
        self._lifecycle_events = lifecycle_events
        self._vector_store = vector_store
        self._index_entries = index_entries
        self._chunk_embeddings = chunk_embeddings

    def run(self, job: DocumentJob) -> DocumentJobStage | None:
        document = self._documents.get(job.doc_id)
        if document is None:
            raise StageExecutionError(
                error_code="missing_document",
                error_detail=f"document {job.doc_id!r} was not found",
            )
        if document.ingest_status is not ProcessingStatus.CHUNKED:
            raise StageExecutionError(
                error_code="invalid_document_status",
                error_detail=(
                    f"index stage requires chunked document, got {document.ingest_status.value}"
                ),
            )
        chunks = self._chunks.list_for_document(document.doc_id)
        if not chunks:
            raise StageExecutionError(
                error_code="missing_chunks",
                error_detail=f"document {document.doc_id!r} has no persisted chunks",
            )
        try:
            entries = self._vector_store.publish_document(doc_id=document.doc_id, chunks=chunks)
        except Exception as exc:
            self._cleanup_partial_publication(document.doc_id)
            raise StageExecutionError(
                error_code="index_failed",
                error_detail=f"failed to index document {document.doc_id!r}: {exc}",
            ) from exc
        if len(entries) != len(chunks):
            self._cleanup_partial_publication(document.doc_id)
            raise StageExecutionError(
                error_code="partial_index_publication",
                error_detail=(
                    f"expected {len(chunks)} index entries for {document.doc_id!r}, "
                    f"got {len(entries)}"
                ),
            )
        completed_at = datetime.now(UTC)
        self._documents.update_status(
            doc_id=document.doc_id,
            status=ProcessingStatus.INDEXED,
            updated_at=completed_at,
        )
        self._lifecycle_events.append(
            LifecycleEvent(
                event_id=f"event_{uuid4().hex}",
                doc_id=document.doc_id,
                stage=LifecycleStage.INDEX,
                from_status=ProcessingStatus.CHUNKED,
                to_status=ProcessingStatus.INDEXED,
                occurred_at=completed_at,
                detail={"index_entry_count": str(len(entries))},
            )
        )
        return DocumentJobStage.READY_CHECK

    def _cleanup_partial_publication(self, doc_id: DocId) -> None:
        if self._chunk_embeddings is not None:
            self._chunk_embeddings.replace_for_document(doc_id, [])
        if self._index_entries is not None:
            self._index_entries.replace_for_document(doc_id, [])
