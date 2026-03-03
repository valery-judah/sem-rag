from __future__ import annotations

from datetime import UTC, datetime

from docforge.models import AnchorRef, DocumentTimestamps, RawDocument, Segment, StructureNode
from docforge.parsers import ParserPipeline


def _raw_document() -> RawDocument:
    updated_at = datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)
    return RawDocument(
        doc_id="doc-1",
        source="local_file",
        source_ref="./doc.txt",
        url="file:./doc.txt",
        content_bytes=b"hello\r\nworld",
        content_type="text/plain",
        metadata={"title": "Test Doc"},
        timestamps=DocumentTimestamps(created_at=updated_at, updated_at=updated_at),
    )


def test_parser_pipeline_default_components_parse_document() -> None:
    parsed = ParserPipeline().parse(_raw_document())

    assert parsed.doc_id == "doc-1"
    assert parsed.title == "Test Doc"
    assert parsed.canonical_text == "hello\nworld"
    assert parsed.doc_anchor.anchor_id == "doc:doc-1"
    assert [segment.type for segment in parsed.segments] == ["SECTION", "PASSAGE"]
    assert parsed.segments[0].child_ids == [parsed.segments[1].segment_id]
    assert parsed.segments[1].parent_id == parsed.segments[0].segment_id


def test_parser_pipeline_uses_components_via_interface_contract() -> None:
    class FakeCanonicalizer:
        def canonicalize(self, document: RawDocument) -> str:
            assert document.doc_id == "doc-1"
            return "canonical body"

    class FakeStructureExtractor:
        def extract(
            self,
            *,
            document: RawDocument,
            canonical_text: str,
            doc_anchor: AnchorRef,
        ) -> StructureNode:
            assert document.doc_id == "doc-1"
            assert canonical_text == "canonical body"
            assert doc_anchor.anchor_id == "doc:doc-1"
            return StructureNode(
                node_id="root", node_type="doc", text=canonical_text, anchor=doc_anchor
            )

    class FakeSegmenter:
        def segment(
            self,
            *,
            document: RawDocument,
            canonical_text: str,
            structure_tree: StructureNode,
            doc_anchor: AnchorRef,
        ) -> list[Segment]:
            assert document.doc_id == "doc-1"
            assert canonical_text == "canonical body"
            assert structure_tree.node_id == "root"
            assert doc_anchor.anchor_id == "doc:doc-1"

            section = Segment(
                segment_id="section-1",
                doc_id=document.doc_id,
                type="SECTION",
                child_ids=["passage-1"],
                section_path="root",
                anchor=AnchorRef(anchor_id="section:doc-1:root", kind="section"),
                text=canonical_text,
                token_count=2,
            )
            passage = Segment(
                segment_id="passage-1",
                doc_id=document.doc_id,
                type="PASSAGE",
                parent_id="section-1",
                section_path="root",
                anchor=AnchorRef(anchor_id="passage:doc-1:0", kind="passage"),
                text=canonical_text,
                token_count=2,
            )
            return [section, passage]

    pipeline = ParserPipeline(
        canonicalizer=FakeCanonicalizer(),
        structure_extractor=FakeStructureExtractor(),
        segmenter=FakeSegmenter(),
    )
    parsed = pipeline.parse(_raw_document())

    assert [segment.segment_id for segment in parsed.segments] == ["section-1", "passage-1"]
    assert [anchor.anchor_id for anchor in parsed.section_anchors] == ["section:doc-1:root"]
    assert [anchor.anchor_id for anchor in parsed.block_anchors] == ["passage:doc-1:0"]
