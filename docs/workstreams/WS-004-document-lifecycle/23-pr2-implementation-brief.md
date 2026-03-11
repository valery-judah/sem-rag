---
artifact_kind: implementation_brief
id: WS-004-PR2
title: PR 2 Implementation Brief
status: draft
created: 2026-03-11
updated: 2026-03-11
---

# PR 2 Implementation Brief: Persistence Foundation and Artifact Store

## Summary
- Introduce the durable storage foundation for the document lifecycle: Postgres metadata plus filesystem-backed raw and intermediate artifacts.
- Convert `parity.persistence` from a single SQLite module into a package with an explicit migration path, while keeping current import sites working.
- Add storage seams for documents, lifecycle events, document jobs, and raw/extracted/normalized artifacts without yet implementing intake, extraction, or worker execution.

## Implementation Changes
- Replace `src/parity/persistence.py` with a `src/parity/persistence/` package.
- Add `src/parity/persistence/__init__.py` as the compatibility surface for existing `parity.persistence` imports.
- Move the current SQLite helpers into a compatibility module such as `src/parity/persistence/sqlite_compat.py` and re-export them from `__init__.py` so current contract and persistence tests do not break during PR 2.
- Add `src/parity/persistence/models.py` as the canonical schema definition for the new Postgres-backed lifecycle tables.
- Add `src/parity/persistence/repositories.py` for explicit repository protocols and first concrete Postgres implementations for:
  - document metadata
  - lifecycle event persistence
  - document job persistence
- Add `src/parity/persistence/jobs.py` for job-row runtime types and repository helpers, but do not implement worker claiming or execution loops yet.
- Add `src/parity/persistence/migrations/` with the initial migration and migration bootstrap.
- Add `src/parity/artifacts/schemas.py` for storage-facing artifact payloads and references:
  - `RawArtifactRef`
  - `ExtractedArtifact`
  - `NormalizedArtifact`
- Add `src/parity/artifacts/store.py` for a filesystem-backed `ArtifactStore` that reads and writes:
  - raw uploaded files as bytes
  - extracted artifacts as JSON
  - normalized artifacts as JSON
- Update `pyproject.toml` and `uv.lock` to add the Postgres and migration dependencies needed for the new persistence layer.

## Persistence Design Decisions
- Use Postgres for lifecycle metadata and filesystem storage for large inspectable artifacts. This matches the workstream design split and keeps raw/extracted/normalized payloads easy to inspect.
- Use SQLAlchemy Core plus Alembic for schema definition and migrations. PR 2 should avoid an ORM-heavy domain rewrite; the repository layer remains responsible for mapping storage rows into internal runtime models.
- Keep `Document`, `Section`, and `Chunk` under `src/parity/_contracts/` for now. PR 2 should not combine persistence work with another shared-model namespace migration.
- Keep the current `Document` contract shape stable in PR 2 even if the new `documents` table carries forward-looking columns such as `checksum`, `raw_storage_path`, `failure_code`, and `failure_detail`.
- Persist `LifecycleEvent.failure_category` explicitly rather than dropping it into opaque JSON, because PR 1 made failure taxonomy a real lifecycle concept.
- Add `document_jobs` now as a durable queue foundation, but keep job dispatch, retry policy, and worker ownership rules for PR 4.

## Schema Scope
- `documents` should become the durable lifecycle anchor and include:
  - stable identity and workspace boundary
  - source type, title, and filename
  - upload timestamp
  - forward-looking checksum and raw artifact path fields
  - lifecycle status and failure metadata
  - created/updated timestamps
- `lifecycle_events` should persist the PR 1 runtime event shape:
  - `event_id`
  - `doc_id`
  - `stage`
  - `from_status`
  - `to_status`
  - `occurred_at`
  - `failure_category`
  - `detail_json`
- `document_jobs` should persist only the queue foundation:
  - `job_id`
  - `doc_id`
  - `target_stage`
  - `status`
  - `attempt_count`
  - `not_before`
  - `error_code`
  - `error_detail`
  - `created_at`
  - `updated_at`
- Do not move `sections` or `chunks` into the new Postgres migration in PR 2. Their production schema should land with the stages that first produce and replace them.

## Artifact Store Layout
- Use a managed root directory and reject path traversal or caller-supplied absolute paths.
- Use deterministic per-document paths so later stages can overwrite or inspect artifacts without guessing locations.

```text
data/
  raw/{workspace_id}/{doc_id}/source.pdf
  raw/{workspace_id}/{doc_id}/source.md
  extracted/{workspace_id}/{doc_id}/extracted.json
  normalized/{workspace_id}/{doc_id}/normalized.json
```

- Keep artifact naming stage-scoped rather than version-history-aware in PR 2. Supersession and multi-version retention are out of scope.
- Reserve debug event logs or failure dumps for a later PR instead of broadening the initial artifact API now.

## Repository Boundaries
- `DocumentRepository` owns create/get/update semantics for durable document metadata and status changes.
- `LifecycleEventRepository` owns append/list semantics for the document event trail.
- `DocumentJobRepository` owns create/get/list semantics for queued work records.
- Stage logic in later PRs should depend on these repository interfaces rather than writing SQL directly.
- The artifact store should be a separate seam from the SQL repositories. Artifact persistence should not be hidden inside the document repository.

## Public And Internal Boundaries
- This PR does not create a stable public API, CLI contract, or HTTP contract.
- The new Postgres schema is an internal implementation seam, not an evergreen API contract.
- Do not wire the retrieval demo in `src/parity/retrieval.py` to this new persistence layer in PR 2.
- Do not implement upload endpoints, file-type validation, checksum derivation, extraction, normalization, or readiness checks in PR 2.
- Do not delete the current SQLite-backed helpers outright. Keep them as an internal compatibility seam until later PRs finish moving runtime call sites onto the new repositories.

## Tests
- Keep the current PR 1 contract suite in `tests/contract/` unchanged as the baseline lifecycle guardrail. PR 2 should not rework state-machine coverage again.
- Extend `tests/persistence/` rather than creating new flat test files. The current refactor already established `tests/persistence/` as the home for repository and integrity coverage.
- Add `tests/artifacts/` for filesystem-backed artifact storage tests. This is the new PR 2 test package introduced by the broader pytest plan that the repo can support once the artifact store exists.
- If new pytest markers are added, keep them narrow and aligned with the package split:
  - keep `contract` for lifecycle semantics
  - keep `persistence` for database-backed repository and migration tests
  - add `artifacts` only if artifact-store tests need an explicit marker

### Required PR 2 test files
- `tests/persistence/test_postgres_migrations.py`
  - migration smoke test for the initial Postgres schema
  - verifies `documents`, `lifecycle_events`, and `document_jobs` exist after migration
- `tests/persistence/test_document_repository.py`
  - extend coverage from the current SQLite seam to the new repository implementation
  - verify document create/load and status-update round trips
- `tests/persistence/test_lifecycle_event_persistence.py`
  - verify append/list behavior
  - verify ordering and `failure_category` round-trip persistence
- `tests/persistence/test_document_job_repository.py`
  - verify create/load/update semantics for queued job metadata
  - verify attempt-count and error-detail persistence
- `tests/artifacts/test_raw_artifact_store.py`
  - raw bytes write/read
  - deterministic path generation under the managed root
- `tests/artifacts/test_extracted_artifact_store.py`
  - extracted JSON write/read
  - schema validation on load
- `tests/artifacts/test_normalized_artifact_store.py`
  - normalized JSON write/read
  - overwrite semantics for the same document path

### Fixture And Backing Strategy
- Use a disposable Postgres database for migration and repository tests. These tests should exercise the real schema path, not in-memory fakes.
- Use a real temp filesystem for artifact-store tests so path handling, directory creation, and overwrite behavior are verified against actual files.
- Keep synthetic factories for storage-facing models in the relevant package-level `conftest.py` files rather than introducing stage-runner fixtures prematurely.
- Preserve the current SQLite compatibility tests during the package conversion so `parity.persistence` import compatibility remains covered while the new Postgres seam is added.

### Explicitly Deferred Test Work
- Do not add `tests/stages/` in PR 2. Stage-runner tests belong to the PRs that introduce registration, extraction, normalization, chunking, indexing, and readiness runtimes.
- Do not add `tests/pipeline/` in PR 2. End-to-end Markdown/PDF lifecycle tests would be placeholders until the runtime pipeline exists.
- Do not add readiness or retrieval-smoke tests in PR 2. Those depend on later indexing and readiness seams, and `32_status.md` explicitly records that they are not implemented yet.

## Deferred
- Intake-path behavior, including supported-type validation and checksum generation.
- Registration-stage document creation and raw artifact linkage.
- Worker claiming, retry execution, and stage dispatch.
- Extractor and normalizer implementations.
- Section and chunk production tables and repositories.
- Readiness predicates, retrieval smoke checks, and any source-inspection endpoint.
