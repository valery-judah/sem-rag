# Design: Source Connectors

## Frozen Contract
- **Inputs:** Source-specific configuration (credentials, spaces, filters) + Optional Incremental Cursor (timestamp or opaque state string).
- **Outputs:** An ordered stream of `tuple[RawDocument, Any]` objects (where `Any` is the incremental cursor).
- **Required fields for `RawDocument`:**
  - `doc_id` (string): Stable identifier.
  - `source` (string): Connector type identifier (e.g., `confluence`, `local`).
  - `source_ref` (string): The native reference in the source system (e.g., file path, Confluence page ID).
  - `url` (string): Absolute URL to the resource.
  - `content_stream` (Iterator[bytes]): Unprocessed content payload.
  - `content_type` (string): MIME type (e.g., `text/html`, `application/pdf`).
  - `metadata` (dict): Extracted metadata like `title`.
  - `acl_scope` (dict): Opaque access control scopes.
  - `timestamps` (dict): Extracted `created_at` and `updated_at` (ISO 8601 strings).
- **Invariants:**
  - Determinism: Repeated fetching of identical source materials yields an identical stream of `RawDocument` objects.
  - Identity Stability: `doc_id` is derived deterministically from the connector type (e.g., `local`) and the stable path (e.g., `hash(source + source_ref)`), instead of user-configured instance names.
- **ID Strategy:**
  - `doc_id = SHA256(f"{source}:{source_ref}").hexdigest()[:32]`
- **Config schema + defaults:**
  ```yaml
  sources:
    - type: string (required)
      name: string (optional, defaults to type)
      config: dict (connector-specific, required)
  ```

## Algorithm Overview
- **Step 1: Initialization**
  - The connector instantiates with credentials and target configuration.
  - Verifies connectivity.
- **Step 2: Enumeration & Filtering**
  - Connector lists all available items in the configured scope.
  - If `cursor` is provided, filters the list to include only items modified after the cursor state.
- **Step 3: Fetching**
  - Iterates over filtered items and downloads the raw payload.
  - Extracts metadata, URL, and ACLs natively.
- **Step 4: Mapping & Emitting**
  - Maps native representation to `RawDocument`.
  - Emits the document (and `DocFetched` event).
- **Step 5: Cursor Update**
  - The connector yields the new high-water mark cursor alongside each emitted document.

## Abstractions & Connector Interface
The connector module will provide an abstract base class `BaseSourceConnector`.
```python
from abc import ABC, abstractmethod
from typing import Iterator, Tuple, Optional, Any

class BaseSourceConnector(ABC):
    @abstractmethod
    def __init__(self, config: dict):
        pass

    @abstractmethod
    def fetch_documents(self, cursor: Optional[Any] = None) -> Iterator[Tuple['RawDocument', Any]]:
        """
        Yields a stream of tuples containing RawDocument objects and the next cursor state.
        """
        pass
```

## Edge-case Policy
- **Empty documents:** Yield a `RawDocument` with an empty stream for `content_stream`. The downstream parser will decide how to handle empty docs (likely filter them out).
- **Unknown content types:** Use `application/octet-stream`. The downstream parser may reject it if it lacks a supporting handler.
- **Missing timestamps:** Fall back to the current timestamp of ingestion (or `null` if the source absolutely cannot provide them).
- **API Pagination/Rate Limiting:**
  - The connector is responsible for safely paginating through large scopes.
  - Must retry internally on `429 Too Many Requests` using exponential backoff up to 3 times before raising a structured `RateLimitError`.

## Error Handling & Retries (Policies)
- **TransientSourceError:** Network timeouts, HTTP 502/503/504. Retry up to 3 times with exponential backoff.
- **RateLimitError:** HTTP 429. Respect `Retry-After` header if present; otherwise default to exponential backoff.
- **TerminalSourceError:** HTTP 401, 403, 404, or malformed data payload. Do NOT retry. Log the failure, emit a `PipelineError`, and skip the document (or fail the batch, depending on orchestrator configuration).
- **ConfigurationError:** Invalid credentials or invalid scope. Raised immediately during Step 1 (Initialization).