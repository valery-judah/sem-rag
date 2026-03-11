"""Readiness predicate over persisted lifecycle artifacts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from parity._contracts import ProcessingStatus
from parity.artifacts import FilesystemArtifactStore
from parity.indexing import VectorStore
from parity.persistence import (
    ChunkRepository,
    DocumentRepository,
    IndexEntryRepository,
    SectionRepository,
)


class ReadinessResult(BaseModel):
    """Detailed internal readiness evaluation result."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    is_ready: bool
    reasons: list[str] = Field(default_factory=list)
    section_count: int = 0
    chunk_count: int = 0
    index_entry_count: int = 0


class ReadinessService:
    """Evaluate whether a document is truly retrievable and inspectable."""

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        sections: SectionRepository,
        chunks: ChunkRepository,
        index_entries: IndexEntryRepository,
        artifact_store: FilesystemArtifactStore,
        vector_store: VectorStore,
    ) -> None:
        self._documents = documents
        self._sections = sections
        self._chunks = chunks
        self._index_entries = index_entries
        self._artifact_store = artifact_store
        self._vector_store = vector_store

    def evaluate(self, *, doc_id: str) -> ReadinessResult:
        reasons: list[str] = []
        document = self._documents.get(doc_id)
        if document is None:
            return ReadinessResult(doc_id=doc_id, is_ready=False, reasons=["missing_document"])
        if document.ingest_status is ProcessingStatus.FAILED:
            return ReadinessResult(doc_id=doc_id, is_ready=False, reasons=["document_failed"])

        try:
            self._artifact_store.read_normalized(
                workspace_id=document.workspace_id,
                doc_id=document.doc_id,
            )
        except FileNotFoundError:
            reasons.append("missing_normalized_artifact")

        sections = self._sections.list_for_document(doc_id)
        if not sections:
            reasons.append("missing_sections")
        chunks = self._chunks.list_for_document(doc_id)
        if not chunks:
            reasons.append("missing_chunks")
        entries = self._index_entries.list_for_document(doc_id)
        if len(entries) != len(chunks):
            reasons.append("index_entry_count_mismatch")

        section_ids = {section.section_id for section in sections}
        if any(chunk.section_id is None or chunk.section_id not in section_ids for chunk in chunks):
            reasons.append("broken_chunk_section_linkage")

        if chunks:
            hits = self._vector_store.smoke_query(
                doc_id=doc_id,
                text=chunks[0].text,
                k=1,
            )
            if not hits or hits[0].doc_id != doc_id:
                reasons.append("retrieval_smoke_failed")
        else:
            reasons.append("retrieval_smoke_failed")

        return ReadinessResult(
            doc_id=doc_id,
            is_ready=not reasons,
            reasons=reasons,
            section_count=len(sections),
            chunk_count=len(chunks),
            index_entry_count=len(entries),
        )
