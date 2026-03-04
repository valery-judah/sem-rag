import json
from pathlib import Path

from docforge.parsers.models import BlockNode, HeadingNode, ParserBlockType, ParserConfig
from docforge.parsers.pdf_hybrid.distill import distill_pdf
from docforge.parsers.pdf_hybrid.schema import ExtractedPdfDocument


def load_fixture(name: str) -> ExtractedPdfDocument:
    p = Path("tests/parsers/pdf_hybrid/fixtures") / name
    with open(p) as f:
        data = json.load(f)
    return ExtractedPdfDocument.model_validate(data)


def test_distill_digital_born():
    extracted = load_fixture("digital_born.json")
    config = ParserConfig(parser_version="1.0.0")

    parsed = distill_pdf(extracted, config)

    # 1. Check canonical text
    # expected: "# First Heading\n\nThis is a paragraph under the heading."
    # plus "\n\n\f\n\n- Item 1\n- Item 2"
    assert (
        parsed.canonical_text
        == "# First Heading\n\nThis is a paragraph under the heading.\n\n\x0c\n\n- Item 1\n- Item 2"
    )

    # 2. Check structure tree
    root = parsed.structure_tree
    assert len(root.children) == 1
    h1 = root.children[0]
    assert isinstance(h1, HeadingNode)
    assert h1.level == 1
    assert h1.text == "First Heading"

    # Children of heading should be the paragraph and the list
    assert len(h1.children) == 2
    para = h1.children[0]
    assert isinstance(para, BlockNode)
    assert para.type == ParserBlockType.PARA

    lst = h1.children[1]
    assert isinstance(lst, BlockNode)
    assert lst.type == ParserBlockType.LIST

    # 3. Check ranges
    assert (
        parsed.canonical_text[para.range[0] : para.range[1]]
        == "This is a paragraph under the heading."
    )
    assert parsed.canonical_text[lst.range[0] : lst.range[1]] == "- Item 1\n- Item 2"

    # 4. Check metadata
    assert parsed.metadata["has_textual_content"] is True
    assert parsed.metadata["pdf_pipeline_version"] == "1.0"
    assert parsed.metadata["selected_engine_counts"] == {"marker": 2}


def test_distill_scan_heavy():
    extracted = load_fixture("scan_heavy.json")
    config = ParserConfig(parser_version="1.0.0")

    parsed = distill_pdf(extracted, config)

    assert "Some OCR text." in parsed.canonical_text
    assert "[UNPARSEABLE PAGE 1]" in parsed.canonical_text

    assert parsed.metadata["selected_engine_counts"] == {
        "mineru": 1
    }  # Page 2 selected engine is None

    root = parsed.structure_tree
    # No headings, just paras
    assert len(root.children) == 2
    for child in root.children:
        assert isinstance(child, BlockNode)
        assert child.type == ParserBlockType.PARA

    assert len(parsed.anchors.sections) == 1
    assert parsed.anchors.sections[0].section_path == "root"
    assert len(parsed.anchors.blocks) == 2
    assert {b.section_path for b in parsed.anchors.blocks} == {"root"}


def test_distill_mixed_layout():
    extracted = load_fixture("mixed_layout.json")
    config = ParserConfig(parser_version="1.0.0")

    parsed = distill_pdf(extracted, config)

    root = parsed.structure_tree
    assert len(root.children) == 2
    h2_1 = root.children[0]
    h2_2 = root.children[1]

    assert isinstance(h2_1, HeadingNode) and h2_1.level == 2
    assert isinstance(h2_2, HeadingNode) and h2_2.level == 2

    # Check deduplication logic
    assert h2_1.text == "Repeated Heading"
    assert h2_2.text == "Repeated Heading_0"

    assert len(h2_1.children) == 1
    assert h2_1.children[0].type == ParserBlockType.PARA

    assert len(h2_2.children) == 1
    assert h2_2.children[0].type == ParserBlockType.CODE

    # Section paths should be unique
    sections = parsed.anchors.sections
    assert len(sections) == 2
    assert sections[0].section_path == "Repeated Heading"
    assert sections[1].section_path == "Repeated Heading_0"


def test_distill_preserves_explicit_title():
    extracted = load_fixture("digital_born.json")
    config = ParserConfig(parser_version="1.0.0")

    parsed = distill_pdf(extracted, config, title="My Title")

    assert parsed.title == "My Title"


def test_distill_determinism():
    extracted1 = load_fixture("digital_born.json")
    extracted2 = load_fixture("digital_born.json")

    config = ParserConfig(parser_version="1.0.0")

    parsed1 = distill_pdf(extracted1, config)
    parsed2 = distill_pdf(extracted2, config)

    assert parsed1.model_dump() == parsed2.model_dump()
    assert parsed1.anchors.doc_anchor == parsed2.anchors.doc_anchor
