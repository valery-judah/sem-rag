from __future__ import annotations

import hashlib

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute

from parity.app.deps import get_document_lifecycle_service
from parity.artifacts import FilesystemArtifactStore
from parity.stages import DocumentRegistrationError, RegisterDocumentStage

pytestmark = pytest.mark.anyio


def _upload_endpoint(app: FastAPI):
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == "/documents" and "POST" in route.methods:
            return route.endpoint
    raise AssertionError("upload route was not found")


class _UploadFileStub:
    def __init__(self, *, filename: str, content: bytes) -> None:
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


def _upload_file(filename: str, content: bytes) -> _UploadFileStub:
    return _UploadFileStub(filename=filename, content=content)


def _service(sql_engine, tmp_path):
    return get_document_lifecycle_service(
        engine=sql_engine,
        artifact_store=FilesystemArtifactStore(tmp_path / "artifacts"),
    )


async def test_pdf_upload_registers_successfully(app: FastAPI, sql_engine, tmp_path) -> None:
    payload = b"%PDF-1.7\n1 0 obj\n"

    result = await _upload_endpoint(app)(
        workspace_id="ws-1",
        file=_upload_file("system-design.pdf", payload),
        service=_service(sql_engine, tmp_path),
        title="System Design",
    )

    assert result.model_dump() == {
        "doc_id": result.doc_id,
        "ingest_status": "registered",
        "source_type": "pdf",
        "filename": "system-design.pdf",
        "title": "System Design",
        "uploaded_at": result.uploaded_at,
        "checksum": f"sha256:{hashlib.sha256(payload).hexdigest()}",
    }


async def test_markdown_upload_registers_successfully(
    app: FastAPI,
    sql_engine,
    tmp_path,
) -> None:
    result = await _upload_endpoint(app)(
        workspace_id="ws-1",
        file=_upload_file("ops-notes.md", b"# Ops\n\nThis is UTF-8 markdown.\n"),
        service=_service(sql_engine, tmp_path),
        title="Ops Notes",
    )

    assert result.ingest_status.value == "registered"
    assert result.source_type.value == "markdown"
    assert result.filename == "ops-notes.md"
    assert result.title == "Ops Notes"
    assert result.checksum.startswith("sha256:")


async def test_unsupported_extension_is_rejected_explicitly(
    app: FastAPI,
    sql_engine,
    tmp_path,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await _upload_endpoint(app)(
            workspace_id="ws-1",
            file=_upload_file("notes.txt", b"plain text"),
            service=_service(sql_engine, tmp_path),
            title=None,
        )

    assert exc_info.value.status_code == 415
    assert "text-based PDF and Markdown" in exc_info.value.detail


async def test_fake_pdf_content_with_pdf_extension_is_rejected_explicitly(
    app: FastAPI,
    sql_engine,
    tmp_path,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await _upload_endpoint(app)(
            workspace_id="ws-1",
            file=_upload_file("notes.pdf", b"not really a pdf"),
            service=_service(sql_engine, tmp_path),
            title=None,
        )

    assert exc_info.value.status_code == 415
    assert "PDF header bytes" in exc_info.value.detail


async def test_unsupported_png_is_rejected_explicitly(
    app: FastAPI,
    sql_engine,
    tmp_path,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await _upload_endpoint(app)(
            workspace_id="ws-1",
            file=_upload_file("image.png", b"\x89PNG\r\n\x1a\n"),
            service=_service(sql_engine, tmp_path),
            title=None,
        )

    assert exc_info.value.status_code == 415
    assert "text-based PDF and Markdown" in exc_info.value.detail


async def test_omitted_title_falls_back_to_filename_stem(
    app: FastAPI,
    sql_engine,
    tmp_path,
) -> None:
    result = await _upload_endpoint(app)(
        workspace_id="ws-1",
        file=_upload_file("team-playbook.markdown", b"# Team Playbook\n"),
        service=_service(sql_engine, tmp_path),
        title=None,
    )

    assert result.title == "team-playbook"


async def test_upload_route_maps_registration_error_to_500(
    app: FastAPI,
    sql_engine,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_registration_error(self, request):  # type: ignore[no-untyped-def]
        del self, request
        raise DocumentRegistrationError("synthetic registration failure")

    monkeypatch.setattr(RegisterDocumentStage, "run", _raise_registration_error)

    with pytest.raises(HTTPException) as exc_info:
        await _upload_endpoint(app)(
            workspace_id="ws-1",
            file=_upload_file("doc.md", b"# Doc\n"),
            service=_service(sql_engine, tmp_path),
            title=None,
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "document registration failed"
