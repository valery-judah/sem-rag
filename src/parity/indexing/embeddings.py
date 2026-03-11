"""Deterministic local embedding adapter used by indexing tests and smoke paths."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from collections.abc import Sequence

from .base import EmbeddingAdapter

_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


class DeterministicEmbeddingAdapter(EmbeddingAdapter):
    """Generate stable normalized vectors from token hashes."""

    def __init__(self, *, dimensions: int = 32, model_name: str = "deterministic-hash-v1") -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than 0")
        self._dimensions = dimensions
        self.model_name = model_name

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        buckets: list[float] = [0.0] * self._dimensions
        counts = Counter(token.lower() for token in _TOKEN_PATTERN.findall(text))
        if not counts:
            return buckets

        for token, count in counts.items():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            buckets[bucket] += sign * float(count)

        norm = math.sqrt(sum(value * value for value in buckets))
        if norm == 0.0:
            return buckets
        return [value / norm for value in buckets]
