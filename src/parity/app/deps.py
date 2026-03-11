"""Dependency wiring for the internal lifecycle app and worker."""

from __future__ import annotations

from functools import cache, lru_cache
from typing import Annotated

import sqlalchemy as sa
from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.engine import Engine

from parity.artifacts import FilesystemArtifactStore
from parity.chunking import ChunkingService
from parity.extractors import ExtractorRegistry, MarkdownExtractor, PdfExtractor
from parity.indexing import DeterministicEmbeddingAdapter, SqlVectorStore
from parity.lifecycle.orchestrator import DocumentLifecycleOrchestrator
from parity.lifecycle.readiness import ReadinessService
from parity.lifecycle.service import DocumentLifecycleService
from parity.lifecycle.worker import DocumentLifecycleWorker
from parity.normalizers import MarkdownNormalizer, NormalizerRegistry, PdfNormalizer
from parity.persistence import (
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentJobRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlLifecycleEventRepository,
    SqlSectionRepository,
)
from parity.query import QueryService
from parity.query.interpretation import DeterministicQueryInterpreter
from parity.query.persistence import SqlQueryRunStore, SqlQuerySnapshotStore, SqlQueryTraceStore
from parity.query.retrieval import SnapshotDenseQueryRetriever
from parity.readmodels import SqlQueryableCorpusReadModel
from parity.stages import (
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
from parity.structure import SectionDerivationService

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
        def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
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
    vector_store = SqlVectorStore(
        engine=engine,
        embedding_adapter=DeterministicEmbeddingAdapter(),
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
        embedding_adapter=DeterministicEmbeddingAdapter(),
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
    stage_runners = {
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
    """Build the internal query service for Stage 1 snapshot capture."""

    return QueryService(
        corpus_read_model=corpus_read_model,
        run_store=SqlQueryRunStore(engine),
        snapshot_store=SqlQuerySnapshotStore(engine),
        trace_store=SqlQueryTraceStore(engine),
        interpreter=DeterministicQueryInterpreter(),
        retriever=SnapshotDenseQueryRetriever(
            corpus_read_model=corpus_read_model,
            embedding_adapter=DeterministicEmbeddingAdapter(),
        ),
    )


def reset_runtime_caches() -> None:
    """Clear cached runtime singletons for tests."""

    get_settings.cache_clear()
    _build_engine.cache_clear()
    _build_artifact_store.cache_clear()
