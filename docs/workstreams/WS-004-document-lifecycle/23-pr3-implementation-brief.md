---
artifact_kind: implementation_brief
id: WS-004-PR3
title: PR 3 Implementation Brief
status: draft
created: 2026-03-11
updated: 2026-03-11
---

# PR 3 Implementation Brief: Internal Intake and Registration Stage

## Summary
- Make PR 3 the first real runtime slice of the document lifecycle: a supported PDF or Markdown upload becomes a durable `Document` in `REGISTERED`.
- Add a thin internal HTTP intake route backed by a transport-independent lifecycle service and a dedicated registration stage.
- Persist the raw artifact, checksum, durable document metadata, and initial lifecycle event, while explicitly deferring job orchestration and downstream stage execution.

## Implementation Changes
- Add `src/parity/app/api.py` with a FastAPI app exposing only `POST /documents` for PR 3.
- Add `src/parity/app/deps.py` and `src/parity/app/settings.py` for internal runtime wiring:
  - database URL from the existing `DATABASE_URL`
  - artifact root from a new internal setting such as `PARITY_ARTIFACT_ROOT`
- Add `src/parity/lifecycle/service.py` with `DocumentLifecycleService.upload_document(...)` as the transport-thin coordination seam for intake and registration.
- Add `src/parity/stages/register.py` for the registration-stage logic that turns an accepted upload into a durable `REGISTERED` document.
- Use the existing `FilesystemArtifactStore` to persist the raw upload under the deterministic doc-scoped path already introduced in PR 2.
- Reuse the existing `documents` table fields added in PR 2:
  - `checksum`
  - `raw_storage_path`
  - `ingest_status`
  - `storage_ref`
- Reuse the existing `lifecycle_events` table for the initial `REGISTER` event.
- Update `pyproject.toml` and `uv.lock` to add the internal HTTP/runtime dependencies needed for upload handling:
  - `fastapi`
  - `uvicorn`
  - `python-multipart`
  - `httpx` in dev dependencies for API tests

## Intake And Registration Design Decisions
- Treat the new HTTP route as an internal implementation seam, not a stable public API contract. Do not update `docs/evergreen/api-contracts.md` in PR 3.
- Generate `doc_id` at intake before raw artifact persistence. This `doc_id` is the PR 3 idempotency anchor for the upload context.
- Keep registration idempotency scoped to the same intake context, not checksum-level deduplication across separate uploads.
- Use a transport-thin service layer so later CLI, worker, or test entrypoints can reuse the same registration logic without embedding lifecycle behavior in FastAPI handlers.
- Stop PR 3 at durable registration. Do not create `document_jobs` rows yet and do not introduce worker dispatch or retry execution in this PR.
- Validate source type from both filename and file content cues rather than trusting upload metadata alone.
- Keep upload handling simple for MVP:
  - buffer the file once in memory
  - compute `sha256`
  - persist raw bytes
  - defer streaming optimization, file-size caps, and timeout enforcement to later hardening work

## Route Scope
- Add only `POST /documents` in PR 3.
- Accept `multipart/form-data` with:
  - required `workspace_id`
  - optional `title`
  - required `file`
- Return `201 Created` on success with an internal response payload containing:
  - `doc_id`
  - `ingest_status`
  - `source_type`
  - `filename`
  - `title`
  - `uploaded_at`
  - `checksum`
- Do not add `GET /documents/{doc_id}`, status, artifacts, retry, or health routes in PR 3. Those belong to later runtime slices.

## Validation Rules
- Supported inputs remain locked to MVP scope:
  - text-based PDF
  - Markdown
- PDF validation should require:
  - filename extension `.pdf`
  - recognizable PDF header bytes such as `%PDF-`
- Markdown validation should require:
  - filename extension `.md` or `.markdown`
  - UTF-8-decodable text payload
- Unsupported or mismatched uploads must fail explicitly with a `415` response.
- If `title` is omitted, derive it from the filename stem.

## Registration Stage Responsibilities
- Validate the intended lifecycle transition `UPLOADED -> REGISTERED`.
- Persist the raw artifact through `FilesystemArtifactStore.write_raw(...)`.
- Build a durable document row with:
  - stable `doc_id`
  - workspace boundary
  - source type
  - title
  - filename
  - upload timestamp
  - `REGISTERED` status
  - `storage_ref` pointing to the managed raw artifact path
  - `checksum`
  - `raw_storage_path`
- Append a single lifecycle event for stage `REGISTER` with:
  - `from_status=UPLOADED`
  - `to_status=REGISTERED`
- Leave extraction, downstream status changes, and queue handoff for PR 4.

## Atomicity And Failure Behavior
- Make document creation plus lifecycle-event append atomic at the SQL layer.
- Unsupported input failures should happen before any `documents` row or lifecycle event is created.
- If raw artifact persistence succeeds but registration fails at the database layer, perform best-effort cleanup of the just-written raw file and return an internal error.
- If registration is retried for the same `doc_id` and the existing stored document matches the same upload context, treat it as idempotent success and do not append a duplicate lifecycle event.
- Do not mark any document `FAILED` in PR 3 for unsupported uploads that never reached durable registration. `FAILED` remains a document-scoped lifecycle state, and unsupported inputs rejected before registration do not yet have a durable document identity.

## Public And Internal Boundaries
- This PR does not create a stable public HTTP, CLI, or package API contract.
- The new FastAPI route is an internal runtime/admin seam only.
- The `_contracts.Document` shape should remain unchanged in PR 3.
- Do not broaden PR 3 into extraction, normalization, retries, worker loops, or readiness behavior.
- Do not add new persistence for sections, chunks, index entries, or source-inspection payloads.

## Tests
- Add `tests/app/test_documents_api.py` for route-level coverage:
  - PDF upload registers successfully
  - Markdown upload registers successfully
  - unsupported extension is rejected explicitly
  - fake PDF content with `.pdf` extension is rejected explicitly
  - omitted title falls back to filename-derived title
- Add `tests/stages/test_register_stage.py` for stage semantics:
  - creates a durable document with stable identity
  - persists raw artifact linkage
  - persists checksum and raw storage path
  - appends exactly one `REGISTER` lifecycle event
  - is idempotent for the same intake context
  - does not create `document_jobs`
- Add targeted failure-path tests:
  - registration transaction failure does not leave a partial document row
  - best-effort raw artifact cleanup happens after database failure
- Keep the existing contract, persistence, and artifact-store suites intact as regression guardrails.
- Validation target for the implementation PR: `make test`

## Documentation Updates
- Update `docs/evergreen/architecture.md` after implementation lands so the new internal app/service seam appears in current repo truth.
- Update `docs/evergreen/runbook.md` with the internal command for running the upload app locally.
- Do not update `docs/evergreen/api-contracts.md` because PR 3 does not earn a stable public contract.

## Deferred
- `document_jobs` creation and extraction handoff
- worker claiming, retry policy, and stage dispatch
- `GET /documents/{doc_id}` and status endpoints
- extraction and normalization runtimes
- section and chunk persistence
- indexing, readiness evaluation, and retrieval smoke checks
- file-size caps, streaming uploads, timeout enforcement, and broader hardening
