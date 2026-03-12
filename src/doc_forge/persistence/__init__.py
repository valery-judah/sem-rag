"""Persistence package for compatibility SQLite helpers and lifecycle metadata storage."""

from doc_forge.indexing import ChunkEmbedding, IndexEntry

from .jobs import DocumentJob, DocumentJobStage, DocumentJobStatus
from .migrations import apply_migrations, apply_migrations_with_lock
from .models import PersistedDocument
from .repositories import (
    ChunkEmbeddingRepository,
    ChunkRepository,
    DocumentJobRepository,
    DocumentRepository,
    IndexEntryRepository,
    LifecycleEventRepository,
    SectionRepository,
    SqlChunkEmbeddingRepository,
    SqlChunkRepository,
    SqlDocumentJobRepository,
    SqlDocumentRepository,
    SqlIndexEntryRepository,
    SqlLifecycleEventRepository,
    SqlSectionRepository,
)
from .sqlite_compat import (
    create_schema,
    list_chunks_by_document,
    list_documents_by_workspace,
    list_sections_by_document,
    replace_chunks_for_document,
    replace_sections_for_document,
    save_chunks,
    save_document,
    save_sections,
)

__all__ = [
    "ChunkEmbedding",
    "ChunkEmbeddingRepository",
    "DocumentJob",
    "ChunkRepository",
    "DocumentJobRepository",
    "DocumentJobStage",
    "DocumentJobStatus",
    "DocumentRepository",
    "IndexEntry",
    "IndexEntryRepository",
    "LifecycleEventRepository",
    "PersistedDocument",
    "SectionRepository",
    "SqlChunkEmbeddingRepository",
    "SqlChunkRepository",
    "SqlDocumentJobRepository",
    "SqlDocumentRepository",
    "SqlIndexEntryRepository",
    "SqlLifecycleEventRepository",
    "SqlSectionRepository",
    "apply_migrations",
    "apply_migrations_with_lock",
    "create_schema",
    "list_chunks_by_document",
    "list_documents_by_workspace",
    "list_sections_by_document",
    "replace_chunks_for_document",
    "replace_sections_for_document",
    "save_chunks",
    "save_document",
    "save_sections",
]
