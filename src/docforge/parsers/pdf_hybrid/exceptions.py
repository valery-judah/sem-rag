"""
Exceptions for the PDF Hybrid Pipeline.
"""


class PdfHybridPipelineError(Exception):
    """Base exception for hybrid pipeline errors."""

    pass


class PdfHybridPipelineUnavailable(PdfHybridPipelineError):
    """Raised when require_any_engine=True and no engine binary is discoverable."""

    pass


class EngineTimeoutError(PdfHybridPipelineError):
    """Raised when an engine subprocess exceeds configured timeout."""

    pass


class EngineProcessError(PdfHybridPipelineError):
    """Raised when an engine subprocess exits non-zero or crashes."""

    pass


class AdapterParseError(PdfHybridPipelineError):
    """Raised when engine output JSON is malformed or schema-invalid."""

    pass
