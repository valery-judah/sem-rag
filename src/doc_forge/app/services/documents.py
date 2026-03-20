from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status

from doc_forge.identifiers import DocId, WorkspaceId
from doc_forge.lifecycle.service import (
    DocumentLifecycleService,
    DocumentNotFoundError,
    RetryNotAllowedError,
    UnsupportedDocumentError,
)
from doc_forge.stages import DocumentRegistrationError

from ..logging import get_logger as get_app_logger
from ..schemas import (
    DocumentArtifactRefsResponse,
    DocumentDetailResponse,
    DocumentStatusResponse,
    RetryDocumentResponse,
    UploadDocumentResponse,
)

logger = get_app_logger(__name__)


def _filename_extension(filename: str | None) -> str | None:
    if not filename:
        return None
    suffix = Path(filename).suffix.lower()
    return suffix or None


class DocumentsAppService:
    """Orchestrates document operations, logging, exception mapping, and response shaping."""

    def __init__(self, lifecycle_service: DocumentLifecycleService) -> None:
        self._service = lifecycle_service

    def upload_document(
        self,
        *,
        workspace_id: WorkspaceId,
        file_name: str | None,
        content: bytes,
        title: str | None,
    ) -> UploadDocumentResponse:
        try:
            result = self._service.upload_document(
                workspace_id=workspace_id,
                title=title,
                filename=file_name,
                content=content,
            )
            logger.info(
                "document.upload.accepted",
                workspace_id=workspace_id,
                doc_id=result.doc_id,
                source_type=result.source_type.value,
                filename_extension=_filename_extension(file_name),
                size_bytes=len(content),
                checksum_sha256=result.checksum,
                http_status=status.HTTP_201_CREATED,
                status="accepted",
            )
            return UploadDocumentResponse.model_validate(result, from_attributes=True)
        except UnsupportedDocumentError as exc:
            logger.warning(
                "document.upload.rejected",
                workspace_id=workspace_id,
                filename_extension=_filename_extension(file_name),
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
                filename_extension=_filename_extension(file_name),
                size_bytes=len(content),
                error_code="document_registration_failed",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                status="rejected",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="document registration failed",
            ) from exc

    def delete_document(self, doc_id: DocId) -> None:
        logger.info("document.delete.started", doc_id=doc_id)
        try:
            self._service.delete_document(doc_id=doc_id)
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

    def get_document(self, doc_id: DocId) -> DocumentDetailResponse:
        try:
            document = self._service.require_document(doc_id)
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

    def get_document_status(self, doc_id: DocId) -> DocumentStatusResponse:
        try:
            result = self._service.get_document_status(doc_id=doc_id)
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
            return DocumentStatusResponse.model_validate(result, from_attributes=True)
        except DocumentNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    def get_document_artifacts(self, doc_id: DocId) -> DocumentArtifactRefsResponse:
        try:
            result = self._service.get_artifact_refs(doc_id=doc_id)
            logger.info(
                "document.artifacts.loaded",
                doc_id=doc_id,
                has_extracted=result.extracted_path is not None,
                has_normalized=result.normalized_path is not None,
                http_status=status.HTTP_200_OK,
                status="loaded",
            )
            return DocumentArtifactRefsResponse.model_validate(result, from_attributes=True)
        except DocumentNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    def retry_document(self, doc_id: DocId) -> RetryDocumentResponse:
        logger.info("document.retry.requested", doc_id=doc_id)
        try:
            result = self._service.retry_document(doc_id=doc_id)
            logger.info(
                "document.retry.queued",
                doc_id=doc_id,
                queued_stage=result.queued_stage.value,
                ingest_status=result.ingest_status.value,
                http_status=status.HTTP_202_ACCEPTED,
                status="queued",
            )
            return RetryDocumentResponse.model_validate(result, from_attributes=True)
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
