from __future__ import annotations

import pytest

from parity import SemanticIndex


def test_semantic_index_requires_non_empty_documents() -> None:
    with pytest.raises(ValueError, match="documents must not be empty"):
        SemanticIndex([])


def test_search_requires_positive_k() -> None:
    index = SemanticIndex(["alpha beta", "gamma delta"])

    with pytest.raises(ValueError, match="k must be greater than 0"):
        index.search("alpha", k=0)


def test_search_ranks_more_relevant_document_first() -> None:
    matching_doc = "semantic retrieval improves rag results"
    non_matching_doc = "gardening tools for spring soil"
    index = SemanticIndex([non_matching_doc, matching_doc])

    results = index.search("semantic retrieval rag", k=2)

    assert len(results) == 2
    assert results[0][0] == matching_doc
    assert results[0][1] > results[1][1]
