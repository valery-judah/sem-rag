"""Base protocols and errors for source extraction."""

from __future__ import annotations

from typing import Protocol

from parity._contracts import SourceType
from parity.artifacts import ExtractedArtifact


class ExtractionError(RuntimeError):
    """Raised when a source cannot be extracted into recoverable text."""


class NoRecoverableTextError(ExtractionError):
    """Raised when the source does not contain usable text for MVP."""


class Extractor(Protocol):
    """Protocol for source-specific text extraction."""

    def extract(self, *, doc_id: str, raw_content: bytes) -> ExtractedArtifact: ...


class ExtractorRegistry:
    """Dispatch extraction by supported source type."""

    def __init__(self, *, markdown: Extractor, pdf: Extractor) -> None:
        self._markdown = markdown
        self._pdf = pdf

    def extract(
        self,
        *,
        doc_id: str,
        source_type: SourceType,
        raw_content: bytes,
    ) -> ExtractedArtifact:
        if source_type is SourceType.MARKDOWN:
            return self._markdown.extract(doc_id=doc_id, raw_content=raw_content)
        if source_type is SourceType.PDF:
            return self._pdf.extract(doc_id=doc_id, raw_content=raw_content)
        raise ExtractionError(f"unsupported source type for extraction: {source_type.value}")
