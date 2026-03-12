"""SQLite-compatible vector-store implementation backed by persistence repositories."""

from __future__ import annotations

import math

from sqlalchemy.engine import Engine

from doc_forge.corpus import Chunk
from doc_forge.identifiers import DocId
from doc_forge.persistence.models import utc_now
from doc_forge.persistence.repositories import (
    ChunkEmbeddingRepository,
    IndexEntryRepository,
    SqlChunkEmbeddingRepository,
    SqlIndexEntryRepository,
)

from .base import ChunkEmbedding, EmbeddingAdapter, IndexEntry, VectorSearchHit, VectorStore


class SqlVectorStore(VectorStore):
    """Persist embeddings and publication records, then serve simple smoke queries."""

    def __init__(
        self,
        *,
        engine: Engine,
        embedding_adapter: EmbeddingAdapter,
        index_backend: str = "sqlite-json-vector",
        index_version: str = "v1",
        chunk_embeddings: ChunkEmbeddingRepository | None = None,
        index_entries: IndexEntryRepository | None = None,
    ) -> None:
        self._engine = engine
        self._embedding_adapter = embedding_adapter
        self._index_backend = index_backend
        self._index_version = index_version
        self._chunk_embeddings = chunk_embeddings or SqlChunkEmbeddingRepository(engine)
        self._index_entries = index_entries or SqlIndexEntryRepository(engine)

    def publish_document(
        self,
        *,
        doc_id: DocId,
        chunks: list[Chunk],
    ) -> list[IndexEntry]:
        vectors = self._embedding_adapter.embed_texts([chunk.text for chunk in chunks])
        now = utc_now()
        embeddings = [
            ChunkEmbedding(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                embedding_model=self._embedding_adapter.model_name,
                embedding_vector=vector,
                created_at=now,
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        entries = [
            IndexEntry(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                index_backend=self._index_backend,
                index_key=chunk.chunk_id,
                index_version=self._index_version,
                published_at=now,
            )
            for chunk in chunks
        ]

        with self._engine.begin() as connection:
            self._chunk_embeddings.replace_for_document(
                doc_id,
                embeddings,
                connection=connection,
            )
            self._index_entries.replace_for_document(
                doc_id,
                entries,
                connection=connection,
            )

        return entries

    def smoke_query(
        self,
        *,
        doc_id: DocId,
        text: str,
        k: int = 1,
    ) -> list[VectorSearchHit]:
        if k <= 0:
            raise ValueError("k must be greater than 0")
        query_vector = self._embedding_adapter.embed_texts([text])[0]
        scored: list[VectorSearchHit] = []
        for embedding in self._chunk_embeddings.list_for_document(doc_id):
            scored.append(
                VectorSearchHit(
                    chunk_id=embedding.chunk_id,
                    doc_id=embedding.doc_id,
                    score=_cosine_similarity(query_vector, embedding.embedding_vector),
                )
            )
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:k]

    def delete_document(self, *, doc_id: DocId) -> None:
        with self._engine.begin() as connection:
            self._chunk_embeddings.replace_for_document(
                doc_id,
                [],
                connection=connection,
            )
            self._index_entries.replace_for_document(
                doc_id,
                [],
                connection=connection,
            )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)
