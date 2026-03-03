from __future__ import annotations

from datetime import UTC, datetime

from docforge.config import SegmentationConfig
from docforge.models import AnchorRef, DocumentTimestamps, RawDocument, Segment, StructureNode
from docforge.parsers import HeuristicStructureExtractor, HierarchicalSegmenter

UPDATED_AT = datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)


def _raw_document(*, doc_id: str = "doc-segments") -> RawDocument:
    return RawDocument(
        doc_id=doc_id,
        source="fixture",
        source_ref=f"{doc_id}.md",
        url=f"file:{doc_id}.md",
        content_bytes=b"unused",
        content_type="text/markdown",
        metadata={"title": "Segmenter Fixture"},
        timestamps=DocumentTimestamps(created_at=UPDATED_AT, updated_at=UPDATED_AT),
    )


def _extract_structure(*, document: RawDocument, canonical_text: str) -> StructureNode:
    extractor = HeuristicStructureExtractor()
    return extractor.extract(
        document=document,
        canonical_text=canonical_text,
        doc_anchor=AnchorRef(anchor_id=f"doc:{document.doc_id}", kind="doc"),
    )


def _tokens(count: int, *, prefix: str) -> str:
    return " ".join(f"{prefix}{index}" for index in range(count))


def _segments_by_type(segments: list[Segment], segment_type: str) -> list[Segment]:
    return [segment for segment in segments if segment.type == segment_type]


def test_hierarchical_segmenter_builds_acyclic_hierarchy_with_valid_parent_pointers() -> None:
    canonical_text = (
        f"# Top\n\n{_tokens(350, prefix='top')}\n\n## Child\n\n{_tokens(340, prefix='child')}\n"
    )
    document = _raw_document(doc_id="doc-hierarchy")
    structure = _extract_structure(document=document, canonical_text=canonical_text)
    segmenter = HierarchicalSegmenter(
        config=SegmentationConfig(passage_tokens_target=300, overlap_ratio=0.0)
    )

    segments = segmenter.segment(
        document=document,
        canonical_text=canonical_text,
        structure_tree=structure,
        doc_anchor=AnchorRef(anchor_id=f"doc:{document.doc_id}", kind="doc"),
    )
    section_segments = _segments_by_type(segments, "SECTION")
    passage_segments = _segments_by_type(segments, "PASSAGE")

    assert len(section_segments) == 2
    assert len(passage_segments) >= 3

    all_ids = {segment.segment_id for segment in segments}
    section_ids = {segment.segment_id for segment in section_segments}
    assert all(passage.parent_id in section_ids for passage in passage_segments)
    assert all(
        child_id in all_ids for section in section_segments for child_id in section.child_ids
    )
    assert max(passage.token_count for passage in passage_segments) <= 300

    adjacency: dict[str, list[str]] = {}
    for section in section_segments:
        adjacency[section.segment_id] = [
            child for child in section.child_ids if child in section_ids
        ]

    seen: set[str] = set()
    stack: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in stack:
            raise AssertionError("detected cycle in section hierarchy")
        if node_id in seen:
            return
        stack.add(node_id)
        for child_id in adjacency[node_id]:
            visit(child_id)
        stack.remove(node_id)
        seen.add(node_id)

    roots = [section.segment_id for section in section_segments if section.parent_id is None]
    for root in roots:
        visit(root)

    assert seen == section_ids


def test_hierarchical_segmenter_segment_ids_are_deterministic_for_identical_inputs() -> None:
    canonical_text = (
        "# Deployment\n\n"
        f"{_tokens(330, prefix='deploy')}\n\n"
        "## Rollback\n\n"
        f"{_tokens(320, prefix='rollback')}\n"
    )
    document = _raw_document(doc_id="doc-determinism")
    structure = _extract_structure(document=document, canonical_text=canonical_text)
    segmenter = HierarchicalSegmenter(
        config=SegmentationConfig(passage_tokens_target=300, overlap_ratio=0.1)
    )

    first = segmenter.segment(
        document=document,
        canonical_text=canonical_text,
        structure_tree=structure,
        doc_anchor=AnchorRef(anchor_id=f"doc:{document.doc_id}", kind="doc"),
    )
    second = segmenter.segment(
        document=document,
        canonical_text=canonical_text,
        structure_tree=structure,
        doc_anchor=AnchorRef(anchor_id=f"doc:{document.doc_id}", kind="doc"),
    )

    first_signature = [
        (segment.segment_id, segment.parent_id, segment.anchor.anchor_id, segment.token_count)
        for segment in first
    ]
    second_signature = [
        (segment.segment_id, segment.parent_id, segment.anchor.anchor_id, segment.token_count)
        for segment in second
    ]
    assert first_signature == second_signature


def test_hierarchical_segmenter_splits_large_table_and_code_blocks_without_headings() -> None:
    table_rows = "\n".join(
        f"| row-{index} | {_tokens(12, prefix=f'v{index}_')} |" for index in range(50)
    )
    code_body = "\n\n".join(
        [
            (f'def fn_{index}():\n    return "{_tokens(55, prefix=f"code{index}_")}"')
            for index in range(15)
        ]
    )
    canonical_text = (
        f"| Name | Value |\n| --- | --- |\n{table_rows}\n\n```python\n{code_body}\n```\n"
    )
    document = _raw_document(doc_id="doc-edge-cases")
    structure = _extract_structure(document=document, canonical_text=canonical_text)
    segmenter = HierarchicalSegmenter(
        config=SegmentationConfig(passage_tokens_target=300, overlap_ratio=0.1)
    )

    segments = segmenter.segment(
        document=document,
        canonical_text=canonical_text,
        structure_tree=structure,
        doc_anchor=AnchorRef(anchor_id=f"doc:{document.doc_id}", kind="doc"),
    )
    section_segments = _segments_by_type(segments, "SECTION")
    passage_segments = _segments_by_type(segments, "PASSAGE")

    assert len(section_segments) == 1
    assert section_segments[0].section_path == "root"
    assert len(passage_segments) >= 4

    table_passages = [
        passage
        for passage in passage_segments
        if "table" in passage.metadata.get("block_types", [])
    ]
    assert len(table_passages) >= 2
    assert all("| Name | Value |" in passage.text for passage in table_passages)
    assert all("| --- | --- |" in passage.text for passage in table_passages)

    code_passages = [
        passage for passage in passage_segments if "code" in passage.metadata.get("block_types", [])
    ]
    assert len(code_passages) >= 2
    assert all("```python" in passage.text for passage in code_passages)
    assert all("```" in passage.text for passage in code_passages)

    max_expected_tokens = 300 + int(round(300 * 0.15))
    for passage in passage_segments:
        assert passage.token_count <= max_expected_tokens
