"""Persistence package for compatibility SQLite helpers and lifecycle metadata storage."""

from .jobs import DocumentJob, DocumentJobStage, DocumentJobStatus
from .migrations import apply_migrations
from .models import PersistedDocument
from .repositories import (
    ChunkRepository,
    DocumentJobRepository,
    DocumentRepository,
    LifecycleEventRepository,
    SectionRepository,
    SqlChunkRepository,
    SqlDocumentJobRepository,
    SqlDocumentRepository,
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
    "DocumentJob",
    "ChunkRepository",
    "DocumentJobRepository",
    "DocumentJobStage",
    "DocumentJobStatus",
    "DocumentRepository",
    "LifecycleEventRepository",
    "PersistedDocument",
    "SectionRepository",
    "SqlChunkRepository",
    "SqlDocumentJobRepository",
    "SqlDocumentRepository",
    "SqlLifecycleEventRepository",
    "SqlSectionRepository",
    "apply_migrations",
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
