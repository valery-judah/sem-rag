from __future__ import annotations

from typing import Protocol

from docforge.models import AnchorRef, RawDocument, Segment, StructureNode


class Canonicalizer(Protocol):
    def canonicalize(self, document: RawDocument) -> str:
        """Convert source bytes into deterministic canonical text."""


class StructureExtractor(Protocol):
    def extract(
        self,
        *,
        document: RawDocument,
        canonical_text: str,
        doc_anchor: AnchorRef,
    ) -> StructureNode:
        """Build a structure tree from canonical text."""


class Segmenter(Protocol):
    def segment(
        self,
        *,
        document: RawDocument,
        canonical_text: str,
        structure_tree: StructureNode,
        doc_anchor: AnchorRef,
    ) -> list[Segment]:
        """Emit SECTION/PASSAGE segments from the structure tree."""
