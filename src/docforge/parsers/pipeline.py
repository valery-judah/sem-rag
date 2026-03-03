from __future__ import annotations

from docforge.models import AnchorRef, ParsedDocument, RawDocument, Segment, StructureNode
from docforge.parsers.anchors import collect_structure_anchors
from docforge.parsers.interfaces import Canonicalizer, Segmenter, StructureExtractor
from docforge.parsers.registry import ContentTypeCanonicalizer
from docforge.parsers.structure import HeuristicStructureExtractor


class DefaultCanonicalizer:
    def __init__(self, delegate: Canonicalizer | None = None) -> None:
        self._delegate = delegate or ContentTypeCanonicalizer()

    def canonicalize(self, document: RawDocument) -> str:
        return self._delegate.canonicalize(document)


class DefaultStructureExtractor:
    def __init__(self, delegate: StructureExtractor | None = None) -> None:
        self._delegate = delegate or HeuristicStructureExtractor()

    def extract(
        self,
        *,
        document: RawDocument,
        canonical_text: str,
        doc_anchor: AnchorRef,
    ) -> StructureNode:
        return self._delegate.extract(
            document=document,
            canonical_text=canonical_text,
            doc_anchor=doc_anchor,
        )


class DefaultSegmenter:
    def segment(
        self,
        *,
        document: RawDocument,
        canonical_text: str,
        structure_tree: StructureNode,
        doc_anchor: AnchorRef,
    ) -> list[Segment]:
        del structure_tree

        section_segment_id = f"{document.doc_id}:section:0"
        passage_segment_id = f"{document.doc_id}:passage:0"
        has_text = bool(canonical_text.strip())

        section = Segment(
            segment_id=section_segment_id,
            doc_id=document.doc_id,
            type="SECTION",
            child_ids=[passage_segment_id] if has_text else [],
            section_path="root",
            anchor=AnchorRef(
                anchor_id=f"section:{document.doc_id}:root",
                kind="section",
                section_path="root",
            ),
            text=canonical_text,
            token_count=_token_count(canonical_text),
        )
        if not has_text:
            return [section]

        passage = Segment(
            segment_id=passage_segment_id,
            doc_id=document.doc_id,
            type="PASSAGE",
            parent_id=section_segment_id,
            section_path="root",
            anchor=AnchorRef(
                anchor_id=f"passage:{document.doc_id}:0",
                kind="passage",
                section_path="root",
                start_offset=0,
                end_offset=len(canonical_text),
            ),
            text=canonical_text,
            token_count=_token_count(canonical_text),
        )
        return [section, passage]


class ParserPipeline:
    def __init__(
        self,
        *,
        canonicalizer: Canonicalizer | None = None,
        structure_extractor: StructureExtractor | None = None,
        segmenter: Segmenter | None = None,
    ) -> None:
        self.canonicalizer = canonicalizer or DefaultCanonicalizer()
        self.structure_extractor = structure_extractor or DefaultStructureExtractor()
        self.segmenter = segmenter or DefaultSegmenter()

    def parse(self, document: RawDocument) -> ParsedDocument:
        doc_anchor = AnchorRef(anchor_id=f"doc:{document.doc_id}", kind="doc")
        canonical_text = self.canonicalizer.canonicalize(document)
        structure_tree = self.structure_extractor.extract(
            document=document,
            canonical_text=canonical_text,
            doc_anchor=doc_anchor,
        )
        segments = self.segmenter.segment(
            document=document,
            canonical_text=canonical_text,
            structure_tree=structure_tree,
            doc_anchor=doc_anchor,
        )
        section_anchors, block_anchors = collect_structure_anchors(structure_tree)
        if not section_anchors:
            section_anchors = [segment.anchor for segment in segments if segment.type == "SECTION"]
        if not block_anchors:
            block_anchors = [segment.anchor for segment in segments if segment.type == "PASSAGE"]
        return ParsedDocument(
            doc_id=document.doc_id,
            title=_title_from_metadata(document),
            canonical_text=canonical_text,
            structure_tree=structure_tree,
            doc_anchor=doc_anchor,
            section_anchors=section_anchors,
            block_anchors=block_anchors,
            segments=segments,
        )


def _title_from_metadata(document: RawDocument) -> str | None:
    title = document.metadata.get("title")
    if isinstance(title, str):
        return title
    return None


def _token_count(text: str) -> int:
    if not text.strip():
        return 0
    return len(text.split())
