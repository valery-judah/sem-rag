class ConnectorError(Exception):
    """Base class for source connector errors."""

    pass


class ConfigurationError(ConnectorError):
    """Raised for invalid credentials or invalid scope during Step 1 (Initialization)."""

    pass


class TransientSourceError(ConnectorError):
    """Raised for network timeouts, HTTP 502/503/504. Should be retried with exponential backoff."""

    pass


class TerminalSourceError(ConnectorError):
    """
    Raised for HTTP 401, 403, 404, or malformed data payload.
    Do NOT retry.
    """

    pass


class RateLimitError(ConnectorError):
    """
    Raised for HTTP 429. Respect `Retry-After` header if present;
    otherwise default to exponential backoff.
    """

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
