from __future__ import annotations

from doc_forge.indexing import SentenceTransformerEmbeddingAdapter


class _FakeSentenceTransformerModel:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def encode(
        self,
        sentences,
        *,
        normalize_embeddings: bool = True,
        convert_to_numpy: bool = True,
        show_progress_bar: bool = False,
    ) -> list[list[float]]:
        assert normalize_embeddings is True
        assert convert_to_numpy is True
        assert show_progress_bar is False
        self.calls.append(list(sentences))
        return [[0.5, -0.25], [1, 2]]


def test_sentence_transformer_embedding_adapter_uses_loader_and_coerces_float_vectors() -> None:
    fake_model = _FakeSentenceTransformerModel()
    seen_model_names: list[str] = []

    def _loader(model_name: str) -> _FakeSentenceTransformerModel:
        seen_model_names.append(model_name)
        return fake_model

    adapter = SentenceTransformerEmbeddingAdapter(
        model_name="sentence-transformers/test-model",
        loader=_loader,
    )

    vectors = adapter.embed_texts(["alpha", "beta"])

    assert seen_model_names == ["sentence-transformers/test-model"]
    assert fake_model.calls == [["alpha", "beta"]]
    assert vectors == [[0.5, -0.25], [1.0, 2.0]]
