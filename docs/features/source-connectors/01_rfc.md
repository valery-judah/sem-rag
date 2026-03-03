# RFC: Source Connectors

## Problem Statement
Enterprise knowledge required for a retrieval-augmented generation (RAG) system is typically siloed across diverse internal systems (e.g., wikis, version control, ticketing systems, databases, cloud drives). Each system provides differing APIs, authentication mechanisms, and data formats. We need a unified extraction abstraction—a **Source Connectors** layer—to fetch this content reliably, track changes incrementally, and yield a standardized `RawDocument` format for downstream processing in the Knowledge Representation Pipeline.

## Scope
### In Scope
- Define an abstraction for a Source Connector that can:
  - Enumerate documents from a designated source.
  - Fetch raw document content along with essential metadata (timestamps, ACL, source references).
  - Produce standardized `RawDocument` outputs, utilizing streams (e.g., `Iterator[bytes]`) for content to minimize memory overhead when processing large files.
- Support for **incremental fetching modes**: 
  - Utilizing change events (preferred).
  - Falling back to polling comparisons using `updated_at` or content hashes.
- Initial Phase 1 implementations will focus on a subset of 1-2 source types (e.g., a basic file/local connector and a simple external connector like Git or Confluence).
- Establishing a stable identity generation mechanism (`doc_id`) per document.

### Out of Scope (Non-goals)
- Runtime pipeline orchestration (e.g., Airflow DAG definitions, Kubernetes jobs).
- Deep caching or latency optimizations for connector network calls.
- Advanced retry policies and backoff mechanics across prolonged outages (handled at the orchestrator level).
- Complex, system-specific entity resolution or semantic mapping (done downstream in Structural Parser / Graph Extractor).
- A/B rollout mechanics for connector versions.

## Success Criteria
1. **Schema Compliance:** 100% of successfully fetched documents conform to the `RawDocument` schema.
2. **Stable Identity:** Re-ingesting an unchanged source document consistently yields the exact same `doc_id`.
3. **Incremental Fetching:** Providing a valid sync state/cursor significantly reduces fetch volume to only modified/new/deleted documents.
4. **Resilience:** The connector handles API pagination seamlessly without dropping records or exceeding rate limits catastrophically.
5. **Observability:** Connectors emit structured `DocFetched` and `PipelineError` events for monitoring.

## Incremental Fetch Strategy
To optimize extraction, connectors must avoid complete re-ingestion of the entire corpus. The design dictates two potential paths:
1. **Event-Driven (Preferred):** The connector listens to or consumes a stream of webhook events (e.g., "Page Updated", "Commit Pushed").
2. **Polling via Cursors:** The connector maintains a high-water mark (cursor), such as the maximum `updated_at` timestamp or sequence ID from the last successful sync. Subsequent runs request only entities modified after this cursor. 

The state management for cursors is external to the connector; the connector takes a cursor as input and returns a new cursor alongside the batch of `RawDocument` objects.

## Rollout Strategy
- **M1:** Implement the abstract base class and a `LocalFileConnector` to immediately unblock downstream parsing work.
- **M2:** Implement the first external connector (e.g., Confluence or Git).
- **M3:** Introduce and stabilize incremental state tracking via polling.
