"""Transport-thin lifecycle coordination for intake and registration."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from parity._contracts import ProcessingStatus, SourceType
from parity.stages import RegisterDocumentRequest, RegisterDocumentStage


class UnsupportedDocumentError(ValueError):
    """Raised when an upload falls outside the MVP-supported source types."""


class UploadDocumentResult(BaseModel):
    """Internal response payload for successful document uploads."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    ingest_status: ProcessingStatus
    source_type: SourceType
    filename: str
    title: str
    uploaded_at: datetime
    checksum: str


class DocumentLifecycleService:
    """Coordinate upload intake and durable registration."""

    def __init__(self, *, register_stage: RegisterDocumentStage) -> None:
        self._register_stage = register_stage

    def upload_document(
        self,
        *,
        workspace_id: str,
        title: str | None,
        filename: str | None,
        content: bytes,
    ) -> UploadDocumentResult:
        """Validate an upload and durably register it."""

        normalized_filename = self._require_filename(filename)
        source_type = self._detect_source_type(
            filename=normalized_filename,
            content=content,
        )
        uploaded_at = datetime.now(UTC)
        resolved_title = self._resolve_title(title=title, filename=normalized_filename)
        checksum = self._checksum(content)
        request = RegisterDocumentRequest(
            doc_id=f"doc_{uuid4().hex}",
            workspace_id=workspace_id,
            source_type=source_type,
            title=resolved_title,
            filename=normalized_filename,
            uploaded_at=uploaded_at,
            checksum=checksum,
            content=content,
        )
        document = self._register_stage.run(request)
        return UploadDocumentResult(
            doc_id=document.doc_id,
            ingest_status=document.ingest_status,
            source_type=document.source_type,
            filename=document.filename,
            title=document.title,
            uploaded_at=document.uploaded_at,
            checksum=document.checksum or checksum,
        )

    def _require_filename(self, filename: str | None) -> str:
        normalized = (filename or "").strip()
        if not normalized:
            raise UnsupportedDocumentError("uploaded file must include a filename")
        return normalized

    def _detect_source_type(self, *, filename: str, content: bytes) -> SourceType:
        suffix = Path(filename).suffix.lower()

        if suffix == ".pdf":
            if not content.startswith(b"%PDF-"):
                raise UnsupportedDocumentError(
                    "uploaded .pdf files must include recognizable PDF header bytes",
                )
            return SourceType.PDF

        if suffix in {".md", ".markdown"}:
            try:
                content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise UnsupportedDocumentError(
                    "uploaded markdown files must be valid UTF-8 text",
                ) from exc
            return SourceType.MARKDOWN

        raise UnsupportedDocumentError(
            "supported uploads are limited to text-based PDF and Markdown files",
        )

    def _resolve_title(self, *, title: str | None, filename: str) -> str:
        normalized_title = (title or "").strip()
        if normalized_title:
            return normalized_title
        return Path(filename).stem

    def _checksum(self, content: bytes) -> str:
        digest = hashlib.sha256(content).hexdigest()
        return f"sha256:{digest}"
