"""Internal indexing seams."""

from .base import ChunkEmbedding, EmbeddingAdapter, IndexEntry, VectorSearchHit, VectorStore
from .embeddings import (
    DeterministicEmbeddingAdapter,
    SentenceTransformerEmbeddingAdapter,
    require_sentence_transformers,
)
from .vector_store import SqlVectorStore

__all__ = [
    "ChunkEmbedding",
    "DeterministicEmbeddingAdapter",
    "EmbeddingAdapter",
    "IndexEntry",
    "SentenceTransformerEmbeddingAdapter",
    "SqlVectorStore",
    "VectorSearchHit",
    "VectorStore",
    "require_sentence_transformers",
]
