"""Dependency wiring for the internal lifecycle app and worker."""

from __future__ import annotations

from functools import cache, lru_cache
from typing import Annotated, Any

import sqlalchemy as sa
from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.engine import Engine

from doc_forge.app.services.documents import DocumentsAppService
from doc_forge.app.services.internal import InternalAppService
from doc_forge.app.services.queries import QueriesAppService
from doc_forge.app.services.system import SystemAppService
from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.chunking import ChunkingService
from doc_forge.extractors import ExtractorRegistry, MarkdownExtractor, PdfExtractor
from doc_forge.indexing import (
    DeterministicEmbeddingAdapter,
    EmbeddingAdapter,
    SentenceTransformerEmbeddingAdapter,
    SqlVectorStore,
)
from doc_forge.lifecycle.orchestrator import DocumentLifecycleOrchestrator
from doc_forge.lifecycle.readiness import ReadinessService
from doc_forge.lifecycle.service import DocumentLifecycleService
from doc_forge.lifecycle.worker import DocumentLifecycleWorker, StageRunner
from doc_forge.normalizers import MarkdownNormalizer, NormalizerRegistry, PdfNormalizer
from doc_forge.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentJobRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlLifecycleEventRepository,
    SqlSectionRepository,
)
from doc_forge.persistence.jobs import DocumentJobStage
from doc_forge.query import QueryService
from doc_forge.query.answer_generation import (
    DeterministicGroundedAnswerGenerator,
    GroundedAnswerGenerator,
    MlxGroundedAnswerGenerator,
    OllamaGroundedAnswerGenerator,
)
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
from doc_forge.stages import (
    ChunkDocumentStage,
    ExtractDocumentJobStage,
    ExtractDocumentStage,
    IndexDocumentStage,
    NormalizeDocumentJobStage,
    NormalizeDocumentStage,
    ReadyDocumentStage,
    RegisterDocumentStage,
    SectionizeDocumentStage,
)
from doc_forge.structure import SectionDerivationService

from .logging import reset_logging
from .settings import AppSettings, load_settings


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Load and cache process-scoped runtime settings."""

    return load_settings()


@cache
def _build_engine(database_url: str) -> Engine:
    engine = sa.create_engine(database_url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _(dbapi_connection: Any, connection_record: Any) -> None:
            del connection_record
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    return engine


def get_engine(settings: Annotated[AppSettings, Depends(get_settings)]) -> Engine:
    """Return the shared SQLAlchemy engine for the configured database."""

    return _build_engine(settings.database_url)


@cache
def _build_artifact_store(root: str) -> FilesystemArtifactStore:
    return FilesystemArtifactStore(root)


def get_artifact_store(
    settings: Annotated[AppSettings, Depends(get_settings)],
) -> FilesystemArtifactStore:
    """Return the shared artifact store rooted under the configured path."""

    return _build_artifact_store(str(settings.artifact_root))


@cache
def _build_embedding_adapter(backend: str, model_name: str) -> EmbeddingAdapter:
    normalized = backend.strip().lower()
    if normalized == "deterministic":
        return DeterministicEmbeddingAdapter()
    if normalized in {"sentence-transformers", "sentence_transformers"}:
        return SentenceTransformerEmbeddingAdapter(model_name=model_name)
    raise RuntimeError(
        "DOC_FORGE_EMBEDDING_BACKEND must be one of: deterministic, sentence-transformers"
    )


def get_embedding_adapter() -> EmbeddingAdapter:
    """Build the configured embedding adapter while keeping deterministic as the default."""

    settings = get_settings()
    return _build_embedding_adapter(
        settings.embedding_backend,
        settings.embedding_model_name,
    )


def get_vector_store(
    engine: Annotated[Engine, Depends(get_engine)],
) -> SqlVectorStore:
    """Build the vector store instance for queries and health checks."""

    return SqlVectorStore(
        engine=engine,
        embedding_adapter=get_embedding_adapter(),
        index_entries=SqlIndexEntryRepository(engine),
        chunk_embeddings=SqlChunkEmbeddingRepository(engine),
    )


@cache
def _build_answer_generator(
    backend: str,
    model_name: str,
    max_new_tokens: int,
    temperature: float,
) -> GroundedAnswerGenerator:
    normalized = backend.strip().lower()
    if normalized == "deterministic":
        return DeterministicGroundedAnswerGenerator()
    if normalized == "mlx":
        return MlxGroundedAnswerGenerator(
            model_name=model_name,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
    if normalized == "ollama":
        return OllamaGroundedAnswerGenerator(
            model_name=model_name,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
    raise RuntimeError(
        "DOC_FORGE_ANSWER_GENERATOR_BACKEND must be one of: deterministic, mlx, ollama"
    )


def get_answer_generator() -> GroundedAnswerGenerator:
    """Build the configured Stage-7 answer generator with deterministic defaults."""

    settings = get_settings()
    return _build_answer_generator(
        settings.answer_generator_backend,
        settings.answer_generator_model_name,
        settings.answer_generator_max_new_tokens,
        settings.answer_generator_temperature,
    )


def get_document_lifecycle_service(
    engine: Annotated[Engine, Depends(get_engine)],
    artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
) -> DocumentLifecycleService:
    """Build the lifecycle service used by the internal app."""

    documents = SqlDocumentRepository(engine)
    jobs = SqlDocumentJobRepository(engine)
    lifecycle_events = SqlLifecycleEventRepository(engine)
    sections = SqlSectionRepository(engine)
    chunks = SqlChunkRepository(engine)
    index_entries = SqlIndexEntryRepository(engine)
    chunk_embeddings = SqlChunkEmbeddingRepository(engine)
    orchestrator = DocumentLifecycleOrchestrator(jobs=jobs)
    embedding_adapter = get_embedding_adapter()
    vector_store = SqlVectorStore(
        engine=engine,
        embedding_adapter=embedding_adapter,
        index_entries=index_entries,
        chunk_embeddings=chunk_embeddings,
    )
    register_stage = RegisterDocumentStage(
        engine=engine,
        documents=documents,
        lifecycle_events=lifecycle_events,
        artifact_store=artifact_store,
    )
    return DocumentLifecycleService(
        register_stage=register_stage,
        orchestrator=orchestrator,
        documents=documents,
        jobs=jobs,
        lifecycle_events=lifecycle_events,
        artifact_store=artifact_store,
        sections=sections,
        chunks=chunks,
        index_entries=index_entries,
        chunk_embeddings=chunk_embeddings,
        vector_store=vector_store,
    )


def get_document_lifecycle_worker(
    engine: Annotated[Engine, Depends(get_engine)],
    artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
) -> DocumentLifecycleWorker:
    """Build the internal lifecycle worker with the full stage registry."""

    documents = SqlDocumentRepository(engine)
    jobs = SqlDocumentJobRepository(engine)
    lifecycle_events = SqlLifecycleEventRepository(engine)
    sections = SqlSectionRepository(engine)
    chunks = SqlChunkRepository(engine)
    index_entries = SqlIndexEntryRepository(engine)
    chunk_embeddings = SqlChunkEmbeddingRepository(engine)
    orchestrator = DocumentLifecycleOrchestrator(jobs=jobs)
    embedding_adapter = get_embedding_adapter()

    extract_stage = ExtractDocumentStage(
        engine=engine,
        documents=documents,
        lifecycle_events=lifecycle_events,
        artifact_store=artifact_store,
        extractors=ExtractorRegistry(
            markdown=MarkdownExtractor(),
            pdf=PdfExtractor(),
        ),
    )
    normalize_stage = NormalizeDocumentStage(
        engine=engine,
        documents=documents,
        lifecycle_events=lifecycle_events,
        artifact_store=artifact_store,
        normalizers=NormalizerRegistry(
            markdown=MarkdownNormalizer(),
            pdf=PdfNormalizer(),
        ),
    )
    vector_store = SqlVectorStore(
        engine=engine,
        embedding_adapter=embedding_adapter,
        index_entries=index_entries,
        chunk_embeddings=chunk_embeddings,
    )
    readiness = ReadinessService(
        documents=documents,
        sections=sections,
        chunks=chunks,
        index_entries=index_entries,
        artifact_store=artifact_store,
        vector_store=vector_store,
    )
    stage_runners: dict[DocumentJobStage, StageRunner] = {
        ExtractDocumentJobStage.target_stage: ExtractDocumentJobStage(stage=extract_stage),
        NormalizeDocumentJobStage.target_stage: NormalizeDocumentJobStage(stage=normalize_stage),
        SectionizeDocumentStage.target_stage: SectionizeDocumentStage(
            documents=documents,
            sections=sections,
            artifact_store=artifact_store,
            service=SectionDerivationService(),
        ),
        ChunkDocumentStage.target_stage: ChunkDocumentStage(
            documents=documents,
            sections=sections,
            chunks=chunks,
            lifecycle_events=lifecycle_events,
            artifact_store=artifact_store,
            service=ChunkingService(),
        ),
        IndexDocumentStage.target_stage: IndexDocumentStage(
            documents=documents,
            chunks=chunks,
            lifecycle_events=lifecycle_events,
            vector_store=vector_store,
            index_entries=index_entries,
            chunk_embeddings=chunk_embeddings,
        ),
        ReadyDocumentStage.target_stage: ReadyDocumentStage(
            documents=documents,
            lifecycle_events=lifecycle_events,
            readiness=readiness,
        ),
    }
    return DocumentLifecycleWorker(
        jobs=jobs,
        documents=documents,
        lifecycle_events=lifecycle_events,
        orchestrator=orchestrator,
        stage_runners=stage_runners,
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
) -> QueryService:
    """Build the internal query service for end-to-end internal query execution."""

    embedding_adapter = get_embedding_adapter()
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
        answer_generator=get_answer_generator(),
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
    _build_engine.cache_clear()
    _build_artifact_store.cache_clear()
    _build_embedding_adapter.cache_clear()
    _build_answer_generator.cache_clear()
    reset_logging()
