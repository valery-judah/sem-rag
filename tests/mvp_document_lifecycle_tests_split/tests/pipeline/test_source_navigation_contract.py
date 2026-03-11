from __future__ import annotations

import pytest


pytestmark = pytest.mark.pipeline


def test_retrieval_units_are_traceable_to_document_section_and_coarse_location(ready_document_bundle):
    chunk = ready_document_bundle["chunk"]
    assert getattr(chunk, "doc_id") == "doc_ready"
    assert list(getattr(chunk, "heading_path"))
    assert getattr(chunk, "section_id") or getattr(chunk, "page_start", None) is not None or getattr(chunk, "source_offset_start", None) is not None
