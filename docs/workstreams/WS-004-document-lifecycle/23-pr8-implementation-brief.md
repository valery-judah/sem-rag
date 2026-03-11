---
artifact_kind: implementation_brief
id: WS-004-PR8
title: PR 8 Implementation Brief
status: implemented
created: 2026-03-11
updated: 2026-03-11
---

# PR 8 Implementation Brief: Chunk Production and `CHUNKED` Semantics

## Summary
- Produce retrieval-addressable chunks from normalized artifacts plus recovered sections.
- Keep `_contracts.Chunk` stable and store token counts in debug metadata.
- Mark documents `CHUNKED` only after chunk replacement succeeds.

## Implementation Changes
- Add `src/parity/chunking/policy.py`, `src/parity/chunking/service.py`, and `src/parity/stages/chunk.py`.
- Preserve code blocks as standalone chunks when practical.
- Persist chunk lineage and token-count debug metadata.

## Invariants
- Every chunk belongs to one document and one persisted section.
- Chunk order is stable and heading-path context is preserved.
- Chunking is section-first and favors discourse boundaries over naive splitting.

## Tests
- `tests/stages/test_chunk_stage.py`
- Existing chunk repository and integrity tests remain green.

## Deferred
- Vector publication and readiness semantics.
