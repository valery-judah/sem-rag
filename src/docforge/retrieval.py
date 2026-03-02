"""Simple semantic retrieval index based on normalized bag-of-words vectors."""

from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


class SemanticIndex:
    """In-memory semantic-like retriever using cosine similarity over token counts."""

    def __init__(self, documents: list[str]) -> None:
        if not documents:
            raise ValueError("documents must not be empty")
        self._documents = documents
        self._vectors = [self._vectorize(doc) for doc in documents]

    @staticmethod
    def _vectorize(text: str) -> Counter[str]:
        tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
        return Counter(tokens)

    @staticmethod
    def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
        if not left or not right:
            return 0.0

        dot = sum(value * right.get(key, 0) for key, value in left.items())
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return dot / (left_norm * right_norm)

    def search(self, query: str, k: int = 3) -> list[tuple[str, float]]:
        if k <= 0:
            raise ValueError("k must be greater than 0")
        query_vector = self._vectorize(query)

        scored = [
            (doc, self._cosine_similarity(query_vector, doc_vector))
            for doc, doc_vector in zip(self._documents, self._vectors, strict=True)
        ]

        ranked = sorted(scored, key=lambda item: item[1], reverse=True)
        return ranked[:k]
