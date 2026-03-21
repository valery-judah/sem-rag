# WS-029 Design: Dependency Wiring Decoupling

**Status:** Draft
**Applies to:** WS-029
**Decision:** Strategy A+
**Last updated:** 2026-03-20

## Purpose

This document turns the framing in [`WS-029-framing.md`](./WS-029-framing.md) into a
concrete implementation design.

The chosen direction is **Strategy A+**:

- extract plain construction logic into a non-FastAPI factory module
- keep `app/deps.py` as thin FastAPI wiring
- move non-HTTP builders used by runtime entrypoints out of `deps.py`
- narrow internal route wiring so each route constructs only the service it actually uses

This is an internal repo-shaping change. It does not create a new public API.

## Authority and scope

This design is subordinate to:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
3. `docs/evergreen/api-contracts.md`
4. [`WS-029-framing.md`](./WS-029-framing.md)
5. `docs/workstreams/WS-030-di/di-principles.md`

This document defines:

- the target construction boundary for lifecycle worker dependencies
- the target responsibility split between factories and FastAPI providers
- the target wiring shape for internal routes

This document does not define a repo-wide inversion refactor.

## Current pain to remove

Today, `src/doc_forge/app/deps.py` does both of the following:

- acts as the FastAPI dependency module
- acts as the imperative construction API for the worker runtime

That leads to three concrete problems:

1. `src/doc_forge/lifecycle/worker.py` imports private builders from `app.deps` and calls a
   FastAPI-shaped provider directly.
2. `get_document_lifecycle_worker()` has a misleading contract: it looks like edge-only DI
   wiring but is also used as a normal Python factory.
3. The internal route wiring constructs both `DocumentLifecycleService` and
   `DocumentLifecycleWorker` for both internal routes, even though each route only needs one
   of them.

## Design goals

At the end of this change:

- non-HTTP code constructs workers through plain Python factories
- FastAPI-specific wiring stays in `app/deps.py`
- `worker.py` contains no `Depends` or `Annotated` imports or usage
- internal routes depend only on the service graph they need
- current provider override seams remain available for tests

## Non-goals

- converting `deps.py` into a package
- moving worker ownership into FastAPI lifespan
- introducing new domain ports or protocols across the repo
- changing lifecycle behavior, job semantics, or route contracts

## Main design decisions

### 1. Add a plain factory module

Add a new module:

```text
src/doc_forge/app/factories.py
```

This module owns plain Python construction logic only. It must not import FastAPI.

It should become the home for builders that are valid both inside and outside HTTP wiring:

- `build_engine(database_url: str) -> Engine`
- `build_artifact_store(root: str) -> FilesystemArtifactStore`
- `build_embedding_adapter(backend: str, model_name: str) -> EmbeddingAdapter`
- `build_answer_generator(...) -> GroundedAnswerGenerator`
- `build_document_lifecycle_service(...) -> DocumentLifecycleService`
- `build_document_lifecycle_worker(...) -> DocumentLifecycleWorker`

The exact final list may be slightly smaller or larger, but the rule is stable:
if a builder is plain constructor composition and may be needed outside FastAPI, it belongs
in the factory module rather than in `deps.py`.

### 2. Keep `app/deps.py` as FastAPI wiring only

`src/doc_forge/app/deps.py` remains the composition root for HTTP dependency injection.

Its responsibilities after the change:

- resolve `Settings` via `Depends(get_settings)` when needed
- translate settings into plain builder inputs
- delegate object construction to `app.factories`
- expose provider functions for routes and test overrides
- retain `reset_runtime_caches()` as the test-facing cache reset entrypoint

Its responsibilities after the change do **not** include:

- owning the underlying construction logic
- serving as the import target for worker runtime construction

### 3. Move runtime-safe shared builders out of `deps.py`

The worker runtime currently imports `_build_engine` and `_build_artifact_store` from
`app.deps`. That is the wrong boundary.

After the change:

- cached engine construction moves to `app.factories.build_engine`
- cached artifact-store construction moves to `app.factories.build_artifact_store`
- any cache clears needed by tests are still triggered through `reset_runtime_caches()`

This keeps the runtime entrypoint coupled to plain Python factories, not to FastAPI wiring.

### 4. Split the internal app service by route responsibility

The current `InternalAppService` bundles retrieval and worker actions into one object:

- `retrieval_query()` uses `DocumentLifecycleService`
- `run_next_job()` uses `DocumentLifecycleWorker`

That combined service causes over-construction because both dependencies are always built
through `get_internal_app_service()`.

The design should replace that shared boundary with two route-specific services:

- `InternalRetrievalAppService`
- `InternalWorkerAppService`

Recommended location:

```text
src/doc_forge/app/services/internal.py
```

Recommended shape:

```python
@dataclass(frozen=True, slots=True)
class InternalRetrievalAppService:
    lifecycle_service: DocumentLifecycleService
    ...


@dataclass(frozen=True, slots=True)
class InternalWorkerAppService:
    worker: DocumentLifecycleWorker
    ...
```

This preserves the current app-service pattern while making route dependencies honest.

### 5. Keep provider override seams stable for tests

Current tests override providers such as `get_document_lifecycle_worker` with
`app.dependency_overrides[...]`.

The new design should preserve that style:

- route providers should still depend on `get_document_lifecycle_worker` and
  `get_document_lifecycle_service`
- tests may override the lower-level providers or the route-specific app-service providers
- `reset_runtime_caches()` should remain importable from `doc_forge.app.deps`

This keeps the change aligned with the repo's current test strategy.

### 6. Do not use FastAPI lifespan in this workstream

The worker is currently a stateless coordinator over repositories and stage runners.
That does not justify FastAPI lifespan ownership yet.

Lifespan should remain reserved for true app-scoped resources with startup and shutdown
concerns, such as connection pools or managed clients. If worker construction later becomes
observably expensive or gains managed resources, the decision can be revisited in a separate
workstream.

## Target repo shape

Recommended resulting shape:

```text
src/doc_forge/app/
  api.py
  deps.py
  factories.py
  routers/
    internal.py
  services/
    internal.py

src/doc_forge/lifecycle/
  worker.py
```

## Target wiring shape

### Factory layer

The factory module should look conceptually like this:

```python
from functools import cache


@cache
def build_engine(database_url: str) -> Engine:
    ...


@cache
def build_artifact_store(root: str) -> FilesystemArtifactStore:
    ...


@cache
def build_embedding_adapter(backend: str, model_name: str) -> EmbeddingAdapter:
    ...


def build_document_lifecycle_service(
    engine: Engine,
    artifact_store: FilesystemArtifactStore,
    embedding_adapter: EmbeddingAdapter,
) -> DocumentLifecycleService:
    ...


def build_document_lifecycle_worker(
    engine: Engine,
    artifact_store: FilesystemArtifactStore,
    embedding_adapter: EmbeddingAdapter,
) -> DocumentLifecycleWorker:
    ...
```

Important constraints:

- no FastAPI imports
- no `Depends`
- no `Annotated`
- no hidden calls to `get_settings()`

Inputs must be explicit.

### FastAPI provider layer

`app/deps.py` should become thin translation and delegation:

```python
def get_engine(settings: Annotated[Settings, Depends(get_settings)]) -> Engine:
    return build_engine(settings.database_url)


def get_artifact_store(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FilesystemArtifactStore:
    return build_artifact_store(str(settings.artifact_root))


def get_embedding_adapter(
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmbeddingAdapter:
    return build_embedding_adapter(
        settings.embedding_backend,
        settings.embedding_model,
    )


def get_document_lifecycle_worker(
    engine: Annotated[Engine, Depends(get_engine)],
    artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
    embedding_adapter: Annotated[EmbeddingAdapter, Depends(get_embedding_adapter)],
) -> DocumentLifecycleWorker:
    return build_document_lifecycle_worker(
        engine=engine,
        artifact_store=artifact_store,
        embedding_adapter=embedding_adapter,
    )
```

The exact provider graph may vary slightly, but `deps.py` should read as wiring, not as the
primary place where the lifecycle object graph is implemented.

### Internal route layer

The internal routes should depend on route-specific app services:

```python
@router.post("/retrieval/query")
def retrieval_query(
    request: Annotated[RetrievalQueryRequest, Body(...)],
    service: Annotated[
        InternalRetrievalAppService,
        Depends(get_internal_retrieval_app_service),
    ],
) -> RetrievalQueryResponse:
    return service.retrieval_query(request)


@router.post("/internal/run-next-job")
def run_next_job(
    service: Annotated[
        InternalWorkerAppService,
        Depends(get_internal_worker_app_service),
    ],
) -> WorkerJobResult:
    return service.run_next_job()
```

This is the key step that removes unnecessary paired construction from the internal HTTP
boundary.

### Worker runtime entrypoint

`src/doc_forge/lifecycle/worker.py:main()` should import only plain factories and settings:

```python
from doc_forge.app.factories import (
    build_artifact_store,
    build_document_lifecycle_worker,
    build_embedding_adapter,
    build_engine,
)
from doc_forge.app.settings import get_settings


def main() -> None:
    settings = get_settings()
    worker = build_document_lifecycle_worker(
        engine=build_engine(settings.database_url),
        artifact_store=build_artifact_store(str(settings.artifact_root)),
        embedding_adapter=build_embedding_adapter(
            settings.embedding_backend,
            settings.embedding_model,
        ),
    )
    ...
```

The exact imports may differ if a convenience runtime factory is added, but the critical rule
is stable: `worker.py` must no longer import construction helpers from `app.deps`.

## Cache and settings behavior

The current repo intentionally caches settings and several runtime singletons.
That behavior should remain unchanged.

Requirements:

- `get_settings()` remains the process-scoped cached settings source
- factory-level cached builders remain cached
- `reset_runtime_caches()` continues clearing the relevant caches for tests

Implementation consequence:

- even if cached builders move to `app.factories`, `reset_runtime_caches()` in `app.deps`
  must clear their caches

This preserves the behavior documented in
`docs/workstreams/WS-028-config-management/settings-lifecycle.md`.

## Migration plan

Implement in this order:

1. Add `src/doc_forge/app/factories.py` and move pure builders there without changing behavior.
2. Update `app/deps.py` providers to delegate to the factory module.
3. Update `reset_runtime_caches()` to clear caches owned by the factory module.
4. Update `lifecycle/worker.py` to use plain factories directly.
5. Split `InternalAppService` into route-specific services.
6. Update `app/deps.py` and `routers/internal.py` to use route-specific providers.
7. Update tests that need new provider names while preserving existing lower-level override seams.
8. Run `uv run poe verify`.

This order keeps the change incremental and easier to validate.

## Validation strategy

Required validation:

- `uv run poe verify`

Targeted behavior to preserve:

- `POST /internal/run-next-job` continues returning the same payload shape
- worker runtime still runs independently through `runtime.py worker`
- internal retrieval route behavior is unchanged
- dependency override tests continue working

## Acceptance criteria

The implementation should be considered correct when all of the following are true:

- `src/doc_forge/lifecycle/worker.py` contains no `Depends`
- `src/doc_forge/lifecycle/worker.py` contains no `Annotated`
- `src/doc_forge/lifecycle/worker.py` does not import private builders from `app.deps`
- `src/doc_forge/app/factories.py` contains no FastAPI imports
- `app/deps.py` reads primarily as wiring and delegation
- `/retrieval/query` no longer requires worker construction
- `/internal/run-next-job` no longer requires `DocumentLifecycleService` construction
- `uv run poe verify` is green

## Rejected alternatives

### Keep the current dual-use pattern

Rejected because it leaves FastAPI DI outside the HTTP edge and keeps misleading provider
signatures as imperative construction APIs.

### Use FastAPI lifespan now

Rejected because it solves a possible optimization before the code has earned it, introduces
more invasive route and app changes, and weakens the current provider-override testing seam.

### Split `deps.py` into a package now

Rejected because the extra package movement adds churn without adding meaningful value over the
chosen A+ design.
