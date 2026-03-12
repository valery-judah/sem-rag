"""Stage-3 query retrieval stage."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from doc_forge.query.contracts import (
    CorpusSnapshot,
    InterpretedQuery,
    QueryRequest,
    QueryStageName,
)
from doc_forge.query.policies import QueryPolicy
from doc_forge.query.retrieval import DenseQueryRetriever, QueryRetrievalResult
from doc_forge.query.trace import QueryStageTrace, QueryStageTraceStatus, utc_now

STAGE_NAME = QueryStageName.RETRIEVE


class RetrievalStageResult(BaseModel):
    """Structured result of the retrieval stage."""

    model_config = ConfigDict(extra="forbid")

    retrieval: QueryRetrievalResult
    trace: QueryStageTrace


def run(
    *,
    query_id: str,
    request: QueryRequest,
    snapshot: CorpusSnapshot,
    interpreted_query: InterpretedQuery,
    policy: QueryPolicy,
    retriever: DenseQueryRetriever,
) -> RetrievalStageResult:
    """Retrieve snapshot-scoped candidates and return the trace payload."""

    started_at = utc_now()
    retrieval = retriever.retrieve(
        request=request,
        snapshot=snapshot,
        interpreted_query=interpreted_query,
        policy=policy,
    )
    finished_at = utc_now()
    trace = QueryStageTrace(
        query_id=query_id,
        stage_name=STAGE_NAME,
        stage_status=QueryStageTraceStatus.SUCCEEDED,
        started_at=started_at,
        finished_at=finished_at,
        payload={
            "interpreted_query": interpreted_query.model_dump(mode="json"),
            "retrieval_query_representation": retrieval.representation.model_dump(mode="json"),
            "embedding_model": retrieval.embedding_model,
            "retrieval_backend": retrieval.retrieval_backend,
            "snapshot_doc_ids": snapshot.eligible_doc_ids,
            "retrieval_candidate_cap": policy.retrieval_candidate_cap,
            "retrievable_chunk_count": retrieval.retrievable_chunk_count,
            "candidates": [candidate.model_dump(mode="json") for candidate in retrieval.candidates],
        },
    )
    return RetrievalStageResult(
        retrieval=retrieval,
        trace=trace,
    )
