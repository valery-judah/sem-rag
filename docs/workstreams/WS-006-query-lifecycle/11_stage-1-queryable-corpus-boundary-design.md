# Stage 1 Design: Queryable Corpus Boundary and Document Read Model

**Status:** Implemented  
**Applies to:** WS-006 / MVP / Stage 1  
**Last updated:** 2026-03-11

## Purpose

This document records the repo-facing Stage 1 design as implemented in `doc_forge`.

Stage 1 does not implement retrieval, support assessment, or answer generation.
It implements the boundary that later query stages depend on:

- only `READY` documents are queryable;
- each query run captures a stable corpus snapshot at query start;
- later query work reads against persisted snapshot membership rather than live workspace state;
- empty workspaces are represented explicitly instead of as failures.

## Authority and scope

This document is subordinate to:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
3. `docs/evergreen/api-contracts.md`
4. [`07_design.md`](./07_design.md)
5. [`10_stage-0-foundation-design.md`](./10_stage-0-foundation-design.md)
6. [`query_subsystem_staged_implementation_plan.md`](./query_subsystem_staged_implementation_plan.md)

This document describes internal repo shape and current implementation truth only.
It does not create a stable public API.

## Outcome

Stage 1 is implemented with:

- a read-only query-facing document adapter in [documents.py](src/doc_forge/readmodels/documents.py);
- query-facing document, section, and chunk projections;
- snapshot capture through `QueryService.prepare_query()`;
- durable persistence for query runs and query snapshots;
- an internal `POST /queries` endpoint that records the run and snapshot, then returns a stub response;
- tests covering `READY`-only visibility, snapshot freezing, and empty snapshots.

## Design constraints resolved in Stage 1

Stage 1 had to work with the repo that exists today.

The relevant constraints were:

- there is no separate workspace registry table;
- there is no ACL or ownership enforcement layer yet;
- lifecycle persistence already owns documents, sections, chunks, and index entries;
- `ProcessingStatus.READY` is the earned queryability boundary;
- the repo does not support historical time-travel reads for document status.

The implemented consequence is straightforward:

- workspace validation remains a non-empty `workspace_id` plus repository scoping;
- query-time freezing is membership-based, not historical-state-based;
- snapshot determinism comes from persisted `eligible_doc_ids`, not from replaying lifecycle state at a later time.

## Implemented shape

### Read model

[documents.py](src/doc_forge/readmodels/documents.py) now exposes:

- `QueryableDocumentRecord`
- `QueryableSectionRecord`
- `QueryableChunkRecord`
- `QueryableCorpusReadModel`
- `SqlQueryableCorpusReadModel`

`SqlQueryableCorpusReadModel` is repository-backed and depends on:

- `DocumentRepository`
- `SectionRepository`
- `ChunkRepository`
- `IndexEntryRepository`

It does not read raw SQL tables directly from query-stage code and it does not mutate lifecycle state.

### Queryable document boundary

`list_ready_documents(workspace_id)` filters by:

- matching `workspace_id`
- `document.ingest_status is ProcessingStatus.READY`

No non-`READY` document enters the query-facing corpus.

### Snapshot capture

`capture_snapshot(workspace_id, query_started_at=...)` returns `CorpusSnapshot` with:

- `workspace_id`
- `query_started_at`
- `eligible_doc_ids`
- optional `retrieval_index_version`
- `readiness_version=None`

Snapshot membership is frozen from the set of `READY` documents visible at capture time.

### Fixed-snapshot reads

The read model exposes:

- `list_sections_for_snapshot(snapshot)`
- `list_chunks_for_snapshot(snapshot)`

Both methods read only the persisted `eligible_doc_ids` from the snapshot.
They do not recompute workspace eligibility.

### Provenance-bearing chunk filter

`list_chunks_for_snapshot(snapshot)` returns only provenance-bearing chunks.

In the implemented code, a chunk is queryable when it retains at least one locator surface:

- `section_id`, or
- `page_start`, or
- `source_start_offset`

This keeps Stage 1 aligned with the trust requirement that query-time chunks remain traceable back to source structure or source position.

### Retrieval index version handling

`retrieval_index_version` is populated conservatively:

- if all indexed entries in the snapshot resolve to exactly one `index_version`, that value is used;
- otherwise it remains `None`.

`readiness_version` remains `None` in Stage 1 because the repo still has no canonical readiness-version artifact.

## Query persistence

[persistence.py](src/doc_forge/query/persistence.py) now includes:

- `QueryRunStore`
- `QuerySnapshotStore`
- `SqlQueryRunStore`
- `SqlQuerySnapshotStore`

The SQL-backed stores persist:

- query runs in `query_runs`
- snapshots in `query_snapshots`

The snapshot store is separate from stage tracing because snapshot capture is a boundary artifact, not a semantic stage trace.

Timezone normalization is handled on readback so SQLite-backed tests preserve UTC-aware timestamps consistently with the rest of the repo.

## Query service behavior

[service.py](src/doc_forge/query/service.py) now supports Stage 1 preparation through:

- `capture_snapshot(request, query_started_at=...)`
- `prepare_query(request)`

`prepare_query()` performs:

1. policy resolution through the existing Stage 0 policy defaults
2. query run creation
3. corpus snapshot capture
4. snapshot persistence when a snapshot store is configured
5. return of `QueryRuntimeState` with both `run` and `snapshot`

`execute()` still does not run query stages.
It only upgrades its initialization path so configured environments capture the snapshot before raising the Stage 0 not-implemented error.

## Internal API surface

[api.py](src/doc_forge/app/api.py) now exposes internal `POST /queries`.

It accepts:

- `question`
- `workspace_id`
- optional `policy_overrides`

It returns:

- `query_id`
- `workspace_id`
- `status`
- `snapshot`
- `message`

The route is intentionally thin:

- it calls `QueryService.prepare_query()`
- it persists the run and snapshot
- it returns a stub message: `"query execution is not implemented yet"`

This route remains internal-only.
It does not promote a stable public API contract.

## App wiring

[deps.py](src/doc_forge/app/deps.py) now wires:

- `get_queryable_corpus_read_model()`
- `get_query_service()`

The query service is constructed from the same SQL engine and persistence layer used by the lifecycle runtime.

## Migrations

Stage 1 adds [0004_query_subsystem_stage1.py](src/doc_forge/persistence/migrations/versions/0004_query_subsystem_stage1.py).

That migration creates:

- `query_runs`
- `query_snapshots`

These tables are the durable substrate for later query stages.

## Validation coverage

Stage 1 is covered by:

- [test_queryable_corpus_read_model.py](tests/readmodels/test_queryable_corpus_read_model.py)
- [test_query_service_prepare.py](tests/query/test_query_service_prepare.py)
- [test_runtime_api.py](tests/app/test_runtime_api.py)

The current coverage locks the key Stage 1 invariants:

- non-`READY` documents are excluded from snapshots;
- empty snapshots are explicit and valid;
- query runs persist snapshots durably;
- a document becoming `READY` later appears in a later query but not in an earlier persisted snapshot;
- the internal `/queries` route returns a stub Stage 1 payload rather than pretending execution exists.

## Deferred from Stage 1

Stage 1 still does not implement:

- workspace registry existence checks
- authenticated ownership or ACL checks
- retrieval execution
- context assembly
- support assessment
- answer-mode decisions
- generation
- citation rendering
- public API promotion

Those remain for later stages.

## Evergreen Review

Stable base reviewed during Stage 1:

- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/evergreen/api-contracts.md`

Promoted or worthy of promotion from Stage 1:

- query-facing read model over lifecycle persistence
- `READY`-only queryable corpus boundary
- durable query runs and query snapshots as internal architecture
- internal `POST /queries` as an implemented runtime seam, not a public contract

Not promoted to stable public contract:

- query request or response payload shapes
- query package exports
- internal route behavior

Why:

- Stage 1 earned internal architecture and proving tests, but not downstream compatibility guarantees
- `docs/evergreen/api-contracts.md` still correctly says there is no stable public query API

## Current Routes

Use this route when extending or reviewing Stage 1 behavior.

Stable base first:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
4. `docs/evergreen/api-contracts.md`
6. `docs/workstreams/WS-006-query-lifecycle/query_subsystem_staged_implementation_plan.md`
7. `docs/workstreams/WS-006-query-lifecycle/07_design.md`

Then use the Stage 1-specific route:

1. [documents.py](src/doc_forge/readmodels/documents.py)
2. [service.py](src/doc_forge/query/service.py)
3. [persistence.py](src/doc_forge/query/persistence.py)
4. [api.py](src/doc_forge/app/api.py)
5. [deps.py](src/doc_forge/app/deps.py)

Then confirm in tests:

1. [test_queryable_corpus_read_model.py](tests/readmodels/test_queryable_corpus_read_model.py)
2. [test_query_service_prepare.py](tests/query/test_query_service_prepare.py)
3. [test_runtime_api.py](tests/app/test_runtime_api.py)

## Context Building

This is the actual discovery path that supported Stage 1 implementation.

1. Staged plan:
   - open `query_subsystem_staged_implementation_plan.md`
   - answers: Stage 1 goal, acceptance gate, and prohibited scope expansion
2. Evergreen docs:
   - open `mvp.md`, `architecture.md`,  and `api-contracts.md`
   - answers: canonical scope, durable architecture, current routing, internal-vs-public boundary, and current repo truth
3. Existing query scaffolding:
   - open `src/doc_forge/query/`
   - answers: which contracts and service seams already exist
4. Adjacent stage design:
   - open `10_stage-0-foundation-design.md`
   - answers: expected level of repo-facing specificity and Stage 0 carry-forward constraints
5. Persistence and model seams:
   - open `src/doc_forge/persistence/`, `src/doc_forge/_contracts/`, and `src/doc_forge/lifecycle/status.py`
   - answers: what `READY` means, what provenance exists, and what persistence can actually support
6. Runtime wiring:
   - open `src/doc_forge/app/api.py` and `src/doc_forge/app/deps.py`
   - answers: where the internal route and service wiring should land
7. Proving tests:
   - open the Stage 1 tests listed above
   - answers: whether the seam is implemented repo truth rather than just design intent

Stable reusable rules for this method now live in:


Supported by repo truth in Stage 1:

- `READY` is the queryability boundary
- query membership can be frozen via persisted `eligible_doc_ids`
- internal route and persistence seams are implemented and tested

Inference due to missing seam in Stage 1:

- workspace existence can only be approximated by non-empty `workspace_id` plus document scoping because there is no workspace registry
- `readiness_version` remains unset because there is no canonical readiness-version artifact

## Log

- 2026-03-11: drafted the Stage 1 repo-facing design to define the queryable corpus boundary, snapshot persistence, and internal `/queries` route.
- 2026-03-11: implemented `SqlQueryableCorpusReadModel` with `READY`-only filtering and fixed-snapshot section/chunk reads.
- 2026-03-11: added durable `query_runs` and `query_snapshots` persistence plus migration `0004_query_subsystem_stage1.py`.
- 2026-03-11: wired `QueryService.prepare_query()` and internal `POST /queries`.
- 2026-03-11: added Stage 1 tests for read-model behavior, snapshot freezing, and route behavior.
- 2026-03-11: rewrote this document from forward-looking design draft into implemented Stage 1 repo truth.

## Status

- Stage status: implemented
- Public API status: unchanged, still internal-only
- Query execution status: not implemented beyond run creation and snapshot capture
- Validation status: `make test` passed on 2026-03-11
