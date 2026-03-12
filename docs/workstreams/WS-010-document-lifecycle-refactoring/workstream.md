---
artifact_kind: workstream
id: WS-010
title: document-lifecycle-refactoring
work_type: refactor
status: active
tags: [refactor, performance, scalability, ingestion]
---

# WS-010 Document Lifecycle Refactoring

- Status: active
- Owner: Unassigned
- Created: 2026-03-12
- Updated: 2026-03-12

## Problem
Currently, the document lifecycle operates as a synchronous staging pipeline inside the FastAPI application thread. Extracting, chunking, and embedding texts operate serially and map all chunks into an in-memory cosine similarity structure via a local `SqlVectorStore`. Furthermore, API routes require full file materialization in memory (`await file.read()`), which can fail on very large PDFs. While this architecture is acceptable for prototyping and testing the staging workflow, it lacks the elasticity, isolation, and scale required for a production-sized corpus spanning thousands of documents.

## Scope
This workstream aims to refactor the entire document ingestion path—from file submission down to the vector database—improving scalability, resilience, and configurability. The key architectural improvements include:

1. **Dedicated External Vector Database Support**: Replace the naive SQL/in-memory cosine similarity approach (`_cosine_similarity`) with proper integrations for scalable vector databases (e.g., Qdrant, Milvus, Pinecone) or PostgreSQL's native vector extension (`pgvector`).
2. **Asynchronous / Non-Blocking Worker Implementation**: Shift the `DocumentLifecycleWorker` execution from synchronous HTTP thread handling (via `/internal/run-next-job` or simple loops) to a dedicated asynchronous task queue (e.g., Celery, RQ) to prevent blocking the web server during heavy operations like PDF extraction or large model embedding.
3. **Batched Embedding Generation**: Refactor `publish_document` to chunk external API calls, implement configurable batch sizes, and add rate-limit handling and retry logic (using Tenacity) for the `INDEX` stage.
4. **Idempotency and Resiliency in Indexing**: Modify the indexer to support true transactional idempotency. External database integrations should use native upserts (based on `chunk_id`) so that partial failures can resume without dropping all prior embeddings for the document.
5. **Configurable Pipeline Strategies**: Allow custom extraction and chunking configurations (e.g., semantic vs. fixed-size) per workspace or per document by passing a configuration payload to the `POST /documents` endpoint.
6. **Streaming Intake for Large Files**: Refactor `POST /documents` to use streaming file uploads (`UploadFile.stream()`) to calculate the SHA-256 checksum and write the raw artifact to the `FilesystemArtifactStore` in a memory-efficient manner.
7. **Explicit "Upsert" Endpoint (Document Updates)**: Introduce an endpoint (`PUT /documents/{doc_id}`) to update documents in-place gracefully replacing the old entity, cleaning up old vector store records, and processing the pipeline without losing the conceptual document identity.
8. **Endpoint Documentation & OpenAPI Constraints**:
   - **Rich Examples**: Extend Pydantic models (like `UploadDocumentResult` and `DocumentStatusResult`) with complete `json_schema_extra` examples to render cleanly in Swagger UI/ReDoc.
   - **Strict Typing & Enums**: Use explicit Enums and strict parameter validation instead of broad primitives (e.g., locking down `source_type` and `answer_mode`).
   - **Explicit Error Contracts**: Guarantee all HTTP exceptions (400, 404, 409, 415, 500, 503) are explicitly declared in the `@app.post(responses=...)` dictionary, with consistent `ErrorResponse` schemas.
   - **API Grouping & Descriptions**: Apply FastAPI `tags` (e.g., `["Documents", "Queries", "Internal"]`) and expand endpoint descriptions to define state machine transitions, failure scenarios, and idempotency guarantees.

## Non-Goals
- Changing the public structure of the `RetrievalQueryResult` or document read API contracts unless necessary for these ingestion improvements.
- Implementing a completely new frontend or altering the final QA generation logic (Stage 7).
- Migrating existing legacy SQLite records to the new external vector database (migration paths are secondary to integration correctness).

## Plan
- [ ] Refactor the `/documents` FastAPI endpoints to support streaming and configurable processing.
- [ ] Update all API endpoints and Pydantic models with exhaustive OpenAPI `json_schema_extra` examples, explicit error mapping (`responses=...`), strict Enums, and logical `tags`.
- [ ] Introduce the asynchronous worker task queue (e.g., Celery) and update the orchestrator to enqueue jobs to the broker instead of the internal Postgres `DocumentJob` table if scaling demands.
- [ ] Evaluate and select the target external vector database (or `pgvector`).
- [ ] Refactor `SqlVectorStore` into a generic `VectorStore` interface with scalable backend implementations.
- [ ] Implement batched and rate-limited embedding generation in `IndexDocumentStage`.
- [ ] Update `publish_document` and lifecycle stages for idempotent retries and granular upserts.
- [ ] Write integration and performance tests for the new worker and vector store implementations.

## Related Notes
- Decisions: `decisions.md`
- Evidence: `evidence.md`
- Handoff: `handoff.md`
- ADRs: (TBD)
