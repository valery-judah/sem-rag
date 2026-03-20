from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    status,
)
from pydantic import Field

from doc_forge.app.services.documents import DocumentsAppService
from doc_forge.identifiers import DocId, WorkspaceId

from ..deps import get_documents_app_service
from ..schemas import (
    DocumentArtifactRefsResponse,
    DocumentDetailResponse,
    DocumentStatusResponse,
    ErrorResponse,
    RetryDocumentResponse,
    UploadDocumentResponse,
)

router = APIRouter(tags=["Documents"])


@router.post(
    "/documents",
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
    service: Annotated[DocumentsAppService, Depends(get_documents_app_service)],
    title: Annotated[
        str | None,
        Form(description="Optional custom title for the document. If omitted, uses the filename."),
    ] = None,
) -> UploadDocumentResponse:
    content = file.file.read()
    return service.upload_document(
        workspace_id=workspace_id,
        file_name=file.filename,
        content=content,
        title=title,
    )


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
    service: Annotated[DocumentsAppService, Depends(get_documents_app_service)],
) -> None:
    service.delete_document(doc_id=doc_id)


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
    service: Annotated[DocumentsAppService, Depends(get_documents_app_service)],
) -> DocumentDetailResponse:
    return service.get_document(doc_id=doc_id)


@router.get(
    "/documents/{doc_id}/status",
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
    service: Annotated[DocumentsAppService, Depends(get_documents_app_service)],
) -> DocumentStatusResponse:
    return service.get_document_status(doc_id=doc_id)


@router.get(
    "/documents/{doc_id}/artifacts",
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
    service: Annotated[DocumentsAppService, Depends(get_documents_app_service)],
) -> DocumentArtifactRefsResponse:
    return service.get_document_artifacts(doc_id=doc_id)


@router.post(
    "/documents/{doc_id}/retry",
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
    service: Annotated[DocumentsAppService, Depends(get_documents_app_service)],
) -> RetryDocumentResponse:
    return service.retry_document(doc_id=doc_id)
