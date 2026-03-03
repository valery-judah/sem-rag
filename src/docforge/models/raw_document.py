from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, Field

KnownContentType: TypeAlias = Literal[
    "text/plain",
    "text/markdown",
    "text/html",
    "application/pdf",
    "application/octet-stream",
]


class DocumentTimestamps(BaseModel):
    created_at: datetime
    updated_at: datetime


class RawDocument(BaseModel):
    doc_id: str
    source: str
    source_ref: str
    url: str
    content_bytes: bytes
    content_type: KnownContentType | str
    metadata: dict[str, Any] = Field(default_factory=dict)
    acl_scope: dict[str, Any] = Field(default_factory=dict)
    timestamps: DocumentTimestamps
