# User Stories & Acceptance Criteria: Source Connectors

## 1. Developer Configures a New Source Connector
**Story:** As a pipeline operator, I want to configure a source connector (e.g., Confluence, Git, Local File) so that it can fetch documents matching my inclusion/exclusion rules.

**Acceptance Criteria (Testable Checks):**
- [ ] Connector initialization accepts a valid configuration object dictating the target (e.g., Space ID, Repository URL, Directory path).
- [ ] Invalid configurations raise a structured `ConfigurationError` upon initialization.
- [ ] Connectors successfully authenticate using provided credentials (or error explicitly if authentication fails).

## 2. Full Ingestion Yields Valid RawDocuments
**Story:** As the ingestion engine, I need the connector to yield all documents in the target scope as `RawDocument` objects so the downstream parser can process them.

**Acceptance Criteria (Testable Checks):**
- [ ] The connector enumerates all target documents without silently dropping items during pagination.
- [ ] The output of the connector is a stream/list of strictly valid `RawDocument` dicts/objects.
- [ ] The `doc_id` field in every `RawDocument` is populated using a deterministic hashing/mapping function based on the source identity.
- [ ] Output includes valid `content_stream`, an accurate `content_type`, and base metadata (e.g., `title`, timestamps, ACLs).
- [ ] A `DocFetched` event is emitted for each yielded document.

## 3. Incremental Fetching Respects the Cursor
**Story:** As a system optimizing for cost and speed, I want the connector to accept a sync state (cursor) and only fetch documents that have changed since that cursor.

**Acceptance Criteria (Testable Checks):**
- [ ] The connector method accepts an optional `cursor` parameter (e.g., a timestamp or opaque string).
- [ ] When a cursor is provided, the connector only yields documents modified on or after the cursor state.
- [ ] The connector yields tuples of `(RawDocument, cursor_state)` incrementally, rather than returning a single updated `cursor` at the end of an extraction run.
- [ ] A run with no changed documents yields zero `RawDocument` objects and retains the existing cursor.

## 4. Resilient Error Handling & Retries
**Story:** As an operator, I want the connector to handle temporary network failures gracefully so the entire pipeline job doesn't fail due to an intermittent 503 error.

**Acceptance Criteria (Testable Checks):**
- [ ] Source API rate limits (e.g., HTTP 429) trigger a backoff and retry (or yield an explicit structured `RateLimitError` for the orchestrator to handle).
- [ ] Network timeouts yield a structured `TransientSourceError`.
- [ ] Unrecoverable errors (e.g., HTTP 401 Unauthorized, HTTP 404 Not Found) yield a `TerminalSourceError` and emit a `PipelineError(stage="connect", doc_id="...", error_class="...")` event.

## Quality Gates
- **Schema Validation:** 100% of yielded outputs pass `RawDocument` strict schema validation in CI tests.
- **Determinism Check:** Fetching the exact same source twice without changes produces identical `doc_id`s and metadata fields.
- **Coverage:** Unit tests cover initialization, full sync, incremental sync (cursor logic), and error paths (mocked API failures).