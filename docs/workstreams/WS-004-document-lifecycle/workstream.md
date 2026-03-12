---
artifact_kind: workstream
id: WS-004
title: Document Lifecycle
work_type: feature
status: active
owner:
created: 2026-03-10
updated: 2026-03-11
---

# Summary
Implement the MVP document lifecycle so PDF and Markdown inputs become persisted, provenance-bearing, retrieval-ready corpus artifacts.

## Objective
Deliver the document-processing pipeline behind the existing internal lifecycle seam, ending in `READY` only when a document is actually indexed, traceable, and usable by later retrieval work.

## Non-goals
- Answer generation and the query lifecycle
- User-facing source inspection UI
- Public API stabilization
- OCR, scanned PDFs, and rich layout understanding
- Re-ingestion or document version-history workflows as MVP requirements

## Current status
- The repo already has tested internal lifecycle and corpus contract models for `Document`, `Section`, `Chunk`, and processing status transitions.
- The runtime ingestion pipeline behind those seams does not exist yet.
- Requirements, design exploration, and staged delivery docs now define scope, architecture direction, and PR sequencing for this workstream.

## Next step
- Execute `PR 1`: core domain and lifecycle contract enforcement.

## Relevant context
- paths:
- `docs/workstreams/WS-004-document-lifecycle/requirements.md`
- `docs/workstreams/WS-004-document-lifecycle/21-design-exploration.md`
- `docs/workstreams/WS-004-document-lifecycle/22-staged.md`
- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/delivery/workflow.md`
- `src/doc_forge/_contracts/models.py`
- `src/doc_forge/_contracts/lifecycle.py`
- `src/doc_forge/persistence.py`
- components:
- internal contract layer
- persistence layer
- new domain layer plus lifecycle runtime
- future ingestion and indexing pipeline
- constraints:
- keep MVP input scope limited to text-based PDF and Markdown
- do not describe ingestion/runtime capabilities as implemented until code exists
- preserve alignment with the locked internal lifecycle seam unless changed intentionally
- read first:
- `docs/workstreams/WS-004-document-lifecycle/requirements.md`
- `docs/workstreams/WS-004-document-lifecycle/21-design-exploration.md`
- `docs/workstreams/WS-004-document-lifecycle/22-staged.md`

## Workflow steps
1. Lock requirements and staged delivery boundaries.
2. Execute PR 1 for the new domain layer and lifecycle contract.
3. Continue through staged delivery from persistence to readiness with validation at each step.

## Validation
- Stage-aligned tests proving documents can progress through the lifecycle honestly
- Persistence coverage for document, section, and chunk linkage
- Failure-path coverage for unsupported or malformed inputs
- Retrieval smoke evidence before promoting `READY` semantics as implemented

## Linked artifacts
- `docs/workstreams/WS-004-document-lifecycle/requirements.md`
- `docs/workstreams/WS-004-document-lifecycle/21-design-exploration.md`
- `docs/workstreams/WS-004-document-lifecycle/22-staged.md`
- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/delivery/workflow.md`
