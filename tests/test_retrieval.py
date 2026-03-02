import pytest

from docforge.retrieval import SemanticIndex


def test_search_returns_best_document_first() -> None:
    index = SemanticIndex(
        [
            "vector search with embeddings",
            "baking sourdough with rye flour",
            "retrieval augmented generation and semantic ranking",
        ]
    )

    results = index.search("semantic retrieval for rag", k=2)

    assert len(results) == 2
    assert "retrieval augmented generation" in results[0][0]
    assert results[0][1] >= results[1][1]


def test_search_rejects_invalid_k() -> None:
    index = SemanticIndex(["hello world"])

    with pytest.raises(ValueError) as exc:
        index.search("hello", k=0)

    assert "k must be greater than 0" in str(exc.value)
