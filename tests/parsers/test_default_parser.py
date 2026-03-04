from typing import Any
from unittest.mock import patch

from docforge.connectors.models import RawDocument
from docforge.parsers.default import DeterministicParser
from docforge.parsers.models import ParserConfig


def _make_raw_doc(
    content: bytes, content_type: str, *, metadata: dict[str, Any] | None = None
) -> RawDocument:
    resolved_metadata = {"title": "My Title"} if metadata is None else metadata
    return RawDocument(
        doc_id="doc-1",
        source="local",
        source_ref="notes/file.md",
        url="file:///notes/file.md",
        content_stream=iter([content]),
        content_type=content_type,
        metadata=resolved_metadata,
        acl_scope={},
        timestamps={"created_at": "2023-01-01T00:00:00Z", "updated_at": "2023-01-01T00:00:00Z"},
    )


def test_parse_textual_doc_emits_non_empty_canonical_text() -> None:
    parser = DeterministicParser(ParserConfig(parser_version="1.0.0"))
    doc = _make_raw_doc(b"# Hello\n\nWorld", "text/markdown")

    parsed = parser.parse(doc)

    assert parsed.doc_id == "doc-1"
    assert parsed.title == "My Title"
    assert parsed.canonical_text
    assert parsed.metadata["has_textual_content"] is True
    assert parsed.metadata["parser_version"] == "1.0.0"
    assert parsed.metadata["content_type"] == "text/markdown"
    assert parsed.structure_tree.children != []
    assert len(parsed.structure_tree.children) == 1
    assert parsed.anchors.sections == []
    assert parsed.anchors.blocks == []


def test_parse_binary_doc_emits_empty_canonical_text() -> None:
    parser = DeterministicParser(ParserConfig(parser_version="1.0.0"))
    doc = _make_raw_doc(b"%PDF-1.7", "application/pdf")

    parsed = parser.parse(doc)

    assert parsed.canonical_text == ""
    assert parsed.metadata["has_textual_content"] is False
    assert parsed.metadata["detected_content_family"] == "unsupported"


@patch("docforge.parsers.default.run_pdf_pipeline")
@patch("docforge.parsers.default.distill_pdf")
def test_parse_routes_to_pdf_pipeline_when_enabled(mock_distill, mock_run) -> None:
    parser = DeterministicParser(
        ParserConfig(parser_version="1.0.0", enable_hybrid_pdf_pipeline=True)
    )
    doc = _make_raw_doc(b"%PDF-1.7", "application/pdf")

    mock_run.return_value = "fake_extracted_doc"
    mock_distill.return_value = "fake_parsed_doc"

    parsed = parser.parse(doc)

    assert parsed == "fake_parsed_doc"
    mock_run.assert_called_once_with(doc, parser.config)
    mock_distill.assert_called_once_with("fake_extracted_doc", parser.config, title="My Title")


@patch("docforge.parsers.default.run_pdf_pipeline")
@patch("docforge.parsers.default.distill_pdf")
def test_parse_pdf_pipeline_not_implemented_falls_back(mock_distill, mock_run) -> None:
    parser = DeterministicParser(
        ParserConfig(parser_version="1.0.0", enable_hybrid_pdf_pipeline=True)
    )
    doc = _make_raw_doc(b"%PDF-1.7", "application/pdf")

    mock_run.side_effect = NotImplementedError("stub")

    parsed = parser.parse(doc)

    assert parsed.canonical_text == ""
    assert parsed.metadata["has_textual_content"] is False
    assert parsed.metadata["detected_content_family"] == "unsupported"
    assert parsed.metadata["pdf_hybrid_pipeline_fallback"] is True
    mock_distill.assert_not_called()


def test_parse_falls_back_to_source_ref_for_missing_title() -> None:
    parser = DeterministicParser(ParserConfig(parser_version="1.0.0"))
    doc = _make_raw_doc(b"hello", "text/plain", metadata={})

    parsed = parser.parse(doc)

    assert parsed.title == "notes/file.md"


def test_parser_output_is_deterministic() -> None:
    parser = DeterministicParser(ParserConfig(parser_version="1.0.0"))
    doc_a = _make_raw_doc(b"alpha\r\n\r\nbeta", "text/plain")
    doc_b = _make_raw_doc(b"alpha\r\n\r\nbeta", "text/plain")

    parsed_a = parser.parse(doc_a)
    parsed_b = parser.parse(doc_b)

    assert parsed_a.model_dump(mode="python") == parsed_b.model_dump(mode="python")
