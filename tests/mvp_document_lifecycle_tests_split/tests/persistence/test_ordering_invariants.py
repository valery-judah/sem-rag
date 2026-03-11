from __future__ import annotations

import pytest

from tests.helpers.builders import new_chunk, new_normalized_block, new_normalized_payload, new_section


pytestmark = pytest.mark.persistence


def test_sections_preserve_document_order(section_repo):
    section_repo.replace_for_document(
        "doc_1",
        [
            new_section(section_id="sec_1", doc_id="doc_1", ordinal=0, heading_text="A", heading_path=["A"]),
            new_section(section_id="sec_2", doc_id="doc_1", ordinal=1, heading_text="B", heading_path=["B"]),
        ],
    )
    ordinals = [getattr(section, "ordinal") for section in section_repo.list_for_document("doc_1")]
    assert ordinals == [0, 1]


def test_chunks_preserve_document_and_section_local_order(chunk_repo):
    chunk_repo.replace_for_document(
        "doc_1",
        [
            new_chunk(chunk_id="chk_1", doc_id="doc_1", section_id="sec_1", ordinal=0),
            new_chunk(chunk_id="chk_2", doc_id="doc_1", section_id="sec_1", ordinal=1),
        ],
    )
    ordinals = [getattr(chunk, "ordinal") for chunk in chunk_repo.list_for_document("doc_1")]
    assert ordinals == [0, 1]


def test_normalized_blocks_preserve_original_reading_order():
    payload = new_normalized_payload(
        blocks=[
            new_normalized_block(block_id="blk_1", kind="heading", text="Intro", order_index=0),
            new_normalized_block(block_id="blk_2", kind="paragraph", text="A", order_index=1),
            new_normalized_block(block_id="blk_3", kind="paragraph", text="B", order_index=2),
        ]
    )
    assert [getattr(block, "order_index") for block in getattr(payload, "blocks")] == [0, 1, 2]
