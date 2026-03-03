# Domain Modeling Refactor Proposal: Source Connectors

Based on a comprehensive analysis of the code in `src/docforge/connectors/` and the documentation in `docs/source-connectors/`, several critical gaps and contradictions exist between the current implementation and the intended design/RFC. Below are the proposed refactors targeting the specific areas of concern.

## 1. The `RawDocument` Schema & Content Modification Invariants
**Gap / Contradiction:**
There is a direct contradiction regarding PDF handling. `docs/source-connectors/00_context.md` strictly states: *"No Content Modification: Source connectors fetch raw bytes. They DO NOT parse, canonicalize, or clean the content."* However, `docs/source-connectors/04_workplan.md` requested PDF text extraction, which the current `LocalFileConnector` implemented via `pypdf` in `src/docforge/connectors/local.py`. Performing extraction in the connector violates the boundary contract.

**Proposed Refactor:**
- **Remove PDF Parsing:** Delete `_extract_pdf_text` from `LocalFileConnector`. Treat `.pdf` files identically to other files by reading them via `f.read()` and passing the raw binary data to `content_bytes`. Let downstream parsers handle extraction.
- **Align Workplan:** Update `04_workplan.md` to remove the PDF text extraction requirements from Phase 0, reinforcing the strict boundary contract of the connector layer.
- **Address Memory Risk:** The `RawDocument` dataclass in `src/docforge/connectors/models.py` mandates `content_bytes: bytes`, forcing the entire file into memory (OOM risk). Consider amending the RFC to support `content_stream: Iterator[bytes] | BinaryIO` to allow downstream parsers to process large payloads in chunks.

## 2. Incremental Fetching Strategies (Cursors & Sync States)
**Gap:**
The `LocalFileConnector.fetch_documents` method completely ignores the `cursor` argument. It enumerates all files every time, bypassing the incremental sync requirement defined in `docs/source-connectors/02_user_stories.md` and statically returns `None` for the next cursor.

**Proposed Refactor:**
- **Implement `mtime` Filtering:** Update `LocalFileConnector._generator()` to compare each file's modification time (`stat.st_mtime`) against the provided `cursor`. Only yield files modified on or after the cursor.
- **Compute Next Cursor:** Track the maximum `mtime` observed during the traversal to represent the high-water mark, which will be returned as the `next_cursor`.

## 3. Interface Abstractions & Stream Safety
**Gap:**
The `BaseSourceConnector.fetch_documents` signature (`-> tuple[Iterator[RawDocument], Any]`) in `src/docforge/connectors/base.py` is unsafe. By returning a tuple of `(Iterator, next_cursor)`, the interface forces calculating the speculative `next_cursor` *before* processing the document stream. If the orchestrator commits this cursor and the stream fails midway, subsequent runs will skip unprocessed documents. Additionally, raising `TerminalSourceError` inside the generator (as done in `LocalFileConnector`) completely aborts the iteration for a single unreadable file, conflicting with the "skip the document" edge-case policy.

**Proposed Refactor:**
- **Redesign the Fetch Interface:** Change `fetch_documents` to tightly couple cursor progression with document yields.
  - *Option A:* `-> Iterator[tuple[RawDocument, Any]]`. Yields provide the document alongside the cursor state reflecting that exact point in the sync.
  - *Option B:* `-> Iterator[RawDocument | CursorUpdateEvent | DocumentErrorEvent]`. Yield documents, periodically yield safe high-water mark cursor events, and yield explicit error events.
- **Yield Errors Instead of Raising:** Support yielding error records instead of raising exceptions so the orchestrator can log the `PipelineError` event and continue processing remaining files.

## 4. Stable Identity Generation (`doc_id`)
**Gap:**
`LocalFileConnector` generates the `doc_id` hash using `self.source_name`, which is populated by the mutable configuration value `config.get("name", "local")`. If a pipeline operator renames the connector instance in their config file, the `doc_id` for every file changes. This violates the Stable Identity Invariant, triggering a full re-ingestion and massive duplication in downstream indexes.

**Proposed Refactor:**
- **Use Immutable Type for Identity:** Decouple `doc_id` generation from the user-defined instance name. The ID hash must strictly use the connector type and the source reference (e.g., `doc_id_input = f"local:{source_ref}".encode()`).
- **Preserve Lineage Metadata:** The user-configured `name` can still be attached to the `RawDocument.metadata` dictionary for lineage tracking, but excluded from the deterministic ID generation algorithm.