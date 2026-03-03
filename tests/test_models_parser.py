from __future__ import annotations

from docforge.models import AnchorRef, ParsedDocument, Segment, StructureNode


def test_parsed_document_serialization_round_trip() -> None:
    doc_anchor = AnchorRef(anchor_id="doc:billing-guide", kind="doc")
    section_anchor = AnchorRef(
        anchor_id="section:billing-guide:root",
        kind="section",
        section_path="Billing",
    )
    passage_anchor = AnchorRef(
        anchor_id="passage:billing-guide:0-24",
        kind="passage",
        section_path="Billing",
        start_offset=0,
        end_offset=24,
    )
    structure = StructureNode(
        node_id="billing-guide:root",
        node_type="doc",
        title="Billing",
        anchor=doc_anchor,
        children=[
            StructureNode(
                node_id="billing-guide:p0",
                node_type="paragraph",
                text="Invoice retries happen daily.",
                anchor=passage_anchor,
            )
        ],
    )
    section = Segment(
        segment_id="seg:section:0",
        doc_id="billing-guide",
        type="SECTION",
        child_ids=["seg:passage:0"],
        section_path="Billing",
        anchor=section_anchor,
        text="Invoice retries happen daily.",
        token_count=4,
    )
    passage = Segment(
        segment_id="seg:passage:0",
        doc_id="billing-guide",
        type="PASSAGE",
        parent_id="seg:section:0",
        section_path="Billing",
        anchor=passage_anchor,
        text="Invoice retries happen daily.",
        token_count=4,
    )
    parsed = ParsedDocument(
        doc_id="billing-guide",
        title="Billing Guide",
        canonical_text="Invoice retries happen daily.",
        structure_tree=structure,
        doc_anchor=doc_anchor,
        section_anchors=[section_anchor],
        block_anchors=[passage_anchor],
        segments=[section, passage],
    )

    serialized = parsed.model_dump_json()
    restored = ParsedDocument.model_validate_json(serialized)

    assert restored.model_dump(mode="json") == parsed.model_dump(mode="json")
