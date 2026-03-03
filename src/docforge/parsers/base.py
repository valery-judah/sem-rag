from abc import ABC, abstractmethod

from docforge.connectors.models import RawDocument
from docforge.parsers.models import ParsedDocument, ParserConfig


class BaseParser(ABC):
    """Abstract base class for all structural parsers."""

    def __init__(self, config: ParserConfig) -> None:
        self.config = config

    @abstractmethod
    def parse(self, doc: RawDocument) -> ParsedDocument:
        """Parse a RawDocument into a ParsedDocument."""
        ...

    def _materialize_content(self, doc: RawDocument) -> bytes:
        """Drain content_stream into bytes. Must be called at most once per doc."""
        return b"".join(doc.content_stream)
