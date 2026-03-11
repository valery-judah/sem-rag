---
artifact_kind: implementation_brief
id: WS-004-PR5
title: PR 5 Implementation Brief
status: implemented
created: 2026-03-11
updated: 2026-03-11
---

# PR 5 Implementation Brief: Extraction Paths for Markdown and PDF

## Summary
- Implement recoverable extraction for Markdown and text-PDF inputs.
- Persist extracted artifacts under deterministic document-scoped paths.
- Move documents into `EXTRACTING` only after the extracted artifact is durably written.

## Implementation Changes
- Add `src/parity/extractors/base.py`, `src/parity/extractors/markdown.py`, and `src/parity/extractors/pdf.py`.
- Extend extracted artifact schemas with block `kind` and source offsets.
- Add extracted artifact delete support in `src/parity/artifacts/store.py`.
- Add `src/parity/stages/extract.py` plus a worker-facing adapter.

## Invariants
- Markdown extraction preserves headings, paragraphs, and code fences with offsets.
- PDF extraction preserves page grouping, emits sparse-text warnings, and rejects empty text layers.
- Extraction failures do not advance document status or leave partial extracted artifacts behind.

## Tests
- `tests/stages/test_extract_stage_markdown.py`
- `tests/stages/test_extract_stage_pdf.py`
- `tests/artifacts/test_extracted_artifact_store.py`

## Deferred
- Normalized output and `NORMALIZED` transitions.
