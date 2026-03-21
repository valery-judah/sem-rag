# Framing

## Problem

`deps.py` currently serves two incompatible roles simultaneously:

1. **FastAPI dependency provider**: functions with `Annotated[..., Depends(...)]`
   signatures that FastAPI resolves per-request via its DI system.
2. **Imperative object factory**: the same functions are called directly by
   `lifecycle/worker.py:main()`, which runs outside any FastAPI request context.

The dual-use is subtle but real. `get_document_lifecycle_worker` has the signature:

```python
def get_document_lifecycle_worker(
    engine: Annotated[Engine, Depends(get_engine)],
    artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
) -> DocumentLifecycleWorker:
```

FastAPI reads the `Annotated` metadata and injects values. When called from `worker.py`,
Python ignores that metadata, so callers must pass arguments explicitly. The signature lies
about its contract: it looks like a DI-only provider, but it is also being used as a normal
factory function outside FastAPI.

Additionally, `DocumentLifecycleWorker` is built per-request through `Depends`, via
`get_internal_app_service`. The worker is a stateless coordinator, so this works, but it
means the full dependency graph is re-constructed on every call to `POST /internal/run-next-job`.

There is a second coupling issue in the current internal route wiring:
`get_internal_app_service` constructs both `DocumentLifecycleService` and
`DocumentLifecycleWorker`, even though `POST /retrieval/query` only needs the lifecycle
service and `POST /internal/run-next-job` only needs the worker. The current boundary
therefore over-constructs both halves of the internal graph.

## Scope

Clarify the construction and injection boundary for `DocumentLifecycleWorker` and the
broader `deps.py` object graph. The outcome should make the role of `deps.py` unambiguous,
give the worker process a clean construction path, and make the internal route wiring more
honest about what each route actually depends on.

## Constraints

- `uv run poe verify` must stay green: format, lint, pyright, and tests.
- `POST /internal/run-next-job` must keep working because it is used by the test harness.
- The worker process (`runtime.py worker`) must keep working independently of FastAPI.
- Avoid adding indirection for its own sake; the fix should reduce confusion, not add layers.

## Input context

- paths:
  - `src/doc_forge/app/deps.py`
  - `src/doc_forge/app/api.py`
  - `src/doc_forge/app/routers/internal.py`
  - `src/doc_forge/app/services/internal.py`
  - `src/doc_forge/lifecycle/worker.py`
  - `src/doc_forge/runtime.py`
- read first:
  - `docs/workstreams/WS-028-config-management/settings-lifecycle.md`
  - `docs/workstreams/WS-030-di/di-principles.md`

## Key decisions

- Which decoupling strategy to adopt.
- Whether `DocumentLifecycleWorker` should be built once with FastAPI lifespan or remain
  request-constructed in HTTP flows.
- Whether `deps.py` should remain a single module or be reduced to a thin FastAPI wiring layer.
- Whether the two internal routes should keep sharing one `InternalAppService` dependency or
  move to narrower route-scoped wiring.

## DI principles alignment

This decision should be evaluated against `docs/workstreams/WS-030-di/di-principles.md`,
not only against local implementation discomfort.

Relevant principles:

1. **FastAPI DI stays at the edge.**
2. **Inside the app, prefer constructor injection.**
3. **Application-scoped resources use lifespan.**
4. **Tests override providers, not business code.**
5. **Have one composition root.**

Applied here:

- The current worker entrypoint violates the edge rule because non-HTTP code imports
  `app.deps` and calls a FastAPI-shaped provider directly.
- The current worker construction path weakens constructor injection because the worker
  process is coupled to FastAPI wiring instead of plain Python factories.
- Lifespan should be reserved for true app-scoped resources. A stateless worker
  coordinator is not obviously one of them.
- Existing tests already use `app.dependency_overrides[...]` on providers, so preserving
  provider-level seams is useful.
- `deps.py` should remain a composition root for HTTP wiring, but it should stop doubling
  as an imperative construction API for non-HTTP entrypoints.

---

## Decoupling strategies

### Strategy A: Extract a plain factory module

Move heavy object-graph construction out of `deps.py` into a plain module such as
`src/doc_forge/app/factories.py`. The factory module should have no FastAPI imports and no
`Depends` annotations, only normal Python functions.

```python
# factories.py
def build_document_lifecycle_worker(
    engine: Engine,
    artifact_store: FilesystemArtifactStore,
) -> DocumentLifecycleWorker:
    ...
```

`deps.py` then becomes a thin adapter:

```python
# deps.py
def get_document_lifecycle_worker(
    engine: Annotated[Engine, Depends(get_engine)],
    artifact_store: Annotated[FilesystemArtifactStore, Depends(get_artifact_store)],
) -> DocumentLifecycleWorker:
    return build_document_lifecycle_worker(engine, artifact_store)
```

`lifecycle/worker.py` calls the plain factory directly:

```python
worker = build_document_lifecycle_worker(
    engine=build_engine(settings.database_url),
    artifact_store=build_artifact_store(str(settings.artifact_root)),
)
```

This strategy should include the already-plain builders currently hidden in `deps.py`,
especially engine and artifact-store construction, so `worker.py` no longer imports private
helpers from the FastAPI wiring module.

**Pros:** Honest signatures. Keeps FastAPI at the edge. Restores constructor injection below
the boundary. Preserves provider overrides in tests. No FastAPI dependency in the factory
module. Testable in isolation.

**Cons:** Adds a module. `deps.py` still exists as wiring glue. By itself, this does not
remove per-request reconstruction of the worker graph for HTTP requests.

---

### Strategy B: FastAPI lifespan builds the worker once at startup

Use FastAPI lifespan to construct the worker once and store it on `app.state`. The internal
route reads it from app state instead of from `Depends`.

```python
# api.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = build_engine(settings.database_url)
    artifact_store = build_artifact_store(str(settings.artifact_root))
    app.state.worker = build_document_lifecycle_worker(engine, artifact_store)
    yield

# routers/internal.py
def run_next_job(request: Request) -> WorkerJobResult:
    worker: DocumentLifecycleWorker = request.app.state.worker
    ...
```

`lifecycle/worker.py` still constructs its own worker independently.

**Pros:** Worker is built once, not per request. Lifespan is the idiomatic place for
long-lived app resources. Startup ownership becomes explicit.

**Cons:** Two construction paths remain: API lifespan and worker process. Route access through
`app.state` is less explicit than constructor parameters. This is more invasive in `api.py`,
route signatures, and tests. It is only justified if the worker is truly an application-scoped
resource whose lifecycle should be owned by FastAPI.

---

### Strategy C: Split `deps.py` into factory and wiring packages

Extend Strategy A by turning `deps.py` into a package, for example `deps/wiring.py` and
`deps/factories.py`, with `deps/__init__.py` re-exporting the public names.

**Pros:** Clearer package boundary. Easier separation between wiring and construction.

**Cons:** More file movement and refactor cost. No meaningful runtime or design benefit over
Strategy A for this specific problem.

---

### Strategy D: Accept the dual-use pattern

Leave `deps.py` as-is and document that `Annotated[..., Depends(...)]` parameters are FastAPI
conventions that also work when called directly because Python ignores the metadata.

**Pros:** Zero code change. Lowest immediate regression risk.

**Cons:** The signature remains misleading. New contributors will keep reading a DI-only
contract that is not actually DI-only. The pattern does not scale well to more non-HTTP
entrypoints. It violates the principle that FastAPI DI should stay at the edge.

---

## Analysis

### What the code currently shows

- `src/doc_forge/lifecycle/worker.py:main()` imports `_build_engine`,
  `_build_artifact_store`, and `get_document_lifecycle_worker` from `src/doc_forge/app/deps.py`
  and then calls the provider directly.
- `src/doc_forge/app/deps.py:get_document_lifecycle_worker()` is a large object-graph
  constructor with FastAPI-shaped parameters, but its implementation is plain constructor
  composition.
- `src/doc_forge/app/deps.py:get_internal_app_service()` always constructs both
  `DocumentLifecycleService` and `DocumentLifecycleWorker`.
- `src/doc_forge/app/routers/internal.py` uses that shared dependency for both internal routes,
  even though the routes consume disjoint capabilities.
- Tests currently override `get_document_lifecycle_worker` directly through
  `app.dependency_overrides`, so preserving provider-level seams is useful.

### Implications

- The dual-use smell is real, not theoretical. `deps.py` is both the FastAPI boundary and an
  imperative construction API for non-HTTP code.
- The per-request reconstruction issue is also real, but it is broader than only the worker:
  the current internal-route wiring builds both the worker and lifecycle-service graphs for
  either route.
- The code does not yet justify lifespan ownership. The worker is a stateless coordinator over
  repositories and stage runners, not a managed pool or long-lived external client.
- Extracting only `build_document_lifecycle_worker()` would help, but it is incomplete if
  `worker.py` still imports engine and artifact-store builders from `app.deps`.

## Recommended direction

Adopt **Strategy A**, but broaden it slightly beyond the original baseline.

1. Extract the worker graph into a plain factory module.
2. Move the already-plain shared resource builders used by non-HTTP code with it:
   engine, artifact store, and any other helper that runtime entrypoints must call directly.
3. Keep `deps.py` as the thin FastAPI wiring layer.
4. Update `lifecycle/worker.py` to use the plain factories directly.
5. Narrow the internal route wiring so `/retrieval/query` does not require worker construction
   and `/internal/run-next-job` does not require `DocumentLifecycleService` construction.

This is the best fit for the DI principles:

- it keeps FastAPI at the edge
- it restores constructor injection below the boundary
- it preserves provider overrides in tests
- it avoids introducing lifespan ownership before the code needs app-scoped resources

Strategy B is worth reconsidering only if the per-request reconstruction cost becomes
observable or if the worker grows true app-lifecycle concerns.

## Expected outputs

- `src/doc_forge/app/factories.py` or equivalent with honest, non-FastAPI factory functions
- Shared non-HTTP builders moved out of `deps.py` when they are needed by runtime entrypoints
- Updated `deps.py` using factories as thin FastAPI wiring only
- Updated `lifecycle/worker.py` calling plain factories directly
- Internal route wiring narrowed so each route depends only on the service it uses
- `uv run poe verify` passes

## Exit criteria

- `grep -n "Depends" src/doc_forge/lifecycle/worker.py` returns nothing
- `grep -n "Annotated" src/doc_forge/lifecycle/worker.py` returns nothing
- No FastAPI imports in the factory module
- `worker.py` does not import private builders from `app.deps`
- `/retrieval/query` no longer constructs a worker just to execute retrieval
- `/internal/run-next-job` no longer constructs `DocumentLifecycleService` just to run the queue
- `uv run poe verify` is green

## Non-goals

- Restructuring `deps.py` into a package as in Strategy C
- Switching to lifespan-based construction as in Strategy B unless cost is observed
- Introducing a broader repo-wide inversion refactor beyond this boundary
- Touching migrations, observability, or answer-generation `os.environ` patterns

## Linked artifacts

- `docs/workstreams/WS-028-config-management/settings-lifecycle.md`
- `docs/workstreams/WS-030-di/di-principles.md`
- `src/doc_forge/app/deps.py`
- `src/doc_forge/app/routers/internal.py`
- `src/doc_forge/app/services/internal.py`
- `src/doc_forge/lifecycle/worker.py`
