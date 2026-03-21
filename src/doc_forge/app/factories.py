"""Plain construction factories for runtime object graphs.

This module owns cached builder functions that are valid both inside and
outside FastAPI wiring.  It must not import FastAPI, ``Depends``, or
``Annotated``.
"""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from doc_forge.lifecycle.worker import DocumentLifecycleWorker

import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.engine import Engine

from doc_forge.artifacts import FilesystemArtifactStore
from doc_forge.indexing import (
    DeterministicEmbeddingAdapter,
    EmbeddingAdapter,
    SentenceTransformerEmbeddingAdapter,
)
from doc_forge.query.answer_generation import (
    DeterministicGroundedAnswerGenerator,
    GroundedAnswerGenerator,
    MlxGroundedAnswerGenerator,
    OllamaGroundedAnswerGenerator,
)


@cache
def build_engine(database_url: str) -> Engine:
    engine = sa.create_engine(database_url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _(dbapi_connection: Any, connection_record: Any) -> None:
            del connection_record
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    return engine


@cache
def build_artifact_store(root: str) -> FilesystemArtifactStore:
    return FilesystemArtifactStore(root)


@cache
def build_embedding_adapter(backend: str, model_name: str) -> EmbeddingAdapter:
    normalized = backend.strip().lower()
    if normalized == "deterministic":
        return DeterministicEmbeddingAdapter()
    if normalized in {"sentence-transformers", "sentence_transformers"}:
        return SentenceTransformerEmbeddingAdapter(model_name=model_name)
    raise RuntimeError(
        "DOC_FORGE_EMBEDDING_BACKEND must be one of: deterministic, sentence-transformers"
    )


@cache
def build_answer_generator(
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


def build_document_lifecycle_worker(
    engine: Engine,
    artifact_store: FilesystemArtifactStore,
    embedding_adapter: EmbeddingAdapter,
) -> DocumentLifecycleWorker:
    from doc_forge.chunking import ChunkingService
    from doc_forge.extractors import ExtractorRegistry, MarkdownExtractor, PdfExtractor
    from doc_forge.indexing import SqlVectorStore
    from doc_forge.lifecycle.orchestrator import DocumentLifecycleOrchestrator
    from doc_forge.lifecycle.readiness import ReadinessService
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
    from doc_forge.stages import (
        ChunkDocumentStage,
        ExtractDocumentJobStage,
        ExtractDocumentStage,
        IndexDocumentStage,
        NormalizeDocumentJobStage,
        NormalizeDocumentStage,
        ReadyDocumentStage,
        SectionizeDocumentStage,
    )
    from doc_forge.structure import SectionDerivationService

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
