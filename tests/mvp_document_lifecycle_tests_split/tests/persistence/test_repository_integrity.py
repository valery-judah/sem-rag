from __future__ import annotations

import pytest

from tests.helpers.builders import new_chunk, new_document, new_index_entry, new_section


pytestmark = pytest.mark.persistence


def test_document_repository_round_trip(document_repo):
    doc = new_document(doc_id="doc_1")
    document_repo.create(doc)
    loaded = document_repo.get("doc_1")
    assert getattr(loaded, "doc_id") == "doc_1"
    assert getattr(loaded, "title") == "Test Document"


def test_section_repository_replace_for_document_is_destructive(section_repo):
    old = new_section(section_id="sec_old", doc_id="doc_1")
    new = new_section(section_id="sec_new", doc_id="doc_1")
    section_repo.replace_for_document("doc_1", [old])
    section_repo.replace_for_document("doc_1", [new])
    assert [getattr(section, "section_id") for section in section_repo.list_for_document("doc_1")] == ["sec_new"]


def test_chunk_repository_replace_for_document_is_destructive(chunk_repo):
    old = new_chunk(chunk_id="chk_old", doc_id="doc_1", section_id="sec_1")
    new = new_chunk(chunk_id="chk_new", doc_id="doc_1", section_id="sec_1")
    chunk_repo.replace_for_document("doc_1", [old])
    chunk_repo.replace_for_document("doc_1", [new])
    assert [getattr(chunk, "chunk_id") for chunk in chunk_repo.list_for_document("doc_1")] == ["chk_new"]


def test_index_entry_repository_replace_for_document_is_destructive(index_entry_repo):
    old = new_index_entry(chunk_id="old", doc_id="doc_1")
    new = new_index_entry(chunk_id="new", doc_id="doc_1")
    index_entry_repo.replace_for_document("doc_1", [old])
    index_entry_repo.replace_for_document("doc_1", [new])
    assert [getattr(entry, "chunk_id") for entry in index_entry_repo.list_for_document("doc_1")] == ["new"]


def test_chunk_linkage_integrity_requires_existing_section(section_repo, chunk_repo):
    section_repo.replace_for_document("doc_1", [new_section(section_id="sec_1", doc_id="doc_1")])
    chunk_repo.replace_for_document("doc_1", [new_chunk(chunk_id="chk_1", doc_id="doc_1", section_id="sec_1")])
    section_ids = {getattr(section, "section_id") for section in section_repo.list_for_document("doc_1")}
    for chunk in chunk_repo.list_for_document("doc_1"):
        assert getattr(chunk, "section_id") in section_ids
