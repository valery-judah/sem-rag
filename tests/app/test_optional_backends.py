from __future__ import annotations

from doc_forge.app.deps import (
    get_document_lifecycle_service,
    get_query_service,
    get_queryable_corpus_read_model,
    reset_runtime_caches,
)
from doc_forge.artifacts import FilesystemArtifactStore


class _FakeSentenceEmbeddingAdapter:
    def __init__(self, *, model_name: str) -> None:
        self.model_name = model_name

    def embed_texts(self, texts):
        return [[0.0] for _ in texts]


class _FakeMlxGenerator:
    def __init__(
        self,
        *,
        model_name: str,
        max_new_tokens: int,
        temperature: float,
    ) -> None:
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

    def generate(self, **kwargs):  # pragma: no cover - runtime wiring test only
        raise AssertionError("generate should not be called in this test")


def test_runtime_services_use_sentence_transformers_when_configured(
    monkeypatch,
    sql_engine,
    db_url: str,
    tmp_path,
) -> None:
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("DOC_FORGE_EMBEDDING_BACKEND", "sentence-transformers")
    monkeypatch.setenv("DOC_FORGE_EMBEDDING_MODEL", "sentence-transformers/test-model")
    monkeypatch.setattr(
        "doc_forge.app.factories.SentenceTransformerEmbeddingAdapter",
        _FakeSentenceEmbeddingAdapter,
    )
    reset_runtime_caches()

    lifecycle_service = get_document_lifecycle_service(
        engine=sql_engine,
        artifact_store=FilesystemArtifactStore(tmp_path / "artifacts"),
    )
    query_service = get_query_service(
        engine=sql_engine,
        corpus_read_model=get_queryable_corpus_read_model(engine=sql_engine),
    )

    assert (
        lifecycle_service._vector_store._embedding_adapter.model_name  # type: ignore[attr-defined]
        == "sentence-transformers/test-model"
    )
    assert (
        query_service._retriever._embedding_adapter.model_name  # type: ignore[attr-defined]
        == "sentence-transformers/test-model"
    )

    reset_runtime_caches()


def test_query_service_uses_mlx_answer_generator_when_configured(
    monkeypatch,
    sql_engine,
    db_url: str,
) -> None:
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("DOC_FORGE_ANSWER_GENERATOR_BACKEND", "mlx")
    monkeypatch.setenv("DOC_FORGE_ANSWER_GENERATOR_MODEL", "mlx-community/test-model")
    monkeypatch.setenv("DOC_FORGE_ANSWER_GENERATOR_MAX_NEW_TOKENS", "64")
    monkeypatch.setenv("DOC_FORGE_ANSWER_GENERATOR_TEMPERATURE", "0.2")
    monkeypatch.setattr("doc_forge.app.factories.MlxGroundedAnswerGenerator", _FakeMlxGenerator)
    reset_runtime_caches()

    service = get_query_service(
        engine=sql_engine,
        corpus_read_model=get_queryable_corpus_read_model(engine=sql_engine),
    )

    assert service._answer_generator.model_name == "mlx-community/test-model"  # type: ignore[attr-defined]
    assert service._answer_generator.max_new_tokens == 64  # type: ignore[attr-defined]
    assert service._answer_generator.temperature == 0.2  # type: ignore[attr-defined]

    reset_runtime_caches()
