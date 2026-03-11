from __future__ import annotations

import pytest

from tests.helpers.builders import new_chunk, new_document, new_index_entry, new_section


pytestmark = pytest.mark.persistence


def test_every_section_references_exactly_one_document(section_repo):
    section_repo.replace_for_document("doc_1", [
        new_section(section_id="sec_1", doc_id="doc_1"),
        new_section(section_id="sec_2", doc_id="doc_1"),
    ])
    for section in section_repo.list_for_document("doc_1"):
        assert getattr(section, "doc_id") == "doc_1"


def test_every_chunk_references_exactly_one_document_and_one_section(section_repo, chunk_repo):
    section_repo.replace_for_document("doc_1", [new_section(section_id="sec_1", doc_id="doc_1")])
    chunk_repo.replace_for_document("doc_1", [new_chunk(chunk_id="chk_1", doc_id="doc_1", section_id="sec_1")])
    section_ids = {getattr(section, "section_id") for section in section_repo.list_for_document("doc_1")}
    for chunk in chunk_repo.list_for_document("doc_1"):
        assert getattr(chunk, "doc_id") == "doc_1"
        assert getattr(chunk, "section_id") in section_ids


def test_index_entries_match_active_chunk_set(chunk_repo, index_entry_repo):
    chunk_repo.replace_for_document("doc_1", [
        new_chunk(chunk_id="chk_1", doc_id="doc_1", section_id="sec_1"),
        new_chunk(chunk_id="chk_2", doc_id="doc_1", section_id="sec_1"),
    ])
    index_entry_repo.replace_for_document("doc_1", [
        new_index_entry(chunk_id="chk_1", doc_id="doc_1"),
        new_index_entry(chunk_id="chk_2", doc_id="doc_1"),
    ])
    chunk_ids = {getattr(chunk, "chunk_id") for chunk in chunk_repo.list_for_document("doc_1")}
    index_ids = {getattr(entry, "chunk_id") for entry in index_entry_repo.list_for_document("doc_1")}
    assert index_ids == chunk_ids
