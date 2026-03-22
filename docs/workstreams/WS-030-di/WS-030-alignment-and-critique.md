
# Review: Repo Alignment with DI Principles

## Context

This review checks the current codebase against the 10 stable principles in
`docs/workstreams/WS-030-di/di-principles.md`. The intent is to identify gaps
and decide whether remediation is warranted.

---

## Findings by Principle

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| 1 | Domain must not import FastAPI | ⚠️ Gap | All four `app/services/` files import `HTTPException`/`status` |
| 2 | High-level policy on contracts only | ✅ | Extensive Protocol usage throughout domain and query layers |
| 3 | `Depends` at the edge only | ✅ | All `Depends(...)` confined to `deps.py` and routers |
| 4 | Constructor injection inside | ✅ | All services/use-cases built via `__init__` args |
| 5 | Protocol by default for ports | ✅ | Every external port is a `Protocol`; no ABCs leaking into domain |
| 6 | Request-scoped resources use `yield` | N/A | No per-request DB sessions; all resources are app-scoped |
| 7 | App-scoped resources use lifespan | ⚠️ Partial | `@cache`/`@lru_cache` in `factories.py`; no FastAPI lifespan handler |
| 8 | Config cached once; request state immutable | ✅ | `@lru_cache` on `get_settings()`; settings are read-only Pydantic models |
| 9 | Tests override providers, not business code | ✅ | `app.dependency_overrides` used correctly; `reset_runtime_caches()` cleans up |
| 10 | Single composition root | ✅ | `deps.py` is the one place all `get_*` providers live |

---

## Gap 1 — FastAPI in App Services (Principle 1)

**Affected files:**
- `src/doc_forge/app/services/documents.py:5`
- `src/doc_forge/app/services/queries.py:5`
- `src/doc_forge/app/services/internal.py:7`
- `src/doc_forge/app/services/system.py:4`

All four import `from fastapi import HTTPException, status` and raise
`HTTPException` directly inside service methods. This couples app services to
the FastAPI transport; services cannot be invoked outside an HTTP context
without triggering a FastAPI import.

**Fix:** Move exception translation to routers (or a thin error-mapping
helper). App services raise domain errors; routers catch them and map to
`HTTPException`. Pattern:

```python
# router
@router.post(...)
def create(..., svc: Annotated[DocumentsAppService, Depends(...)]):
    try:
        return svc.upload_document(...)
    except UnsupportedDocumentError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
```

The `status.HTTP_*` constants used only for structured log fields can be
replaced with plain integer literals (e.g. `404`) in service logging calls, or
extracted to a tiny non-FastAPI constants module.

**Scope:** Each service has 2–5 exception-mapping sites. Total ~15–20 lines
changed across 4 service files + 4 router files.

---

## Gap 2 — Lifespan vs. @cache (Principle 7)

**Affected files:**
- `src/doc_forge/app/factories.py` (all `@cache`-decorated builders)
- `src/doc_forge/app/api.py` (app factory — no `lifespan=` argument)

Current approach: factory functions are decorated with `@functools.cache`;
`reset_runtime_caches()` is the cleanup hook (used only in tests).

This works correctly today because there are no teardown requirements (no
connection pool draining, no explicit model unloading). Adopting a FastAPI
`lifespan` context manager would:
- provide a clear startup/shutdown hook for future pool management
- eliminate the test-only `reset_runtime_caches()` seam

**Recommendation:** Defer until a resource actually needs startup/teardown
lifecycle. The current pattern is pragmatic and not harmful.

---

## Recommended Action

Implement Gap 1 fix only. Gap 2 is low priority.

**Files to change:**
1. `src/doc_forge/app/services/documents.py` — remove FastAPI import; raise domain errors or plain `ValueError`/custom exception
2. `src/doc_forge/app/services/queries.py` — same
3. `src/doc_forge/app/services/internal.py` — same
4. `src/doc_forge/app/services/system.py` — same
5. `src/doc_forge/app/routers/documents.py` — add exception mapping
6. `src/doc_forge/app/routers/queries.py` — add exception mapping
7. `src/doc_forge/app/routers/internal.py` — add exception mapping
8. `src/doc_forge/app/routers/system.py` — add exception mapping

**Structured log fields** that currently use `status.HTTP_*` for the
`http_status` key should be replaced with plain integer literals.

---

## Verification

```bash
uv run poe verify
```

All existing tests should pass unchanged. The observable HTTP behaviour is
identical — only the layer responsible for raising `HTTPException` changes.


# Critique

[WS-030-plan.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-030-di/WS-030-plan.md) is currently empty, so the real inputs here are [whimsical-popping-deer.md](/Users/val/.claude/plans/whimsical-popping-deer.md#L5) and [WS-030-alignment.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-030-di/WS-030-alignment.md).

**Critique**
- The proposal is directionally sensible, but it mixes two separate goals: “remove FastAPI from `app/services`” and “create a new app-level error taxonomy.” Only the first is clearly justified by the current code.
- The plan overstates the architectural violation. `app/services` are already adapter-layer code: they shape HTTP-facing DTOs and log `http_status`, e.g. [documents.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/services/documents.py#L35) and [queries.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/services/queries.py#L37). This is cleanup at the web boundary, not a core domain decoupling.
- Adding `AppError` duplicates semantics already present in domain/query exceptions. That creates two taxonomies to maintain: `DocumentNotFoundError` and `NotFoundError`, `RetryNotAllowedError` and `ConflictError`, etc. [whimsical-popping-deer.md](/Users/val/.claude/plans/whimsical-popping-deer.md#L89)
- The “global handler in `api.py` and tests unchanged” claim is false. There is already a global `Exception` handler in [api.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/api.py#L54), but many tests call route functions directly and assert `HTTPException`, for example [test_runtime_api.py](/Users/val/projects/rag/sem-rag/tests/app/test_runtime_api.py#L124) and [test_documents_api.py](/Users/val/projects/rag/sem-rag/tests/app/test_documents_api.py#L111). If routes stop raising `HTTPException` directly, those tests change.
- The plan does not fully define scope. `QueryExecutionFailedError` mapping is covered, but `incomplete_query_state` in [queries.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/services/queries.py#L92) and readiness failures in [system.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/services/system.py#L33) are transport/application failures, not domain errors. Decide whether `AppError` is for all boundary failures or only domain-to-HTTP translation.
- Be careful with public contract creep. Stable HTTP behavior matters, and the current error body is just `detail` in [schemas.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/schemas.py#L226) and [api-contracts.md](/Users/val/projects/rag/sem-rag/docs/evergreen/api-contracts.md#L56). If `error_code` becomes part of the response body, that is a contract decision, not an internal refactor.

**Decide Before Implementation**
- Are `app/services` meant to be framework-agnostic application services, or are they intentionally HTTP adapter services?
- Do we actually want a new `AppError` layer, or do we just want HTTP mapping moved to the edge?
- Where should translation live: per-route `try/except`, a shared router/helper wrapper, or a global FastAPI exception handler?
- Is `error_code` internal-only for logs, or do we want it exposed in the stable HTTP response?
- Should rich metadata like `terminal_failure.stage_name` stay only in logs, or be carried on the exception object too?
- Is `/readyz` part of this refactor, or should it stay as a simple adapter concern?

**Trade-offs**
- `AppError` layer:
  - Pros: services can be reused outside FastAPI; transport mapping is centralized.
  - Cons: second error taxonomy, more indirection, easier drift from domain semantics.
- Direct domain/query exceptions mapped at the edge:
  - Pros: least abstraction, preserves specific errors, simplest mental model.
  - Cons: needs a helper or repeated mapping code.
- Global handler:
  - Pros: least boilerplate in routers.
  - Cons: weaker direct test ergonomics and less explicit per-route behavior.
- Per-router/helper mapping:
  - Pros: explicit and compatible with current test style.
  - Cons: some duplication unless wrapped well.

My recommendation: do not approve the current plan unchanged. First decide whether `app/services` are supposed to be transport adapters or framework-agnostic application services. If they are still adapter code, the cleanest move is a small HTTP-mapping helper and no new `AppError` hierarchy. If you do want framework-agnostic services, `AppError` is defensible, but prefer router/helper translation first, not a global handler, and plan test updates explicitly.