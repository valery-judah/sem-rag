"""Read-only adapters that expose lifecycle data to the query subsystem."""

from .documents import (
    QueryableChunkRecord,
    QueryableCorpusReadModel,
    QueryableDocumentRecord,
    QueryableSectionRecord,
    SqlQueryableCorpusReadModel,
)

__all__ = [
    "QueryableChunkRecord",
    "QueryableCorpusReadModel",
    "QueryableDocumentRecord",
    "QueryableSectionRecord",
    "SqlQueryableCorpusReadModel",
]
