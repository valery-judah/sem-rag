# API Contracts

**Status:** Draft
**Last reviewed:** 2026-04-29

## Purpose

This document defines the draft external HTTP contract for the local `doc_forge` service.

The contract is being aligned with the MVP product promise in [`mvp.md`](./mvp.md): users upload supported documents into a bounded scope, ask corpus-scoped questions, receive grounded answers or honest abstentions, and inspect source evidence.

Because this document is draft, it is not yet a downstream compatibility guarantee. It records the intended public boundary and the current local route surface so implementation and product scope can converge before the contract is promoted to stable.

## Authority Boundaries

- [`mvp.md`](./mvp.md) owns product scope, supported inputs, trust guarantees, non-goals, and deferrals.
- [`functional-requirements.md`](./functional-requirements.md) owns the 12 minimal MVP functional requirements and acceptance criteria.
- [`architecture.md`](./architecture.md) owns current implementation truth and internal seams.
- This document owns the external HTTP contract once promoted from draft.

If this document implies broader product behavior than the MVP allows, the MVP wins. If this document describes a route that is implemented but not MVP-aligned, the route remains a local/runtime surface rather than a stable product contract.

## Draft Status

The localhost FastAPI service is real and callable, but the public API boundary is still being shaped.

Until this document is promoted out of draft:

- route paths, request fields, response fields, and status codes may change;
- current local routes should not be treated as long-term downstream-stable interfaces;
- OpenAPI visibility does not make a route part of the public product contract;
- internal Python modules under `src/doc_forge/` remain non-public;
- implementation changes that affect the intended public HTTP boundary should update this document in the same change.

## MVP Contract Principles

The eventual stable API should preserve these MVP-facing properties:

1. **Bounded scope is explicit.** Uploads and queries carry a user/workspace/corpus boundary, and queries never retrieve evidence outside that boundary.
2. **Supported inputs are clear.** Text-based PDFs and Markdown files are accepted; unsupported files are rejected or clearly flagged.
3. **Processing state is inspectable.** A caller can tell whether a document or corpus is processing, queryable, failed, or queryable with limitations.
4. **Provenance survives the workflow.** Documents, evidence units, retrieval results, answers, and citations retain source identity and source type.
5. **Answers are evidence-bound.** Query responses answer from retrieved corpus evidence, qualify uncertainty, state limitations, or abstain.
6. **Evidence is inspectable.** Source references resolve to real uploaded documents and recoverable source locations such as Markdown headings or PDF pages.
7. **Diagnostics support trust review.** Query runs expose enough trace or review data to debug unsupported answers, wrong abstentions, and false provenance without becoming production observability.

## Current Local HTTP Surface

The service is started with:

```bash
uv run poe run-api
```

Default local base URLs:

- `http://127.0.0.1:8000`
- `http://localhost:8000`

The following routes are currently implemented and are candidates for the public contract, subject to the draft caveats above.

### System

| Method | Path | Draft role |
|---|---|---|
| `GET` | `/healthz` | Process liveness check. |
| `GET` | `/readyz` | Runtime readiness check. |

### Documents

| Method | Path | Draft role |
|---|---|---|
| `POST` | `/documents` | Upload a supported PDF or Markdown document into a bounded workspace scope. |
| `GET` | `/documents/{doc_id}` | Read registered document metadata. |
| `GET` | `/documents/{doc_id}/status` | Read document processing status. |
| `GET` | `/documents/{doc_id}/artifacts` | Local artifact inspection; candidate diagnostic surface, not yet the MVP evidence-inspection contract. |
| `POST` | `/documents/{doc_id}/retry` | Retry a failed document lifecycle stage; operational surface, not required by MVP product scope. |
| `DELETE` | `/documents/{doc_id}` | Delete a document and its indexing data; implemented, but deletion/reindexing semantics are not part of the MVP promise. |

Draft upload request semantics:

```text
multipart/form-data
  workspace_id: non-empty bounded scope identifier
  file: text-based PDF or Markdown file
  title: optional display title
```

Draft upload response semantics:

```json
{
  "doc_id": "...",
  "ingest_status": "...",
  "source_type": "pdf | markdown",
  "filename": "...",
  "title": "...",
  "uploaded_at": "...",
  "checksum": "..."
}
```

Draft document status semantics:

```json
{
  "doc_id": "...",
  "ingest_status": "...",
  "source_type": "pdf | markdown",
  "title": "...",
  "filename": "...",
  "failure_code": null,
  "failure_detail": null
}
```

The implementation may use lifecycle-specific status names internally. The stable contract still needs a clear external mapping to the MVP status concepts: `processing`, `queryable`, `queryable_with_limitations`, and `failed`.

### Queries

| Method | Path | Draft role |
|---|---|---|
| `POST` | `/queries` | Ask a natural-language question against a bounded workspace scope. |
| `GET` | `/queries/{query_id}` | Read query-run summary and support outcome. |
| `GET` | `/queries/{query_id}/citations` | Inspect source references used by the answer. |
| `GET` | `/queries/{query_id}/trace` | Inspect query-stage trace for trust debugging. |

Draft query request semantics:

```json
{
  "workspace_id": "...",
  "question": "What does the corpus say about retry behavior?"
}
```

Current runtime payloads may also expose local diagnostic fields such as policy overrides. Those fields are not automatically part of the stable MVP contract.

Draft query response semantics:

```json
{
  "query_id": "...",
  "answer": {
    "answer_text": "...",
    "visible_limitations": []
  },
  "support_state": "sufficient | partial | insufficient",
  "answer_mode": "...",
  "citations": {
    "citations": [
      {
        "source_reference": {
          "doc_id": "...",
          "document_title": "...",
          "snippet": "...",
          "heading_path": ["..."],
          "page_label": null,
          "chunk_id": "..."
        },
        "support_role": "..."
      }
    ]
  },
  "message": "..."
}
```

The stable response shape may be flattened later. The stable semantics must preserve:

- answer text or explicit abstention/limitation;
- evidence support state or equivalent answer posture, with enough qualification to represent supported, partial, unsupported, out-of-scope, and ambiguous/conflicting outcomes;
- source references tied to evidence actually used;
- source type and recoverable source location;
- no fabricated documents, pages, headings, anchors, or source support.

## Runtime-Exposed But Non-Public Routes

The following routes are implemented for local smoke, testing, or operation, but they are not draft public product API:

| Method | Path | Role |
|---|---|---|
| `POST` | `/retrieval/query` | Document-scoped retrieval smoke/debug endpoint. |
| `POST` | `/internal/run-next-job` | Internal operator/test endpoint for one queued lifecycle job. |

These routes may change or disappear without public API migration.

## Optional Runtime Schema And Docs

When `DOC_FORGE_ENABLE_SWAGGER=true`, the runtime exposes:

- `GET /openapi.json`
- `GET /docs`

`DOC_FORGE_ENVIRONMENT=dev` alone does not enable these endpoints.

The live OpenAPI document describes the mounted runtime, which may include draft routes, diagnostic routes, and internal-only routes. It is useful for local inspection, but it is not itself the public product contract.

## Identifier Rules

Draft external identifiers should remain safe for use in paths, logs, and artifact references.

Current validation expectations:

- `workspace_id` values are non-empty, trimmed, and must not contain `/`, `\\`, `.`, or `..` path-segment forms.
- `doc_id` values are string-backed; generated values such as `doc_<hex>` remain valid.
- `query_id` path values follow the same non-empty, trimmed, no-separator, no-dot-segment validation rules as other stable identifiers.

The final stable contract should keep identifier validation explicit.

## Open Contract Decisions

Before this document can be promoted from draft, resolve:

1. Whether the product boundary is named `workspace`, `corpus`, or both.
2. The external status vocabulary and mapping from internal lifecycle states.
3. The external support-state vocabulary and mapping from current runtime states to MVP support outcomes.
4. Whether document retry, deletion, and artifact inspection are public API, local operator API, or internal-only.
5. Whether query responses should expose current nested DTOs or a flatter product-facing shape.
6. The minimum evidence-inspection response shape for Markdown, PDF, and mixed-source answers, including where source type appears.
7. The compatibility policy for future route and payload changes.

## Relationship To Other Docs

- [`mvp.md`](./mvp.md) defines the target product and trust contract.
- [`functional-requirements.md`](./functional-requirements.md) defines MVP acceptance criteria.
- [`architecture.md`](./architecture.md) describes current runtime implementation truth behind these routes.
- [`runbook.md`](./runbook.md) describes how to start and operate the local runtime.
- `docs/delivery/` and `docs/workstreams/` may describe delivery slices or future changes, but they do not override this contract.
