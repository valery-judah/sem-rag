"""Base protocols and errors for artifact normalization."""

from __future__ import annotations

from typing import Protocol

from parity._contracts import SourceType
from parity.artifacts import ExtractedArtifact, NormalizedArtifact


class NormalizationError(RuntimeError):
    """Raised when extracted content cannot be normalized safely."""


class Normalizer(Protocol):
    """Protocol for format-specific normalizers."""

    def normalize(self, *, extracted: ExtractedArtifact) -> NormalizedArtifact: ...


class NormalizerRegistry:
    """Dispatch normalization by source type."""

    def __init__(self, *, markdown: Normalizer, pdf: Normalizer) -> None:
        self._markdown = markdown
        self._pdf = pdf

    def normalize(
        self,
        *,
        source_type: SourceType,
        extracted: ExtractedArtifact,
    ) -> NormalizedArtifact:
        if source_type is SourceType.MARKDOWN:
            return self._markdown.normalize(extracted=extracted)
        if source_type is SourceType.PDF:
            return self._pdf.normalize(extracted=extracted)
        raise NormalizationError(f"unsupported source type for normalization: {source_type.value}")
