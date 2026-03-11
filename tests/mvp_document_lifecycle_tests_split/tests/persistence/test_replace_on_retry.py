from __future__ import annotations

import pytest

from tests.helpers.builders import new_chunk, new_index_entry, new_section


pytestmark = pytest.mark.persistence


def test_retry_replace_on_retry_behavior_does_not_duplicate_sections(section_repo):
    first = [new_section(section_id="sec_1", doc_id="doc_1"), new_section(section_id="sec_2", doc_id="doc_1")]
    second = [new_section(section_id="sec_3", doc_id="doc_1")]
    section_repo.replace_for_document("doc_1", first)
    section_repo.replace_for_document("doc_1", second)
    assert {getattr(section, "section_id") for section in section_repo.list_for_document("doc_1")} == {"sec_3"}


def test_retry_replace_on_retry_behavior_does_not_duplicate_chunks(chunk_repo):
    first = [new_chunk(chunk_id="chk_1", doc_id="doc_1", section_id="sec_1")]
    second = [new_chunk(chunk_id="chk_2", doc_id="doc_1", section_id="sec_2")]
    chunk_repo.replace_for_document("doc_1", first)
    chunk_repo.replace_for_document("doc_1", second)
    assert {getattr(chunk, "chunk_id") for chunk in chunk_repo.list_for_document("doc_1")} == {"chk_2"}


def test_retry_replace_on_retry_behavior_does_not_duplicate_index_entries(index_entry_repo):
    first = [new_index_entry(chunk_id="chk_1", doc_id="doc_1")]
    second = [new_index_entry(chunk_id="chk_2", doc_id="doc_1")]
    index_entry_repo.replace_for_document("doc_1", first)
    index_entry_repo.replace_for_document("doc_1", second)
    assert {getattr(entry, "chunk_id") for entry in index_entry_repo.list_for_document("doc_1")} == {"chk_2"}
