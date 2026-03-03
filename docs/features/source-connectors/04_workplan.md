# Workplan: Source Connectors

## Phase 0: Local File Connector

### PR1: Core Scaffolding, Models & Abstractions
- **Goal:** Set up the exact contract and basic types for the entire connector module. No actual remote fetching logic.
- [x] Define the `RawDocument` schema/dataclass in `src/docforge/connectors/models.py`.
- [x] Define the `BaseSourceConnector` abstract base class with `__init__` and `fetch_documents(cursor=None)` signatures.
- [x] Implement base structured exception classes (`ConfigurationError`, `TransientSourceError`, `TerminalSourceError`, `RateLimitError`).
- [x] **Tests:** Ensure `RawDocument` requires all mandatory fields and validates properly.
- [x] **Docs:** Validate these types align 100% with the "Frozen Contract" in `03_design.md`.

### PR2: Local File Connector
- **Goal:** Provide an immediate implementation for testing the downstream structural parser, focusing primarily on local file support without content parsing.
- [x] Create `LocalFileConnector` inheriting from `BaseSourceConnector`.
- [x] Support recursive directory scanning based on inclusion/exclusion path globs, reading raw bytes.
- [x] Extract native file `mtime`/`ctime` and map them to `updated_at`/`created_at`.
- [x] Map file extension to `content_type` using `mimetypes` or simple dictionary.
- [x] **Tests:** Unit test recursive listing, correctly inferring mimetypes, specifically verifying raw file reading, and deterministic `doc_id` generation (e.g., `hash(abs_path)`).
- [x] **Acceptance:** Full sync run over `input/` yields expected `RawDocument` objects with correct raw file content.

## Phase 1: Incremental Sync & External Connectors

### PR3: Incremental Sync Logic for Local File Connector
- **Goal:** Support basic incremental fetching using a cursor (`updated_at` high-water mark).
- [x] Add cursor acceptance to `LocalFileConnector`.
- [x] Filter `os.walk` results: only fetch files where `mtime` > `cursor`.
- [x] Return the maximum encountered `mtime` as the next cursor.
- [x] **Tests:** Execute sync, update a file's timestamp, execute again with cursor, assert only one file was fetched.

### PR4: Advanced External Connector (e.g., Confluence API)
- **Goal:** Implement the first true network-based connector.
- [ ] Implement `ConfluenceConnector`.
- [ ] Handle pagination natively in the API client to fetch all pages in a given space.
- [ ] Map Confluence API responses (Page ID, URL, Body Storage HTML, Labels, Space Permissions) into `RawDocument` structure.
- [ ] Handle `429 Too Many Requests` using the documented retry policy.
- [ ] **Tests:** Mock API responses for pagination and 429 retries. Ensure the yielded `doc_id` strictly matches the `hash("confluence:{page_id}")`.
- [ ] **Acceptance:** A test run against a mock confluence space yields the expected count of documents.

### PR5: Incremental Logic for External Connector
- **Goal:** Make the external connector cursor-aware.
- [ ] Update `ConfluenceConnector` to accept a timestamp string as a cursor.
- [ ] Append CQLExplicit query filters or use the appropriate endpoint parameter to filter pages by `lastModified > cursor`.
- [ ] **Tests:** Mock incremental API response, assert only changed documents are emitted and the correct new cursor is yielded.

### Definition of Done for Phase 1 Connectors
- [ ] All PRs merged.
- [ ] Connectors run end-to-end yielding compliant `RawDocument` instances.
- [ ] CI/CD gates validate schema compliance and `doc_id` determinism.
- [ ] Errors emit structured types and retry safely.
