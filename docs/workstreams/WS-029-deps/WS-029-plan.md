# Implementation Plan: Dependency Wiring Decoupling (WS-029)

## Purpose

Turn the A+ decision from [`WS-029-framing.md`](./WS-029-framing.md) and
[`WS-029-design.md`](./WS-029-design.md) into a reviewable staged delivery plan for stacked
PRs.

This plan is implementation guidance. It does not replace the canonical constraints in:

- [docs/evergreen/architecture.md](/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md)
- [docs/evergreen/api-contracts.md](/Users/val/projects/rag/sem-rag/docs/evergreen/api-contracts.md)
- [WS-029-framing.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-029-deps/WS-029-framing.md)
- [WS-029-design.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-029-deps/WS-029-design.md)
- [docs/workstreams/WS-030-di/di-principles.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-030-di/di-principles.md)

## Execution Unit

Use stacked PRs.

Why stacked PRs are the right fit for WS-029:

- the refactor has two distinct seams: construction-boundary cleanup and internal-route wiring cleanup
- `app/deps.py`, `lifecycle/worker.py`, and the internal app services are sensitive enough that
  smaller review units will reduce regression risk
- the repo should stay verifiable after each step, even if internal names or provider seams change

Avoid one large refactor PR. It would mix factory extraction, runtime entrypoint cleanup,
provider rewiring, internal service splitting, and test updates into one review.

## Breaking-change policy

Breaking internal seams is acceptable in this workstream.

That means the PRs do **not** need to preserve:

- private helper names such as `_build_engine` or `_build_artifact_store`
- the existence of `InternalAppService`
- the existence of `get_internal_app_service`
- test-only override points that are superseded by clearer provider seams

That does **not** mean a merged PR may leave the repo half-working.

Each PR must still:

- keep `uv run poe verify` green
- preserve stable HTTP behavior for the existing internal routes unless the PR explicitly and
  intentionally changes it
- keep `runtime.py worker` working

So the policy is: internal compatibility may break, but merge-time runtime integrity may not.

## PR sizing rule

Each PR should:

- introduce one primary ownership change
- keep the repo runnable and verifiable
- remove old seams rather than preserving them behind temporary aliases when that alias would
  only prolong confusion
- update workstream docs if the plan or design needs to reflect what actually landed

Target size: 3 PRs.

## Review policy

Each PR description should include:

- purpose
- files expected to change
- internal seams removed
- internal seams added
- tests added or adjusted
- explicit deferrals to the next PR

## Staged PR plan

### PR 1. Introduce Plain Factories and Decouple the Worker Runtime

Purpose:
Create the non-FastAPI construction layer and remove the worker runtime's dependency on
`app.deps`.

Deliverables:

- create `src/doc_forge/app/factories.py`
- move runtime-safe shared builders out of `src/doc_forge/app/deps.py`:
  - engine construction
  - artifact-store construction
  - embedding adapter construction
  - answer-generator construction if practical in the same pass
- update `src/doc_forge/lifecycle/worker.py` to import plain factories instead of `app.deps`
- update `src/doc_forge/app/deps.py` to delegate to the moved builders
- update `reset_runtime_caches()` so it clears caches now owned by `app.factories`
- remove the old private builder names from `app.deps` rather than keeping compatibility shims
  unless one is needed only within the PR to keep the diff coherent

Likely files:

- `src/doc_forge/app/factories.py`
- `src/doc_forge/app/deps.py`
- `src/doc_forge/lifecycle/worker.py`
- tests touching runtime cache reset or worker entrypoint behavior

Tests and checks:

- `worker.py` no longer imports `_build_engine` or `_build_artifact_store` from `app.deps`
- `worker.py` contains no `Depends`
- `worker.py` contains no `Annotated`
- cache-reset tests still pass or are updated to reflect the new cache owner
- `uv run poe verify`

Exit condition:
The worker runtime constructs itself entirely through plain factories, and `app.deps` is no
longer a required import target for non-HTTP code.

Deferred:

- moving the full lifecycle service and worker graph builders out of `deps.py`
- splitting the internal app service

### PR 2. Move Lifecycle Graph Construction Behind Factories and Thin Providers

Purpose:
Finish the ownership shift so `app.deps.py` reads as wiring and delegation rather than as the
primary implementation site for lifecycle object-graph construction.

Deliverables:

- move `DocumentLifecycleService` construction into `app.factories`
- move `DocumentLifecycleWorker` construction into `app.factories`
- move any shared helper construction needed by those graphs into `app.factories` where it
  improves clarity without overgeneralizing
- update `get_document_lifecycle_service()` and `get_document_lifecycle_worker()` so they are
  thin wrappers over the factory functions
- remove now-dead construction code from `app.deps.py`
- keep lower-level provider seams available where they are still useful for tests

Likely files:

- `src/doc_forge/app/factories.py`
- `src/doc_forge/app/deps.py`
- tests under `tests/app/` and `tests/pipeline/`

Tests and checks:

- `src/doc_forge/app/factories.py` contains no FastAPI imports
- `src/doc_forge/app/deps.py` no longer owns the lifecycle worker graph directly
- `get_document_lifecycle_worker()` and `get_document_lifecycle_service()` remain overrideable
  provider seams unless there is a deliberate and justified replacement
- `uv run poe verify`

Exit condition:
The lifecycle worker and lifecycle service graphs are owned by the factory layer, and
`app.deps.py` is visibly reduced to FastAPI wiring.

Deferred:

- splitting the internal retrieval and worker app services
- narrowing the internal route provider graph

### PR 3. Split Internal Route Wiring and Remove the Combined Internal Service

Purpose:
Remove the remaining over-construction in the internal HTTP boundary by replacing the shared
internal app service with route-specific services and providers.

Deliverables:

- replace `InternalAppService` with:
  - `InternalRetrievalAppService`
  - `InternalWorkerAppService`
- replace `get_internal_app_service` with route-specific providers
- update `src/doc_forge/app/routers/internal.py` so:
  - `/retrieval/query` depends only on retrieval-side wiring
  - `/internal/run-next-job` depends only on worker-side wiring
- update or rewrite tests that currently override `get_internal_app_service` or rely on the
  combined service shape
- remove the old combined internal service and provider instead of preserving them as aliases

Likely files:

- `src/doc_forge/app/services/internal.py`
- `src/doc_forge/app/deps.py`
- `src/doc_forge/app/routers/internal.py`
- `tests/app/test_runtime_api.py`
- relevant pipeline tests if dependency setup assumptions change

Tests and checks:

- `/retrieval/query` no longer requires worker construction
- `/internal/run-next-job` no longer requires `DocumentLifecycleService` construction
- internal route tests still verify the same HTTP payloads and statuses
- provider override tests are updated to the new route-specific seams
- `uv run poe verify`

Exit condition:
The internal HTTP boundary is honest about route dependencies, and the old combined internal
service seam is gone.

## Merge order

Recommended merge order:

1. PR 1: introduce plain factories and decouple the worker runtime
2. PR 2: move lifecycle graph construction behind factories and thin providers
3. PR 3: split internal route wiring and remove the combined internal service

Do not merge PR 3 before PR 2. Route-level cleanup is easier to review after the construction
layer is already stable.

Do not keep temporary aliases for `_build_*` helpers or `InternalAppService` beyond the PR that
removes them. This workstream is explicitly allowed to break internal seams, and carrying those
aliases forward would preserve the confusion the refactor is meant to remove.

## Validation strategy

Primary validation command for each code PR:

```bash
uv run poe verify
```

Additional review expectations:

- inspect `src/doc_forge/lifecycle/worker.py` after PR 1 to confirm it no longer depends on
  FastAPI wiring
- inspect `src/doc_forge/app/deps.py` after PR 2 to confirm it reads like wiring, not a large
  object-graph implementation module
- inspect `src/doc_forge/app/routers/internal.py` and `src/doc_forge/app/services/internal.py`
  after PR 3 to confirm each route now builds only what it uses

## Final acceptance criteria

WS-029 is complete when all of the following are true:

- `src/doc_forge/app/factories.py` exists and contains no FastAPI imports
- `src/doc_forge/lifecycle/worker.py` does not import construction helpers from `app.deps`
- `src/doc_forge/lifecycle/worker.py` contains no `Depends`
- `src/doc_forge/lifecycle/worker.py` contains no `Annotated`
- lifecycle service and worker graph construction live in the factory layer rather than directly
  in `app.deps.py`
- `app.deps.py` reads primarily as FastAPI wiring and delegation
- `/retrieval/query` no longer constructs a worker just to execute retrieval
- `/internal/run-next-job` no longer constructs `DocumentLifecycleService` just to run the queue
- `InternalAppService` and `get_internal_app_service` are removed
- `uv run poe verify` passes
