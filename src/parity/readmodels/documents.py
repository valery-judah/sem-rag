"""Query-facing read model seams over the document lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from parity._contracts import ProcessingStatus, SourceType
from parity.persistence import (
    ChunkRepository,
    DocumentRepository,
    IndexEntryRepository,
    SectionRepository,
)
from parity.query.contracts import CorpusSnapshot


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


class QueryableDocumentRecord(BaseModel):
    """Read-only document projection exposed to the query subsystem."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    source_type: SourceType
    title: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    uploaded_at: datetime


class QueryableSectionRecord(BaseModel):
    """Read-only section projection exposed to the query subsystem."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    heading_path: list[str] = Field(min_length=1)
    depth: int = Field(ge=0)
    parent_section_id: str | None = None
    heading_text: str | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    source_start_offset: int | None = Field(default=None, ge=0)
    source_end_offset: int | None = Field(default=None, ge=0)


class QueryableChunkRecord(BaseModel):
    """Read-only provenance-bearing chunk projection for query use."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    section_id: str | None = None
    text: str = Field(min_length=1)
    ordinal: int = Field(ge=0)
    heading_path: list[str] = Field(min_length=1)
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    source_start_offset: int | None = Field(default=None, ge=0)
    source_end_offset: int | None = Field(default=None, ge=0)


class QueryableCorpusReadModel(Protocol):
    """Read-only query-facing document access contract."""

    def capture_snapshot(
        self,
        workspace_id: str,
        *,
        query_started_at: datetime | None = None,
    ) -> CorpusSnapshot:
        """Return a stable query-time corpus snapshot for a workspace."""

    def list_ready_documents(self, workspace_id: str) -> list[QueryableDocumentRecord]:
        """Return queryable document projections for a workspace."""

    def list_sections_for_snapshot(
        self,
        snapshot: CorpusSnapshot,
    ) -> list[QueryableSectionRecord]:
        """Return queryable sections for a fixed snapshot."""

    def list_chunks_for_snapshot(
        self,
        snapshot: CorpusSnapshot,
    ) -> list[QueryableChunkRecord]:
        """Return provenance-bearing queryable chunks for a fixed snapshot."""


class SqlQueryableCorpusReadModel:
    """Repository-backed query-facing read model over lifecycle outputs."""

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        sections: SectionRepository,
        chunks: ChunkRepository,
        index_entries: IndexEntryRepository,
    ) -> None:
        self._documents = documents
        self._sections = sections
        self._chunks = chunks
        self._index_entries = index_entries

    def capture_snapshot(
        self,
        workspace_id: str,
        *,
        query_started_at: datetime | None = None,
    ) -> CorpusSnapshot:
        documents = self.list_ready_documents(workspace_id)
        eligible_doc_ids = [document.doc_id for document in documents]
        return CorpusSnapshot(
            workspace_id=workspace_id,
            query_started_at=query_started_at or utc_now(),
            eligible_doc_ids=eligible_doc_ids,
            retrieval_index_version=self._derive_retrieval_index_version(eligible_doc_ids),
        )

    def list_ready_documents(self, workspace_id: str) -> list[QueryableDocumentRecord]:
        return [
            QueryableDocumentRecord(
                doc_id=document.doc_id,
                workspace_id=document.workspace_id,
                source_type=document.source_type,
                title=document.title,
                filename=document.filename,
                uploaded_at=document.uploaded_at,
            )
            for document in self._documents.list_by_workspace(workspace_id)
            if document.ingest_status is ProcessingStatus.READY
        ]

    def list_sections_for_snapshot(
        self,
        snapshot: CorpusSnapshot,
    ) -> list[QueryableSectionRecord]:
        records: list[QueryableSectionRecord] = []
        for doc_id in snapshot.eligible_doc_ids:
            for section in self._sections.list_for_document(doc_id):
                records.append(
                    QueryableSectionRecord(
                        section_id=section.section_id,
                        doc_id=section.doc_id,
                        heading_path=section.heading_path,
                        depth=section.depth,
                        parent_section_id=section.parent_section_id,
                        heading_text=section.heading_text,
                        page_start=section.page_start,
                        page_end=section.page_end,
                        source_start_offset=section.source_start_offset,
                        source_end_offset=section.source_end_offset,
                    )
                )
        return records

    def list_chunks_for_snapshot(
        self,
        snapshot: CorpusSnapshot,
    ) -> list[QueryableChunkRecord]:
        records: list[QueryableChunkRecord] = []
        for doc_id in snapshot.eligible_doc_ids:
            for chunk in self._chunks.list_for_document(doc_id):
                if not self._is_provenance_bearing(chunk):
                    continue
                records.append(
                    QueryableChunkRecord(
                        chunk_id=chunk.chunk_id,
                        doc_id=chunk.doc_id,
                        section_id=chunk.section_id,
                        text=chunk.text,
                        ordinal=chunk.ordinal,
                        heading_path=chunk.heading_path,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        source_start_offset=chunk.source_start_offset,
                        source_end_offset=chunk.source_end_offset,
                    )
                )
        return records

    def _derive_retrieval_index_version(self, doc_ids: list[str]) -> str | None:
        versions = {
            entry.index_version
            for doc_id in doc_ids
            for entry in self._index_entries.list_for_document(doc_id)
        }
        if len(versions) != 1:
            return None
        return next(iter(versions))

    @staticmethod
    def _is_provenance_bearing(chunk: object) -> bool:
        section_id = getattr(chunk, "section_id", None)
        page_start = getattr(chunk, "page_start", None)
        source_start_offset = getattr(chunk, "source_start_offset", None)
        return section_id is not None or page_start is not None or source_start_offset is not None
