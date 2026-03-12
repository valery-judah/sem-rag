---
artifact_kind: implementation_brief
id: WS-004-PR7
title: PR 7 Implementation Brief
status: implemented
created: 2026-03-11
updated: 2026-03-11
---

# PR 7 Implementation Brief: Section Recovery and Section Persistence

## Summary
- Recover stable `Section` rows from normalized artifacts.
- Add a distinct internal `SECTIONIZE` job stage without changing lifecycle statuses.
- Use deterministic section replacement on retry.

## Implementation Changes
- Add `src/doc_forge/structure/sections.py` and `src/doc_forge/stages/sectionize.py`.
- Extend `DocumentJobStage` with `SECTIONIZE`.
- Use existing section repositories and normalized artifact storage.

## Invariants
- Every normalized document yields at least one section.
- Markdown sections reconstruct heading hierarchy under the document root.
- PDFs fall back to coarse synthetic sections when heading inference is weak.

## Tests
- `tests/stages/test_section_stage.py`
- Existing persistence replace-on-retry coverage continues to validate section ownership.

## Deferred
- Chunk production and `CHUNKED` transition.
