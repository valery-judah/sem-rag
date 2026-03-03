from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", arbitrary_types_allowed=True)


class RawDocument(StrictModel):
    """
    Standardized schema for all documents fetched from source connectors.
    """

    doc_id: str
    source: str
    source_ref: str
    url: str
    content_stream: Iterator[bytes]
    content_type: str
    metadata: dict[str, Any]
    acl_scope: dict[str, Any]
    timestamps: dict[str, str]

    @field_validator("doc_id", "source", "source_ref", "content_type")
    @classmethod
    def _validate_non_empty_strings(cls, value: str) -> str:
        if not value:
            raise ValueError("must be a non-empty string")
        return value

    @field_validator("url")
    @classmethod
    def _validate_url_string(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("url must be a string")
        return value

    @field_validator("content_stream", mode="before")
    @classmethod
    def _validate_content_stream_is_iterator(cls, value: Any) -> Any:
        if not isinstance(value, Iterator):
            raise ValueError("content_stream must be an iterator")
        return value
