"""Deterministic retrieval helpers for the staged query subsystem."""

from __future__ import annotations

import math
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from parity.indexing import EmbeddingAdapter
from parity.readmodels import QueryableCorpusReadModel, QueryableEmbeddedChunkRecord

from .contracts import CorpusSnapshot, InterpretedQuery, QueryRequest, RetrievedCandidate
from .policies import QueryPolicy


class RetrievalQueryRepresentation(BaseModel):
    """Deterministic query representation embedded for dense retrieval."""

    model_config = ConfigDict(extra="forbid")

    query_text: str = Field(min_length=1)
    normalized_question: str = Field(min_length=1)
    request_type: str = Field(min_length=1)
    specificity: str = Field(min_length=1)
    scope_hints: list[str] = Field(default_factory=list)
    requires_source_navigation: bool = False
    synthesis_mode: str = Field(min_length=1)
    diagnostic_raw_question: str = Field(min_length=1)


class QueryRetrievalResult(BaseModel):
    """Structured retrieval result consumed by the Stage 3 retrieval stage."""

    model_config = ConfigDict(extra="forbid")

    representation: RetrievalQueryRepresentation
    embedding_model: str = Field(min_length=1)
    retrieval_backend: str = Field(min_length=1)
    retrievable_chunk_count: int = Field(ge=0)
    candidates: list[RetrievedCandidate] = Field(default_factory=list)


class DenseQueryRetriever(Protocol):
    """Snapshot-scoped dense retriever for query execution."""

    def retrieve(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        policy: QueryPolicy,
    ) -> QueryRetrievalResult:
        """Return structured retrieval candidates for a query run."""


class SnapshotDenseQueryRetriever:
    """Dense cosine retriever over snapshot-scoped embedded chunks."""

    def __init__(
        self,
        *,
        corpus_read_model: QueryableCorpusReadModel,
        embedding_adapter: EmbeddingAdapter,
        backend_name: str = "snapshot-dense-cosine-v1",
    ) -> None:
        self._corpus_read_model = corpus_read_model
        self._embedding_adapter = embedding_adapter
        self._backend_name = backend_name

    def retrieve(
        self,
        *,
        request: QueryRequest,
        snapshot: CorpusSnapshot,
        interpreted_query: InterpretedQuery,
        policy: QueryPolicy,
    ) -> QueryRetrievalResult:
        representation = build_retrieval_query_representation(
            request=request,
            interpreted_query=interpreted_query,
        )
        query_vector = self._embedding_adapter.embed_texts([representation.query_text])[0]
        embedded_chunks = self._corpus_read_model.list_embedded_chunks_for_snapshot(snapshot)
        sorted_chunks = sorted(
            embedded_chunks,
            key=lambda chunk: _sort_key(
                chunk=chunk,
                query_vector=query_vector,
                tie_break_order=policy.deterministic_tie_break_order,
            ),
        )
        capped_chunks = sorted_chunks[: policy.retrieval_candidate_cap]
        candidates = [
            RetrievedCandidate(
                doc_id=chunk.doc_id,
                chunk_id=chunk.chunk_id,
                section_id=chunk.section_id,
                heading_path=chunk.heading_path,
                locator=_render_locator(chunk),
                retrieval_score=_cosine_similarity(query_vector, chunk.embedding_vector),
                retrieval_rank=index,
            )
            for index, chunk in enumerate(capped_chunks, start=1)
        ]
        return QueryRetrievalResult(
            representation=representation,
            embedding_model=self._embedding_adapter.model_name,
            retrieval_backend=self._backend_name,
            retrievable_chunk_count=len(embedded_chunks),
            candidates=candidates,
        )


def build_retrieval_query_representation(
    *,
    request: QueryRequest,
    interpreted_query: InterpretedQuery,
) -> RetrievalQueryRepresentation:
    """Build the deterministic retrieval-ready representation from interpretation output."""

    return RetrievalQueryRepresentation(
        query_text=interpreted_query.normalized_question,
        normalized_question=interpreted_query.normalized_question,
        request_type=interpreted_query.request_type.value,
        specificity=interpreted_query.specificity.value,
        scope_hints=interpreted_query.scope_hints,
        requires_source_navigation=interpreted_query.requires_source_navigation,
        synthesis_mode=interpreted_query.synthesis_mode.value,
        diagnostic_raw_question=request.question,
    )


def _sort_key(
    *,
    chunk: QueryableEmbeddedChunkRecord,
    query_vector: list[float],
    tie_break_order: tuple[str, ...],
) -> tuple[object, ...]:
    score = _cosine_similarity(query_vector, chunk.embedding_vector)
    key: list[object] = []
    for term in tie_break_order:
        if term == "score_desc":
            key.append(-score)
        elif term == "doc_id_asc":
            key.append(chunk.doc_id)
        elif term == "chunk_id_asc":
            key.append(chunk.chunk_id)
        elif term == "section_id_asc":
            key.append("" if chunk.section_id is None else chunk.section_id)
        else:
            key.append("")
    return tuple(key)


def _render_locator(chunk: QueryableEmbeddedChunkRecord) -> str | None:
    if chunk.page_start is not None:
        if chunk.page_end is None or chunk.page_end == chunk.page_start:
            return f"p. {chunk.page_start}"
        return f"pp. {chunk.page_start}-{chunk.page_end}"
    if chunk.source_start_offset is not None:
        if chunk.source_end_offset is None or chunk.source_end_offset == chunk.source_start_offset:
            return f"offset {chunk.source_start_offset}"
        return f"offsets {chunk.source_start_offset}-{chunk.source_end_offset}"
    if chunk.section_id is not None:
        return f"section {chunk.section_id}"
    return None


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)
