from __future__ import annotations

import hashlib
from dataclasses import dataclass

import structlog
from fastapi import HTTPException, status

from doc_forge.lifecycle.service import (
    DocumentLifecycleService,
    DocumentNotFoundError,
)
from doc_forge.lifecycle.worker import DocumentLifecycleWorker

from ..schemas import RetrievalQueryRequest, RetrievalQueryResponse, WorkerJobResult


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class InternalRetrievalAppService:
    """Application service for the internal retrieval smoke-test route."""

    lifecycle_service: DocumentLifecycleService
    logger: structlog.stdlib.BoundLogger = structlog.stdlib.get_logger(__name__)

    def retrieval_query(self, request: RetrievalQueryRequest) -> RetrievalQueryResponse:
        self.logger.info(
            "retrieval.smoke.started",
            doc_id=request.doc_id,
            k=request.k,
            query_chars=len(request.query),
            query_sha256=_sha256_text(request.query),
        )
        try:
            result = self.lifecycle_service.query_document(
                doc_id=request.doc_id,
                text=request.query,
                k=request.k,
            )
            top_hit = result.hits[0] if result.hits else None
            self.logger.info(
                "retrieval.smoke.completed",
                doc_id=request.doc_id,
                k=request.k,
                hit_count=len(result.hits),
                top_hit_doc_id=None if top_hit is None else top_hit.doc_id,
                top_hit_chunk_id=None if top_hit is None else top_hit.chunk_id,
                http_status=status.HTTP_200_OK,
                status="completed",
            )
            return RetrievalQueryResponse.model_validate(result, from_attributes=True)
        except DocumentNotFoundError as exc:
            self.logger.warning(
                "retrieval.smoke.rejected",
                doc_id=request.doc_id,
                k=request.k,
                error_code="document_not_found",
                http_status=status.HTTP_404_NOT_FOUND,
                status="rejected",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@dataclass(frozen=True, slots=True)
class InternalWorkerAppService:
    """Application service for the internal operator job-runner route."""

    worker: DocumentLifecycleWorker
    logger: structlog.stdlib.BoundLogger = structlog.stdlib.get_logger(__name__)

    def run_next_job(self) -> WorkerJobResult:
        self.logger.info("worker.run_next.invoked")
        job = self.worker.run_next()
        if job is None:
            self.logger.info(
                "worker.run_next.idle",
                http_status=status.HTTP_200_OK,
                status="idle",
            )
        else:
            self.logger.info(
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
