from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .imports import (
    CHUNK_MODEL_CANDIDATES,
    DOCUMENT_JOB_CANDIDATES,
    DOCUMENT_MODEL_CANDIDATES,
    EXTRACTED_ARTIFACT_CANDIDATES,
    INDEX_ENTRY_MODEL_CANDIDATES,
    NORMALIZED_BLOCK_CANDIDATES,
    NORMALIZED_PAYLOAD_CANDIDATES,
    PROCESSING_STATUS_CANDIDATES,
    SECTION_MODEL_CANDIDATES,
    SOURCE_TYPE_CANDIDATES,
    enum_member,
    import_attr_any,
)


FIXED_NOW = datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc)


def _instantiate(cls: type, **kwargs: Any) -> Any:
    sig = inspect.signature(cls)
    filtered = {}
    has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    if has_varkw:
        filtered = dict(kwargs)
    else:
        filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return cls(**filtered)


def processing_status(name: str) -> Any:
    enum_cls = import_attr_any(PROCESSING_STATUS_CANDIDATES)
    return enum_member(enum_cls, name)


def document_cls() -> type:
    return import_attr_any(DOCUMENT_MODEL_CANDIDATES)


def section_cls() -> type:
    return import_attr_any(SECTION_MODEL_CANDIDATES)


def chunk_cls() -> type:
    return import_attr_any(CHUNK_MODEL_CANDIDATES)


def source_type_value(name: str) -> Any:
    enum_cls = import_attr_any(SOURCE_TYPE_CANDIDATES)
    try:
        return enum_member(enum_cls, name.upper())
    except Exception:
        return name.lower()


def index_entry_cls() -> type | None:
    try:
        return import_attr_any(INDEX_ENTRY_MODEL_CANDIDATES)
    except Exception:
        return None


def normalized_block_cls() -> type | None:
    try:
        return import_attr_any(NORMALIZED_BLOCK_CANDIDATES)
    except Exception:
        return None


def normalized_payload_cls() -> type | None:
    try:
        return import_attr_any(NORMALIZED_PAYLOAD_CANDIDATES)
    except Exception:
        return None


def extracted_artifact_cls() -> type | None:
    try:
        return import_attr_any(EXTRACTED_ARTIFACT_CANDIDATES)
    except Exception:
        return None


def document_job_cls() -> type | None:
    try:
        return import_attr_any(DOCUMENT_JOB_CANDIDATES)
    except Exception:
        return None


def new_document(**overrides: Any) -> Any:
    cls = document_cls()
    base = dict(
        doc_id="doc_123",
        workspace_id="ws_1",
        source_type=source_type_value("markdown"),
        title="Test Document",
        filename="test.md",
        checksum="sha256:test",
        uploaded_at=FIXED_NOW,
        raw_storage_path="data/raw/ws_1/doc_123/source.md",
        storage_ref="data/raw/ws_1/doc_123/source.md",
        status=processing_status("REGISTERED"),
        ingest_status=processing_status("REGISTERED"),
        current_job_id=None,
        failure_code=None,
        failure_detail=None,
    )
    base.update(overrides)
    return _instantiate(cls, **base)


def new_section(**overrides: Any) -> Any:
    cls = section_cls()
    base = dict(
        section_id="sec_1",
        doc_id="doc_123",
        parent_section_id=None,
        heading_path=["Intro"],
        heading_text="Intro",
        ordinal=0,
        page_start=None,
        page_end=None,
        block_start=0,
        block_end=2,
        source_offset_start=0,
        source_offset_end=128,
    )
    base.update(overrides)
    return _instantiate(cls, **base)


def new_chunk(**overrides: Any) -> Any:
    cls = chunk_cls()
    base = dict(
        chunk_id="chk_1",
        doc_id="doc_123",
        section_id="sec_1",
        ordinal=0,
        heading_path=["Intro"],
        text="This is a chunk.",
        token_count=4,
        page_start=None,
        page_end=None,
        block_start=0,
        block_end=1,
        source_offset_start=0,
        source_offset_end=16,
    )
    base.update(overrides)
    return _instantiate(cls, **base)


def new_index_entry(**overrides: Any) -> Any:
    cls = index_entry_cls()
    if cls is None:
        @dataclass
        class FallbackIndexEntry:
            chunk_id: str
            doc_id: str
            index_backend: str
            index_key: str
            index_version: str
            published_at: datetime
        cls = FallbackIndexEntry
    base = dict(
        chunk_id="chk_1",
        doc_id="doc_123",
        index_backend="pgvector",
        index_key="idx:chk_1",
        index_version="v1",
        published_at=FIXED_NOW,
    )
    base.update(overrides)
    return _instantiate(cls, **base)


def new_normalized_block(**overrides: Any) -> Any:
    cls = normalized_block_cls()
    if cls is None:
        @dataclass
        class FallbackNormalizedBlock:
            block_id: str
            kind: str
            text: str
            order_index: int
            heading_level: int | None
            page_start: int | None
            page_end: int | None
            source_offset_start: int | None
            source_offset_end: int | None
            meta: dict
        cls = FallbackNormalizedBlock
    base = dict(
        block_id="blk_1",
        kind="paragraph",
        text="hello world",
        order_index=0,
        heading_level=None,
        page_start=None,
        page_end=None,
        source_offset_start=0,
        source_offset_end=11,
        meta={},
    )
    base.update(overrides)
    return _instantiate(cls, **base)


def new_normalized_payload(**overrides: Any) -> Any:
    cls = normalized_payload_cls()
    if cls is None:
        @dataclass
        class FallbackNormalizedPayload:
            doc_id: str
            source_type: str
            blocks: list[Any]
            stats: dict
        cls = FallbackNormalizedPayload
    blocks = overrides.pop("blocks", [new_normalized_block()])
    base = dict(
        doc_id="doc_123",
        source_type="markdown",
        blocks=blocks,
        stats={"block_count": len(blocks)},
    )
    base.update(overrides)
    return _instantiate(cls, **base)


def new_extracted_artifact(**overrides: Any) -> Any:
    cls = extracted_artifact_cls()
    if cls is None:
        @dataclass
        class FallbackExtractedArtifact:
            doc_id: str
            extractor_version: str
            source_type: str
            payload_path: str
            meta: dict
        cls = FallbackExtractedArtifact
    base = dict(
        doc_id="doc_123",
        extractor_version="v1",
        source_type="markdown",
        payload_path="data/extracted/ws_1/doc_123/extracted.json",
        meta={"warnings": []},
    )
    base.update(overrides)
    return _instantiate(cls, **base)


def new_document_job(**overrides: Any) -> Any:
    cls = document_job_cls()
    if cls is None:
        @dataclass
        class FallbackDocumentJob:
            job_id: str
            doc_id: str
            target_stage: str
            status: str
            attempt_count: int
            not_before: datetime | None
            error_code: str | None
            error_detail: str | None
        cls = FallbackDocumentJob
    base = dict(
        job_id="job_1",
        doc_id="doc_123",
        target_stage="extract",
        status="queued",
        attempt_count=0,
        not_before=None,
        error_code=None,
        error_detail=None,
    )
    base.update(overrides)
    return _instantiate(cls, **base)
