---
artifact_kind: implementation_brief
id: WS-004-PR6
title: PR 6 Implementation Brief
status: implemented
created: 2026-03-11
updated: 2026-03-11
---

# PR 6 Implementation Brief: Normalization and `NORMALIZED` Semantics

## Summary
- Normalize extracted Markdown and PDF content into a canonical inspectable representation.
- Extend normalized blocks with `heading_level` while keeping `_contracts` unchanged.
- Advance documents to `NORMALIZED` only after the normalized artifact is persisted.

## Implementation Changes
- Add `src/doc_forge/normalizers/base.py`, `src/doc_forge/normalizers/markdown.py`, and `src/doc_forge/normalizers/pdf.py`.
- Add normalized artifact delete support in `src/doc_forge/artifacts/store.py`.
- Add `src/doc_forge/stages/normalize.py` plus a worker-facing adapter.

## Invariants
- Markdown normalization preserves headings, list items, code blocks, and paragraphs.
- PDF normalization uses conservative heading inference and marks fallback requirements in metadata.
- Normalization failure leaves the document in `EXTRACTING` and cleans up any partial normalized artifact.

## Tests
- `tests/stages/test_normalize_stage_markdown.py`
- `tests/stages/test_normalize_stage_pdf.py`
- `tests/artifacts/test_normalized_artifact_store.py`

## Deferred
- Section and chunk production.
