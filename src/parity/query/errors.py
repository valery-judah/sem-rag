"""Query-domain exceptions."""

from __future__ import annotations


class QueryError(Exception):
    """Base exception for internal query subsystem failures."""


class InvalidQueryRequestError(QueryError):
    """Raised when a query request cannot satisfy Stage 0 invariants."""


class CorpusBoundaryUnavailableError(QueryError):
    """Raised when the query corpus boundary cannot be resolved."""


class QueryStageContractViolationError(QueryError):
    """Raised when a stage input or output violates the internal contract."""


class UnsupportedPolicyOverrideError(QueryError):
    """Raised when a caller attempts an unsupported policy override."""


class QueryStageNotImplementedError(QueryError):
    """Raised for Stage 0 placeholder execution paths."""
