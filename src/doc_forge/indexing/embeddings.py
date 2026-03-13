"""Deterministic local embedding adapter used by indexing tests and smoke paths."""

from __future__ import annotations

import hashlib
import importlib
import math
import re
from collections import Counter
from collections.abc import Callable, Sequence
from typing import Any, Protocol, cast

import structlog

from doc_forge.app.logging import get_logger

from .base import EmbeddingAdapter

_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")

logger = get_logger(__name__)


class _SentenceTransformerModel(Protocol):
    def encode(
        self,
        sentences: Sequence[str],
        *,
        normalize_embeddings: bool = True,
        convert_to_numpy: bool = True,
        show_progress_bar: bool = False,
    ) -> object: ...


class DeterministicEmbeddingAdapter(EmbeddingAdapter):
    """Generate stable normalized vectors from token hashes."""

    def __init__(
        self,
        *,
        dimensions: int = 32,
        model_name: str = "deterministic-hash-v1",
        logger: structlog.stdlib.BoundLogger | None = None,
    ) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than 0")
        self._dimensions = dimensions
        self.model_name = model_name
        self._logger = logger or get_logger(self.__class__.__name__)

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


def require_sentence_transformers() -> None:
    """Assert that the optional sentence-transformers dependency group is installed."""

    try:
        importlib.import_module("sentence_transformers")
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "sentence-transformers is not installed. Run `uv sync --group llm` "
            "to enable model-backed embeddings."
        ) from exc


def _default_sentence_transformer_loader(model_name: str) -> _SentenceTransformerModel:
    require_sentence_transformers()
    sentence_transformers = importlib.import_module("sentence_transformers")
    sentence_transformer_cls = sentence_transformers.SentenceTransformer

    return cast(_SentenceTransformerModel, sentence_transformer_cls(model_name))


class SentenceTransformerEmbeddingAdapter(EmbeddingAdapter):
    """Generate dense embeddings with sentence-transformers when the optional group is installed."""

    def __init__(
        self,
        *,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        loader: Callable[[str], _SentenceTransformerModel] | None = None,
        logger: structlog.stdlib.BoundLogger | None = None,
    ) -> None:
        self.model_name = model_name
        self._model = (loader or _default_sentence_transformer_loader)(model_name)
        self._logger = logger or get_logger(self.__class__.__name__)

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        self._logger.info("embedding.model.generated", model_name=self.model_name, count=len(texts))
        encoded = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return _coerce_vector_rows(encoded)


def _coerce_vector_rows(encoded: object) -> list[list[float]]:
    rows_object = _to_python_rows(encoded)
    return [[_coerce_float(value) for value in row] for row in rows_object]


def _to_python_rows(value: object) -> list[list[object]]:
    if hasattr(value, "tolist"):
        value = cast(Any, value).tolist()
    rows = list(cast(Sequence[object], value))
    normalized: list[list[object]] = []
    for row in rows:
        if hasattr(row, "tolist"):
            row = cast(Any, row).tolist()
        normalized.append(list(cast(Sequence[object], row)))
    return normalized


def _coerce_float(value: object) -> float:
    return float(cast(float | int | str, value))
