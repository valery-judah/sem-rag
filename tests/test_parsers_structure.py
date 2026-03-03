from __future__ import annotations

from datetime import UTC, datetime

from docforge.models import AnchorRef, DocumentTimestamps, RawDocument
from docforge.parsers import (
    HeuristicStructureExtractor,
    collect_structure_anchors,
    normalize_anchor_slug,
)

UPDATED_AT = datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)


def _raw_document(*, doc_id: str = "doc-structure") -> RawDocument:
    return RawDocument(
        doc_id=doc_id,
        source="fixture",
        source_ref=f"{doc_id}.md",
        url=f"file:{doc_id}.md",
        content_bytes=b"unused",
        content_type="text/markdown",
        metadata={"title": "Structure Fixture"},
        timestamps=DocumentTimestamps(created_at=UPDATED_AT, updated_at=UPDATED_AT),
    )


def test_structure_extractor_builds_hierarchy_for_heading_paragraph_list_table_and_code() -> None:
    canonical_text = (
        "# Billing Guide\n\n"
        "Intro paragraph.\n\n"
        "- Retry daily\n"
        "- Alert on failure\n\n"
        "## Metrics\n"
        "| Service | Window |\n"
        "| --- | --- |\n"
        "| Billing | Nightly |\n\n"
        "```python\n"
        "def add(a, b):\n"
        "    return a + b\n"
        "```\n"
    )
    extractor = HeuristicStructureExtractor()
    structure = extractor.extract(
        document=_raw_document(),
        canonical_text=canonical_text,
        doc_anchor=AnchorRef(anchor_id="doc:doc-structure", kind="doc"),
    )

    assert [node.node_type for node in structure.children] == ["heading"]
    billing = structure.children[0]
    assert billing.title == "Billing Guide"
    assert billing.anchor is not None
    assert billing.anchor.anchor_id == "section:doc-structure:billing-guide"

    assert [node.node_type for node in billing.children] == ["paragraph", "list", "heading"]
    metrics = billing.children[2]
    assert metrics.title == "Metrics"
    assert metrics.anchor is not None
    assert metrics.anchor.anchor_id == "section:doc-structure:billing-guide/metrics"

    assert [node.node_type for node in metrics.children] == ["table", "code"]
    table = metrics.children[0]
    assert table.metadata["headers"] == ["Service", "Window"]
    code = metrics.children[1]
    assert code.text is not None
    assert code.text.startswith("```python\n")
    assert code.text.endswith("```")


def test_structure_anchor_collision_suffixes_are_deterministic_for_repeated_headings() -> None:
    canonical_text = (
        "# Billing & Payments\n\n"
        "## Retry Policy\n"
        "First detail.\n\n"
        "## Retry Policy\n"
        "Second detail.\n\n"
        "# Billing & Payments\n"
    )
    extractor = HeuristicStructureExtractor()
    structure = extractor.extract(
        document=_raw_document(doc_id="doc-anchors"),
        canonical_text=canonical_text,
        doc_anchor=AnchorRef(anchor_id="doc:doc-anchors", kind="doc"),
    )
    section_anchors, _ = collect_structure_anchors(structure)

    assert normalize_anchor_slug(" Billing & Payments ", default="section") == "billing-payments"
    assert [anchor.anchor_id for anchor in section_anchors] == [
        "section:doc-anchors:billing-payments",
        "section:doc-anchors:billing-payments/retry-policy",
        "section:doc-anchors:billing-payments/retry-policy-2",
        "section:doc-anchors:billing-payments-2",
    ]
    assert len({anchor.anchor_id for anchor in section_anchors}) == len(section_anchors)


def test_structure_block_anchors_include_ranges_and_stable_root_path() -> None:
    canonical_text = "Line one.\n\nLine two.\nLine three.\n"
    extractor = HeuristicStructureExtractor()
    structure = extractor.extract(
        document=_raw_document(doc_id="doc-blocks"),
        canonical_text=canonical_text,
        doc_anchor=AnchorRef(anchor_id="doc:doc-blocks", kind="doc"),
    )
    _, block_anchors = collect_structure_anchors(structure)

    assert [anchor.kind for anchor in block_anchors] == ["block", "block"]
    assert [anchor.section_path for anchor in block_anchors] == ["root", "root"]
    assert [anchor.start_offset for anchor in block_anchors] == [0, 11]
    assert [anchor.end_offset for anchor in block_anchors] == [10, 33]
    assert len({anchor.anchor_id for anchor in block_anchors}) == len(block_anchors)
