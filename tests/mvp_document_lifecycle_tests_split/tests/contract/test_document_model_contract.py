from __future__ import annotations

import pytest

from tests.helpers.builders import new_chunk, new_document, new_section, processing_status


pytestmark = pytest.mark.contract


def test_document_has_stable_identity_and_source_type(document_factory):
    doc = document_factory(doc_id="doc_1", source_type="markdown", filename="a.md")
    assert getattr(doc, "doc_id") == "doc_1"
    assert getattr(doc, "filename") == "a.md"
    assert getattr(doc, "source_type")


def test_section_has_non_empty_heading_path(section_factory):
    section = section_factory(section_id="sec_1", heading_path=["Intro"], heading_text="Intro")
    assert list(getattr(section, "heading_path"))
    assert getattr(section, "heading_text")


def test_chunk_has_minimum_retrieval_metadata(chunk_factory):
    chunk = chunk_factory(
        chunk_id="chk_1",
        doc_id="doc_1",
        section_id="sec_1",
        heading_path=["Intro"],
        text="hello world",
        token_count=2,
    )
    assert getattr(chunk, "doc_id") == "doc_1"
    assert getattr(chunk, "section_id") == "sec_1"
    assert list(getattr(chunk, "heading_path"))
    assert getattr(chunk, "token_count") >= 1


def test_document_failure_fields_can_record_operator_usable_detail(document_factory):
    doc = document_factory(
        doc_id="doc_1",
        failure_code="EXTRACTION_FAILURE",
        failure_detail="malformed pdf",
        status=processing_status("FAILED"),
        ingest_status=processing_status("FAILED"),
    )
    assert getattr(doc, "failure_code") == "EXTRACTION_FAILURE"
    assert "malformed" in getattr(doc, "failure_detail")
