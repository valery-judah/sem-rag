"""Internal FastAPI app for document intake."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status

from parity.lifecycle.service import (
    DocumentLifecycleService,
    UnsupportedDocumentError,
    UploadDocumentResult,
)
from parity.stages import DocumentRegistrationError

from .deps import get_document_lifecycle_service


def create_app() -> FastAPI:
    """Create the internal upload app."""

    app = FastAPI()

    @app.post(
        "/documents",
        response_model=UploadDocumentResult,
        status_code=status.HTTP_201_CREATED,
    )
    async def upload_document(
        workspace_id: Annotated[str, Form(min_length=1)],
        file: Annotated[UploadFile, File()],
        service: Annotated[
            DocumentLifecycleService,
            Depends(get_document_lifecycle_service),
        ],
        title: Annotated[str | None, Form()] = None,
    ) -> UploadDocumentResult:
        content = await file.read()
        try:
            return service.upload_document(
                workspace_id=workspace_id,
                title=title,
                filename=file.filename,
                content=content,
            )
        except UnsupportedDocumentError as exc:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(exc),
            ) from exc
        except DocumentRegistrationError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="document registration failed",
            ) from exc

    return app


app = create_app()
