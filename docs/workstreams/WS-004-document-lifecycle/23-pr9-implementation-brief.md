---
artifact_kind: implementation_brief
id: WS-004-PR9
title: PR 9 Implementation Brief
status: implemented
created: 2026-03-11
updated: 2026-03-11
---

# PR 9 Implementation Brief: Embeddings, Vector Persistence, and `INDEXED` Semantics

## Summary
- Add internal indexing persistence with deterministic embeddings and document-scoped replace-on-publish behavior.
- Keep the implementation SQLite-compatible by storing embedding vectors in JSON.
- Promote documents to `INDEXED` only when active chunk publication is complete.

## Implementation Changes
- Add `src/parity/indexing/base.py`, `src/parity/indexing/embeddings.py`, and `src/parity/indexing/vector_store.py`.
- Add `index_entries` and `chunk_embeddings` persistence models, repositories, and Alembic migration `0003_indexing_tables.py`.
- Add `src/parity/stages/index.py`.

## Invariants
- Publication replaces prior embeddings and index entries for the document.
- One active `IndexEntry` exists per active chunk.
- The vector store supports document-scoped smoke queries without introducing a public retrieval API.

## Tests
- `tests/stages/test_index_stage.py`
- `tests/persistence/test_index_entry_repository.py`
- `tests/persistence/test_chunk_embedding_repository.py`

## Deferred
- Readiness predicate and operator-facing retrieval endpoint behavior.
