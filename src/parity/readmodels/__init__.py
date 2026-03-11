"""Read-only adapters that expose lifecycle data to the query subsystem."""

from .documents import QueryableCorpusReadModel, QueryableDocumentRecord

__all__ = ["QueryableCorpusReadModel", "QueryableDocumentRecord"]
