from typing import Any

import pytest
from pydantic import ValidationError

from docforge.parsers.models import (
    AnchorMap,
    BlockAnchor,
    BlockNode,
    DocNode,
    HeadingNode,
    ParsedDocument,
    ParserBlockType,
    ParserConfig,
    SectionAnchor,
)


def make_parsed_document(**overrides: Any) -> ParsedDocument:
    block = BlockNode(type=ParserBlockType.PARA, range=(0, 5))
    heading = HeadingNode(level=1, text="Intro")
    heading.children = [block]
    doc_node = DocNode(children=[heading])
    defaults: dict[str, Any] = {
        "doc_id": "doc-1",
        "title": "Test Doc",
        "canonical_text": "Intro hello",
        "structure_tree": doc_node,
        "anchors": AnchorMap(
            doc_anchor="da1",
            sections=[SectionAnchor(section_path="Intro", sec_anchor="sa1")],
            blocks=[
                BlockAnchor(
                    type=ParserBlockType.PARA,
                    section_path="Intro",
                    pass_anchor="pa1",
                    range=(0, 5),
                )
            ],
        ),
        "metadata": {"parser_version": "1.0.0"},
    }
    defaults.update(overrides)
    return ParsedDocument(**defaults)


def make_full_document() -> ParsedDocument:
    code_block = BlockNode(
        type=ParserBlockType.CODE,
        range=(12, 30),
        metadata={"language": "python"},
    )
    para_block = BlockNode(type=ParserBlockType.PARA, range=(0, 11))
    h2 = HeadingNode(level=2, text="Setup", children=[code_block])
    h1 = HeadingNode(level=1, text="My Project", children=[para_block, h2])
    doc_node = DocNode(children=[h1])
    return ParsedDocument(
        doc_id="doc-full",
        title="My Project",
        canonical_text="My Project\nSetup\nprint('hello')",
        structure_tree=doc_node,
        anchors=AnchorMap(
            doc_anchor="doc_hash",
            sections=[
                SectionAnchor(section_path="My Project", sec_anchor="sec_h1"),
                SectionAnchor(section_path="My Project>Setup", sec_anchor="sec_h2"),
            ],
            blocks=[
                BlockAnchor(
                    type=ParserBlockType.PARA,
                    section_path="My Project",
                    pass_anchor="pass_para",
                    range=(0, 11),
                ),
                BlockAnchor(
                    type=ParserBlockType.CODE,
                    section_path="My Project>Setup",
                    pass_anchor="pass_code",
                    range=(12, 30),
                ),
            ],
        ),
        metadata={"parser_version": "1.0.0"},
    )


def test_block_node_construction() -> None:
    node = BlockNode(type=ParserBlockType.PARA, range=(0, 10))
    assert node.type == ParserBlockType.PARA
    assert node.range == (0, 10)
    assert node.metadata == {}


def test_block_node_with_metadata() -> None:
    node = BlockNode(type=ParserBlockType.CODE, range=(5, 20), metadata={"language": "python"})
    assert node.type == ParserBlockType.CODE
    assert node.metadata == {"language": "python"}


@pytest.mark.parametrize("block_type", list(ParserBlockType))
def test_block_node_all_valid_types(block_type: ParserBlockType) -> None:
    node = BlockNode(type=block_type, range=(0, 1))
    assert node.type == block_type


@pytest.mark.parametrize("block_type", ["para", "unknown", ""])
def test_block_node_string_type_is_rejected_in_strict_mode(block_type: str) -> None:
    with pytest.raises(ValidationError):
        BlockNode(type=block_type, range=(0, 1))


@pytest.mark.parametrize("span", [(-1, 1), (5, 4)])
def test_block_node_invalid_range_raises(span: tuple[int, int]) -> None:
    with pytest.raises(ValidationError, match="BlockNode.range"):
        BlockNode(type=ParserBlockType.PARA, range=span)


def test_heading_node_construction() -> None:
    node = HeadingNode(level=2, text="Setup")
    assert node.type == "heading"
    assert node.level == 2
    assert node.text == "Setup"
    assert node.children == []


@pytest.mark.parametrize("level", [0, 7])
def test_heading_node_invalid_level_raises(level: int) -> None:
    with pytest.raises(ValidationError, match="HeadingNode.level"):
        HeadingNode(level=level, text="X")


def test_doc_node_defaults() -> None:
    node = DocNode()
    assert node.type == "doc"
    assert node.children == []


def test_section_anchor_construction() -> None:
    anchor = SectionAnchor(section_path="H1>H2", sec_anchor="abc123")
    assert anchor.section_path == "H1>H2"
    assert anchor.sec_anchor == "abc123"


def test_block_anchor_construction() -> None:
    anchor = BlockAnchor(
        type=ParserBlockType.CODE,
        section_path="H1>H2",
        pass_anchor="pass_abc",
        range=(10, 50),
    )
    assert anchor.type == ParserBlockType.CODE
    assert anchor.section_path == "H1>H2"
    assert anchor.pass_anchor == "pass_abc"
    assert anchor.range == (10, 50)


@pytest.mark.parametrize("span", [(-1, 1), (5, 4)])
def test_block_anchor_invalid_range_raises(span: tuple[int, int]) -> None:
    with pytest.raises(ValidationError, match="BlockAnchor.range"):
        BlockAnchor(
            type=ParserBlockType.PARA,
            section_path="H1",
            pass_anchor="p1",
            range=span,
        )


def test_anchor_map_construction() -> None:
    anchor_map = AnchorMap(
        doc_anchor="da",
        sections=[SectionAnchor(section_path="A", sec_anchor="sa")],
        blocks=[
            BlockAnchor(
                type=ParserBlockType.PARA,
                section_path="A",
                pass_anchor="pa",
                range=(0, 5),
            )
        ],
    )
    assert anchor_map.doc_anchor == "da"
    assert len(anchor_map.sections) == 1
    assert len(anchor_map.blocks) == 1


def test_parser_config_construction() -> None:
    cfg = ParserConfig(parser_version="1.0.0")
    assert cfg.parser_version == "1.0.0"
    assert cfg.blank_line_collapse == 2


def test_parser_config_empty_version_raises() -> None:
    with pytest.raises(ValidationError, match="parser_version"):
        ParserConfig(parser_version="")


def test_parsed_document_valid() -> None:
    doc = make_parsed_document()
    assert doc.doc_id == "doc-1"
    assert doc.title == "Test Doc"
    assert doc.canonical_text == "Intro hello"
    assert doc.metadata["parser_version"] == "1.0.0"


def test_parsed_document_empty_doc_id_raises() -> None:
    with pytest.raises(ValidationError, match="doc_id"):
        make_parsed_document(doc_id="")


def test_parsed_document_missing_parser_version_raises() -> None:
    with pytest.raises(ValidationError, match="parser_version"):
        make_parsed_document(metadata={})


def test_parsed_document_non_dict_metadata_raises() -> None:
    with pytest.raises(ValidationError, match="metadata"):
        make_parsed_document(metadata="not-a-dict")


def test_parsed_document_empty_canonical_text_allowed_for_non_textual_docs() -> None:
    doc = make_parsed_document(
        canonical_text="",
        structure_tree=DocNode(),
        anchors=AnchorMap(doc_anchor="da1", sections=[], blocks=[]),
        metadata={"parser_version": "1.0.0", "has_textual_content": False},
    )
    assert doc.canonical_text == ""


def test_parsed_document_empty_canonical_text_disallowed_for_textual_docs() -> None:
    with pytest.raises(ValidationError, match="canonical_text"):
        make_parsed_document(
            canonical_text="",
            metadata={"parser_version": "1.0.0", "has_textual_content": True},
        )


def test_parsed_document_block_anchor_range_must_be_in_bounds() -> None:
    bad_blocks = [
        BlockAnchor(
            type=ParserBlockType.PARA,
            section_path="Intro",
            pass_anchor="pa1",
            range=(0, 999),
        )
    ]
    anchors = AnchorMap(doc_anchor="da", sections=[], blocks=bad_blocks)
    with pytest.raises(ValidationError, match="block anchor range"):
        make_parsed_document(anchors=anchors)


def test_parsed_document_structure_tree_range_must_be_in_bounds() -> None:
    bad_block = BlockNode(type=ParserBlockType.PARA, range=(0, 999))
    heading = HeadingNode(level=1, text="Intro", children=[bad_block])
    doc_node = DocNode(children=[heading])
    with pytest.raises(ValidationError, match="structure_tree block range"):
        make_parsed_document(structure_tree=doc_node)


def test_parsed_document_has_required_rfc_fields() -> None:
    required = {"doc_id", "title", "canonical_text", "structure_tree", "anchors", "metadata"}
    assert required.issubset(ParsedDocument.model_fields)


def test_anchor_map_has_required_fields() -> None:
    assert {"doc_anchor", "sections", "blocks"}.issubset(AnchorMap.model_fields)


def test_section_anchor_has_required_fields() -> None:
    assert {"section_path", "sec_anchor"}.issubset(SectionAnchor.model_fields)


def test_block_anchor_uses_range_field() -> None:
    assert {"type", "section_path", "pass_anchor", "range"}.issubset(BlockAnchor.model_fields)


def test_serialized_block_anchor_uses_contract_range_key() -> None:
    original = make_full_document()
    block = original.model_dump(mode="json")["anchors"]["blocks"][0]
    assert "range" in block


def test_doc_node_type_default_is_doc() -> None:
    node = DocNode()
    assert node.type == "doc"


def test_heading_node_type_default_is_heading() -> None:
    node = HeadingNode(level=1, text="X")
    assert node.type == "heading"


def test_serialization_roundtrip_full_document() -> None:
    original = make_full_document()
    reconstructed = ParsedDocument.model_validate(original.model_dump(mode="python"))
    assert reconstructed == original


def test_serialization_roundtrip_is_idempotent() -> None:
    original = make_full_document()
    first = ParsedDocument.model_validate(original.model_dump(mode="python"))
    second = ParsedDocument.model_validate(first.model_dump(mode="python"))
    assert first == second


def test_json_dump_is_rfc_shape() -> None:
    original = make_full_document()
    dumped = original.model_dump(mode="json")
    assert isinstance(dumped["anchors"]["blocks"][0]["range"], list)
    assert dumped["anchors"]["blocks"][0]["type"] in {"para", "code", "list", "table"}


def test_serialization_preserves_ranges_as_tuple_after_validate() -> None:
    original = make_full_document()
    reconstructed = ParsedDocument.model_validate(original.model_dump(mode="python"))
    for blk in reconstructed.anchors.blocks:
        assert isinstance(blk.range, tuple)
        assert len(blk.range) == 2

    h1 = reconstructed.structure_tree.children[0]
    assert isinstance(h1, HeadingNode)
    h2 = h1.children[1]
    assert isinstance(h2, HeadingNode)
    code = h2.children[0]
    assert isinstance(code, BlockNode)
    assert isinstance(code.range, tuple)
    assert code.range == (12, 30)
