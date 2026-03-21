"""Dependency wiring for the internal lifecycle app and worker."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.engine import Engine

from doc_forge.app.services.documents import DocumentsAppService
from doc_forge.app.services.internal import InternalAppService
from doc_forge.app.services.queries import QueriesAppService
from doc_forge.app.services.system import SystemAppService
from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.indexing import (
    EmbeddingAdapter,
    SqlVectorStore,
)
from doc_forge.lifecycle.service import DocumentLifecycleService
from doc_forge.lifecycle.worker import DocumentLifecycleWorker
from doc_forge.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlSectionRepository,
)
from doc_forge.query import QueryService
from doc_forge.query.answer_generation import GroundedAnswerGenerator
from doc_forge.query.answer_mode_policy import DeterministicAnswerModePolicy
from doc_forge.query.context_assembly import DeterministicContextAssembler
from doc_forge.query.interpretation import DeterministicQueryInterpreter
from doc_forge.query.persistence import (
    SqlQueryAnswerStore,
    SqlQueryRunStore,
    SqlQuerySnapshotStore,
    SqlQueryTraceStore,
)
from doc_forge.query.replay import QueryReplayService
from doc_forge.query.retrieval import SnapshotDenseQueryRetriever
from doc_forge.query.review import QueryReviewService
from doc_forge.query.selection import DeterministicQuerySelector
from doc_forge.query.support_assessment import HybridSupportAssessor
from doc_forge.readmodels import SqlQueryableCorpusReadModel

from .factories import (
    build_answer_generator,
    build_artifact_store,
    build_document_lifecycle_service,
    build_document_lifecycle_worker,
    build_embedding_adapter,
    build_engine,
)
from .logging import reset_logging
from .settings import Settings, get_settings


def get_engine(settings: Annotated[Settings, Depends(get_settings)]) -> Engine:
    """Return the shared SQLAlchemy engine for the configured database."""

    return build_engine(settings.database_url)


def get_artifact_store(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FilesystemArtifactStore:
    """Return the shared artifact store rooted under the configured path."""

    return build_artifact_store(str(settings.artifact_root))


def get_embedding_adapter() -> EmbeddingAdapter:
    """Build the configured embedding adapter while keeping deterministic as the default."""

    settings = get_settings()
    return build_embedding_adapter(
        settings.embedding_backend,
        settings.embedding_model,
    )


def get_vector_store(
    engine: Annotated[Engine, Depends(get_engine)],
    embedding_adapter: Annotated[EmbeddingAdapter, Depends(get_embedding_adapter)],
) -> SqlVectorStore:
    """Build the vector store instance for queries and health checks."""

    return SqlVectorStore(
        engine=engine,
        embedding_adapter=embedding_adapter,
        index_entries=SqlIndexEntryRepository(engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(engine),
    )


def get_answer_generator() -> GroundedAnswerGenerator:
    """Build the configured Stage-7 answer generator with deterministic defaults."""

    settings = get_settings()
    return build_answer_generator(
        settings.answer_generator_backend,
        settings.answer_generator_model,
        settings.answer_generator_max_new_tokens,
        settings.answer_generator_temperature,
    )


def get_document_lifecycle_service(
    engine: Annotated[Engine, Depends(get_engine)],
    artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
    embedding_adapter: Annotated[EmbeddingAdapter, Depends(get_embedding_adapter)],
) -> DocumentLifecycleService:
    """Build the lifecycle service used by the internal app."""

    return build_document_lifecycle_service(
        engine=engine,
        artifact_store=artifact_store,
        embedding_adapter=embedding_adapter,
    )


def get_document_lifecycle_worker(
    engine: Annotated[Engine, Depends(get_engine)],
    artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
    embedding_adapter: Annotated[EmbeddingAdapter, Depends(get_embedding_adapter)],
) -> DocumentLifecycleWorker:
    """Build the internal lifecycle worker with the full stage registry."""

    return build_document_lifecycle_worker(
        engine=engine,
        artifact_store=artifact_store,
        embedding_adapter=embedding_adapter,
    )


def get_queryable_corpus_read_model(
    engine: Annotated[Engine, Depends(get_engine)],
) -> SqlQueryableCorpusReadModel:
    """Build the query-facing read model over lifecycle persistence."""

    return SqlQueryableCorpusReadModel(
        documents=SqlDocumentRepository(engine),
        sections=SqlSectionRepository(engine),
        chunks=SqlChunkRepository(engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(engine),
        index_entries=SqlIndexEntryRepository(engine),
    )


def get_query_service(
    engine: Annotated[Engine, Depends(get_engine)],
    corpus_read_model: Annotated[
        SqlQueryableCorpusReadModel,
        Depends(get_queryable_corpus_read_model),
    ],
    embedding_adapter: Annotated[EmbeddingAdapter, Depends(get_embedding_adapter)],
    answer_generator: Annotated[GroundedAnswerGenerator, Depends(get_answer_generator)],
) -> QueryService:
    """Build the internal query service for end-to-end internal query execution."""

    return QueryService(
        corpus_read_model=corpus_read_model,
        run_store=SqlQueryRunStore(engine),
        snapshot_store=SqlQuerySnapshotStore(engine),
        trace_store=SqlQueryTraceStore(engine),
        interpreter=DeterministicQueryInterpreter(),
        retriever=SnapshotDenseQueryRetriever(
            corpus_read_model=corpus_read_model,
            embedding_adapter=embedding_adapter,
        ),
        selector=DeterministicQuerySelector(corpus_read_model=corpus_read_model),
        context_assembler=DeterministicContextAssembler(),
        support_assessor=HybridSupportAssessor(),
        answer_mode_policy=DeterministicAnswerModePolicy(),
        answer_generator=answer_generator,
        answer_store=SqlQueryAnswerStore(engine),
    )


def get_query_review_service(
    engine: Annotated[Engine, Depends(get_engine)],
) -> QueryReviewService:
    """Build the read-only query review service."""

    return QueryReviewService(
        run_store=SqlQueryRunStore(engine),
        snapshot_store=SqlQuerySnapshotStore(engine),
        trace_store=SqlQueryTraceStore(engine),
        answer_store=SqlQueryAnswerStore(engine),
    )


def get_query_replay_service(
    engine: Annotated[Engine, Depends(get_engine)],
) -> QueryReplayService:
    """Build the internal query replay service."""

    return QueryReplayService(
        run_store=SqlQueryRunStore(engine),
        snapshot_store=SqlQuerySnapshotStore(engine),
        trace_store=SqlQueryTraceStore(engine),
        answer_store=SqlQueryAnswerStore(engine),
    )


def get_documents_app_service(
    lifecycle_service: Annotated[DocumentLifecycleService, Depends(get_document_lifecycle_service)],
) -> DocumentsAppService:
    """Build the document orchestration app service."""
    return DocumentsAppService(lifecycle_service=lifecycle_service)


def get_queries_app_service(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    review_service: Annotated[QueryReviewService, Depends(get_query_review_service)],
) -> QueriesAppService:
    """Build the queries app service."""
    return QueriesAppService(
        query_service=query_service,
        review_service=review_service,
    )


def get_system_app_service(
    engine: Annotated[Engine, Depends(get_engine)],
    artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
    vector_store: Annotated[SqlVectorStore, Depends(get_vector_store)],
) -> SystemAppService:
    """Build the system app service."""
    return SystemAppService(
        engine=engine,
        artifact_store=artifact_store,
        vector_store=vector_store,
    )


def get_internal_app_service(
    lifecycle_service: Annotated[
        DocumentLifecycleService,
        Depends(get_document_lifecycle_service),
    ],
    worker: Annotated[
        DocumentLifecycleWorker,
        Depends(get_document_lifecycle_worker),
    ],
) -> InternalAppService:
    """Build the internal app service."""
    from .services.internal import InternalAppService

    return InternalAppService(
        lifecycle_service=lifecycle_service,
        worker=worker,
    )


def reset_runtime_caches() -> None:
    """Clear cached runtime singletons for tests."""

    get_settings.cache_clear()
    build_engine.cache_clear()
    build_artifact_store.cache_clear()
    build_embedding_adapter.cache_clear()
    build_answer_generator.cache_clear()
    reset_logging()
