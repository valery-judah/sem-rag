"""Query-domain exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .contracts import QueryTerminalFailure

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


class QueryExecutionFailedError(QueryError):
    """Raised after a query run has been durably marked failed."""

    def __init__(
        self,
        *,
        query_id: str,
        terminal_failure: QueryTerminalFailure,
    ) -> None:
        super().__init__(terminal_failure.message)
        self.query_id = query_id
        self.terminal_failure = terminal_failure
