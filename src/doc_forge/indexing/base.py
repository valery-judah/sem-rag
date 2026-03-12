"""Internal indexing runtime models and protocol seams."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from doc_forge.corpus import Chunk
from doc_forge.identifiers import DocId


class IndexEntry(BaseModel):
    """Publication record proving one chunk is active in the retrieval layer."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    doc_id: DocId
    index_backend: str
    index_key: str
    index_version: str
    published_at: datetime


class ChunkEmbedding(BaseModel):
    """Persisted embedding vector for one active chunk."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    doc_id: DocId
    embedding_model: str
    embedding_vector: list[float] = Field(default_factory=list)
    created_at: datetime


class VectorSearchHit(BaseModel):
    """Single retrieval hit returned by the internal vector-store seam."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    doc_id: DocId
    score: float


class EmbeddingAdapter(Protocol):
    """Adapter interface for chunk/query embedding generation."""

    model_name: str

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]: ...


class VectorStore(Protocol):
    """Publication and smoke-query seam for document-scoped vector persistence."""

    def publish_document(
        self,
        *,
        doc_id: DocId,
        chunks: list[Chunk],
    ) -> list[IndexEntry]: ...

    def smoke_query(
        self,
        *,
        doc_id: DocId,
        text: str,
        k: int = 1,
    ) -> list[VectorSearchHit]: ...
