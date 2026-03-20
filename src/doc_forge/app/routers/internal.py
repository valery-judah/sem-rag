# ruff: noqa: B008
# pyright: reportUnusedFunction=false
from __future__ import annotations

import hashlib
from typing import Annotated

import structlog
from fastapi import APIRouter, Body, Depends, HTTPException, status

from doc_forge.lifecycle.service import (
    DocumentLifecycleService,
    DocumentNotFoundError,
    RetrievalQueryResult,
)
from doc_forge.lifecycle.worker import DocumentLifecycleWorker

from ..deps import get_document_lifecycle_service, get_document_lifecycle_worker
from ..logging import get_logger as get_app_logger
from ..schemas import ErrorResponse, RetrievalQueryRequest, WorkerJobResult


def get_logger() -> structlog.stdlib.BoundLogger:
    return get_app_logger(__name__)


router = APIRouter()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@router.post(
    "/retrieval/query",
    response_model=RetrievalQueryResult,
    status_code=status.HTTP_200_OK,
    summary="Smoke Query Document",
    tags=["Retrieval"],
    description=(
        "Perform a semantic search against the vector store "
        "for a specific document to retrieve the top-K chunks.\n\n"
        "Note: This is an internal smoke test endpoint for validating indexing."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Document not found",
        },
    },
)
def retrieval_query(
    request: Annotated[RetrievalQueryRequest, Body(description="The query parameters.")],
    service: Annotated[
        DocumentLifecycleService,
        Depends(get_document_lifecycle_service),
    ],
    logger: structlog.stdlib.BoundLogger = Depends(get_logger),
) -> RetrievalQueryResult:
    logger.info(
        "retrieval.smoke.started",
        doc_id=request.doc_id,
        k=request.k,
        query_chars=len(request.query),
        query_sha256=_sha256_text(request.query),
    )
    try:
        result = service.query_document(
            doc_id=request.doc_id,
            text=request.query,
            k=request.k,
        )
        top_hit = result.hits[0] if result.hits else None
        logger.info(
            "retrieval.smoke.completed",
            doc_id=request.doc_id,
            k=request.k,
            hit_count=len(result.hits),
            top_hit_doc_id=None if top_hit is None else top_hit.doc_id,
            top_hit_chunk_id=None if top_hit is None else top_hit.chunk_id,
            http_status=status.HTTP_200_OK,
            status="completed",
        )
        return result
    except DocumentNotFoundError as exc:
        logger.warning(
            "retrieval.smoke.rejected",
            doc_id=request.doc_id,
            k=request.k,
            error_code="document_not_found",
            http_status=status.HTTP_404_NOT_FOUND,
            status="rejected",
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/internal/run-next-job",
    response_model=WorkerJobResult,
    status_code=status.HTTP_200_OK,
    summary="Run Next Job (Internal)",
    description=(
        "Trigger the internal background worker to process the next job in the "
        "document lifecycle queue."
    ),
    tags=["Internal Operator"],
)
def run_next_job(
    worker: Annotated[DocumentLifecycleWorker, Depends(get_document_lifecycle_worker)],
    logger: structlog.stdlib.BoundLogger = Depends(get_logger),
) -> WorkerJobResult:
    logger.info("worker.run_next.invoked")
    job = worker.run_next()
    if job is None:
        logger.info(
            "worker.run_next.idle",
            http_status=status.HTTP_200_OK,
            status="idle",
        )
    else:
        logger.info(
            "worker.run_next.completed",
            doc_id=job.doc_id,
            job_id=job.job_id,
            stage_name=job.target_stage.value,
            http_status=status.HTTP_200_OK,
            status=job.status.value,
        )
    return WorkerJobResult(
        job_id=None if job is None else job.job_id,
        status=None if job is None else job.status.value,
    )
