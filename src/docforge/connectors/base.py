from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from docforge.connectors.models import RawDocument


class BaseSourceConnector(ABC):
    """
    Abstract base class for all source connectors.
    """

    @abstractmethod
    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize the connector with source-specific configuration.
        Should raise ConfigurationError if config is invalid or authentication fails.
        """
        pass

    @abstractmethod
    def fetch_documents(self, cursor: Any | None = None) -> Iterator[tuple[RawDocument, Any]]:
        """
        Yields a stream of (RawDocument, next_cursor) tuples for incremental sync.

        Args:
            cursor: An optional state token (timestamp or string) for incremental sync.

        Yields:
            Tuples of (RawDocument, cursor_state) where cursor_state represents the
            high-water mark up to that point.
        """
        pass
