# ruff: noqa: B008
# pyright: reportUnusedFunction=false
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import structlog
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import Field

from doc_forge.identifiers import DocId, WorkspaceId
from doc_forge.lifecycle.service import (
    DocumentArtifactRefs,
    DocumentLifecycleService,
    DocumentNotFoundError,
    DocumentStatusResult,
    RetryDocumentResult,
    RetryNotAllowedError,
    UnsupportedDocumentError,
    UploadDocumentResult,
)
from doc_forge.stages import DocumentRegistrationError

from ..deps import get_document_lifecycle_service
from ..logging import get_logger as get_app_logger
from ..schemas import DocumentDetailResponse, ErrorResponse


def get_logger() -> structlog.stdlib.BoundLogger:
    return get_app_logger(__name__)


router = APIRouter(tags=["Documents"])


def _filename_extension(filename: str | None) -> str | None:
    if not filename:
        return None
    suffix = Path(filename).suffix.lower()
    return suffix or None


@router.post(
    "/documents",
    response_model=UploadDocumentResult,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Document",
    description=(
        "Upload a PDF or Markdown document to be processed and indexed "
        "into the vector store. This initiates a background lifecycle job.\n\n"
        "**State Transition:** Starts at `REGISTERED` and is queued for `EXTRACT`."
    ),
    responses={
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "model": ErrorResponse,
            "description": "Unsupported document type",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Document registration failed",
        },
    },
)
def upload_document(
    workspace_id: Annotated[
        WorkspaceId,
        Form(description="The workspace this document belongs to."),
    ],
    file: Annotated[UploadFile, File(description="The document file (PDF or Markdown).")],
    service: Annotated[
        DocumentLifecycleService,
        Depends(get_document_lifecycle_service),
    ],
    logger: structlog.stdlib.BoundLogger = Depends(get_logger),
    title: Annotated[
        str | None,
        Form(description="Optional custom title for the document. If omitted, uses the filename."),
    ] = None,
) -> UploadDocumentResult:
    content = file.file.read()
    try:
        result = service.upload_document(
            workspace_id=workspace_id,
            title=title,
            filename=file.filename,
            content=content,
        )
        logger.info(
            "document.upload.accepted",
            workspace_id=workspace_id,
            doc_id=result.doc_id,
            source_type=result.source_type.value,
            filename_extension=_filename_extension(file.filename),
            size_bytes=len(content),
            checksum_sha256=result.checksum,
            http_status=status.HTTP_201_CREATED,
            status="accepted",
        )
        return result
    except UnsupportedDocumentError as exc:
        logger.warning(
            "document.upload.rejected",
            workspace_id=workspace_id,
            filename_extension=_filename_extension(file.filename),
            size_bytes=len(content),
            error_code=exc.error_code,
            http_status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            status="rejected",
        )
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except DocumentRegistrationError as exc:
        logger.exception(
            "document.upload.rejected",
            workspace_id=workspace_id,
            filename_extension=_filename_extension(file.filename),
            size_bytes=len(content),
            error_code="document_registration_failed",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            status="rejected",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="document registration failed",
        ) from exc


@router.delete(
    "/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document",
    description="Completely remove a document, its artifacts, and its indexing data.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Document not found",
        },
    },
)
def delete_document(
    doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
    service: Annotated[
        DocumentLifecycleService,
        Depends(get_document_lifecycle_service),
    ],
    logger: structlog.stdlib.BoundLogger = Depends(get_logger),
) -> None:
    logger.info("document.delete.started", doc_id=doc_id)
    try:
        service.delete_document(doc_id=doc_id)
    except DocumentNotFoundError as exc:
        logger.warning(
            "document.delete.rejected",
            doc_id=doc_id,
            error_code="document_not_found",
            http_status=status.HTTP_404_NOT_FOUND,
            status="rejected",
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    logger.info(
        "document.delete.completed",
        doc_id=doc_id,
        http_status=status.HTTP_204_NO_CONTENT,
        status="completed",
    )


@router.get(
    "/documents/{doc_id}",
    response_model=DocumentDetailResponse,
    summary="Get Document",
    description="Retrieve the core details of a registered document.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Document not found",
        },
    },
)
def get_document(
    doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
    service: Annotated[
        DocumentLifecycleService,
        Depends(get_document_lifecycle_service),
    ],
) -> DocumentDetailResponse:
    try:
        document = service.require_document(doc_id)
        return DocumentDetailResponse(
            doc_id=document.doc_id,
            workspace_id=document.workspace_id,
            source_type=document.source_type.value,
            title=document.title,
            filename=document.filename,
            uploaded_at=document.uploaded_at.isoformat(),
            checksum=document.checksum or "",
            ingest_status=document.ingest_status.value,
            failure_code=document.failure_code,
            failure_detail=document.failure_detail,
            raw_storage_path=document.raw_storage_path or "",
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/documents/{doc_id}/status",
    response_model=DocumentStatusResult,
    summary="Get Document Status",
    description=(
        "Check the current ingestion status and active job stage "
        "for a previously uploaded document."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Document not found",
        },
    },
)
def get_document_status(
    doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
    service: Annotated[
        DocumentLifecycleService,
        Depends(get_document_lifecycle_service),
    ],
    logger: structlog.stdlib.BoundLogger = Depends(get_logger),
) -> DocumentStatusResult:
    try:
        result = service.get_document_status(doc_id=doc_id)
        logger.info(
            "document.status.loaded",
            doc_id=doc_id,
            ingest_status=result.ingest_status.value,
            active_job_stage=(
                None if result.active_job_stage is None else result.active_job_stage.value
            ),
            http_status=status.HTTP_200_OK,
            status="loaded",
        )
        return result
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/documents/{doc_id}/artifacts",
    response_model=DocumentArtifactRefs,
    summary="Get Document Artifact References",
    description=(
        "Retrieve the filesystem paths where raw, extracted, and normalized artifacts are stored."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Document not found",
        },
    },
)
def get_document_artifacts(
    doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
    service: Annotated[
        DocumentLifecycleService,
        Depends(get_document_lifecycle_service),
    ],
    logger: structlog.stdlib.BoundLogger = Depends(get_logger),
) -> DocumentArtifactRefs:
    try:
        result = service.get_artifact_refs(doc_id=doc_id)
        logger.info(
            "document.artifacts.loaded",
            doc_id=doc_id,
            has_extracted=result.extracted_path is not None,
            has_normalized=result.normalized_path is not None,
            http_status=status.HTTP_200_OK,
            status="loaded",
        )
        return result
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/documents/{doc_id}/retry",
    response_model=RetryDocumentResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry Failed Document",
    description=(
        "Queue a retry for a document that failed during its ingestion lifecycle.\n\n"
        "Idempotent: Re-queues the failed stage and resets downstream artifacts."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Document not found",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Retry not allowed or already in progress",
        },
    },
)
def retry_document(
    doc_id: Annotated[DocId, Field(..., description="The unique identifier of the document.")],
    service: Annotated[
        DocumentLifecycleService,
        Depends(get_document_lifecycle_service),
    ],
    logger: structlog.stdlib.BoundLogger = Depends(get_logger),
) -> RetryDocumentResult:
    logger.info("document.retry.requested", doc_id=doc_id)
    try:
        result = service.retry_document(doc_id=doc_id)
        logger.info(
            "document.retry.queued",
            doc_id=doc_id,
            queued_stage=result.queued_stage.value,
            ingest_status=result.ingest_status.value,
            http_status=status.HTTP_202_ACCEPTED,
            status="queued",
        )
        return result
    except DocumentNotFoundError as exc:
        logger.warning(
            "document.retry.rejected",
            doc_id=doc_id,
            error_code="document_not_found",
            http_status=status.HTTP_404_NOT_FOUND,
            status="rejected",
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RetryNotAllowedError as exc:
        logger.warning(
            "document.retry.rejected",
            doc_id=doc_id,
            error_code=exc.error_code,
            http_status=status.HTTP_409_CONFLICT,
            status="rejected",
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
