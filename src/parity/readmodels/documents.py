"""Query-facing read model seams over the document lifecycle."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from parity._contracts import Chunk, Document


class QueryableDocumentRecord(BaseModel):
    """Read-only document projection exposed to the query subsystem."""

    model_config = ConfigDict(extra="forbid")

    document: Document
    chunks: list[Chunk] = Field(default_factory=list)


class QueryableCorpusReadModel(Protocol):
    """Read-only query-facing document access contract."""

    def list_ready_documents(self, workspace_id: str) -> list[Document]:
        """Return queryable documents for a workspace."""

    def list_queryable_chunks(self, doc_ids: list[str]) -> list[Chunk]:
        """Return provenance-bearing chunks for a fixed document set."""
