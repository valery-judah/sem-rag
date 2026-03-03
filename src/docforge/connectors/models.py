from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


@dataclass
class RawDocument:
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

    def __post_init__(self) -> None:
        """Validate that required fields are present and of the correct type."""
        if not isinstance(self.doc_id, str) or not self.doc_id:
            raise ValueError("doc_id must be a non-empty string")
        if not isinstance(self.source, str) or not self.source:
            raise ValueError("source must be a non-empty string")
        if not isinstance(self.source_ref, str) or not self.source_ref:
            raise ValueError("source_ref must be a non-empty string")
        if not isinstance(self.url, str):
            raise ValueError("url must be a string")
        if not isinstance(self.content_stream, Iterator):
            raise TypeError("content_stream must be an iterator")
        if not isinstance(self.content_type, str) or not self.content_type:
            raise ValueError("content_type must be a non-empty string")
        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dictionary")
        if not isinstance(self.acl_scope, dict):
            raise TypeError("acl_scope must be a dictionary")
        if not isinstance(self.timestamps, dict):
            raise TypeError("timestamps must be a dictionary")
