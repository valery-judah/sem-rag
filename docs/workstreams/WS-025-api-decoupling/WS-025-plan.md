# Implementation Plan: API Decoupling (WS-025)

## Purpose
Turn the WS-025 framing into a reviewable staged delivery plan for stacked PRs.

This plan is implementation guidance. It does not replace the canonical constraints in:

- `[docs/evergreen/architecture.md](/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md)`
- `[docs/evergreen/api-contracts.md](/Users/val/projects/rag/sem-rag/docs/evergreen/api-contracts.md)`
- `[docs/workstreams/WS-025-api-decoupling/WS-025-framing.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-025-api-decoupling/WS-025-framing.md)`
- `[docs/workstreams/WS-025-api-decoupling/WS-025-PR2-handoff.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-025-api-decoupling/WS-025-PR2-handoff.md)`

## Execution Unit
Use stacked PRs.

Why this still fits WS-025:

- the refactor has multiple earned seams: router extraction, app services, API DTO ownership, and internal service-model cleanup
- PR 2 now intentionally includes API-boundary redesign, so it needs reviewable scope and explicit doc updates
- logging and HTTP behavior are sensitive enough that changes should be isolated and justified
- the repo can stay runnable after each step without leaving a partial boundary in place for long

Avoid one large refactor PR. It would mix transport extraction, app-service introduction, contract changes, and internal cleanup into one review.

## PR Sizing Rule
Each PR should:

- introduce one primary seam or one primary ownership change
- keep the repo runnable and testable
- update evergreen docs whenever it changes stable HTTP behavior or earned architecture truth
- include tests that pin the seam added in that PR
- defer cleanup that does not need to land in the same review

Target size: 3 PRs.

## Review Policy
Each PR description should include:

- purpose
- files expected to change
- invariants added, preserved, or deliberately changed
- tests added or adjusted
- evergreen docs updated in the PR
- explicit deferrals to the next PR

## Staged PR Plan

### [x] PR 1. Router Extraction and App Assembly

Purpose:
Move route declarations out of `app/api.py` and reduce that module to application assembly concerns.

Deliverables:

- create `src/doc_forge/app/routers/system.py`
- create `src/doc_forge/app/routers/documents.py`
- create `src/doc_forge/app/routers/queries.py`
- create `src/doc_forge/app/routers/internal.py`
- move endpoint decorators and endpoint metadata into router modules
- keep `src/doc_forge/app/api.py` responsible only for:
  - logging configuration
  - Swagger/OpenAPI toggles
  - request middleware
  - global exception handlers
  - `include_router(...)`
- keep route behavior unchanged even if endpoint functions still use the current direct service dependencies temporarily

Likely files:

- `src/doc_forge/app/api.py`
- `src/doc_forge/app/routers/system.py`
- `src/doc_forge/app/routers/documents.py`
- `src/doc_forge/app/routers/queries.py`
- `src/doc_forge/app/routers/internal.py`
- tests under `tests/app/`

Tests and checks:

- existing route tests still pass
- `api.py` no longer defines route handlers directly
- router registration produces the same route set and OpenAPI surface

Exit condition:
The app has explicit router modules and `api.py` is transport assembly only.

Deferred:

- moving orchestration concerns out of handlers
- API DTO ownership changes
- service model cleanup

### [ ] PR 2. Full App-Layer Boundary and Thin Routers

Purpose:
Introduce the app-layer seam and make it the owner of endpoint orchestration, logging, exception translation, and API response shaping.

Deliverables:

- create `src/doc_forge/app/services/system.py`
- create `src/doc_forge/app/services/documents.py`
- create `src/doc_forge/app/services/queries.py`
- create `src/doc_forge/app/services/internal.py`
- add app-service dependency providers in `src/doc_forge/app/deps.py`
- refactor routers to inject app services and delegate immediately
- move endpoint-level business logs from routers into app services
- move domain/internal error translation into app services
- move response DTO construction into app services
- add or update app-owned API models in `src/doc_forge/app/schemas.py`
- update `docs/evergreen/api-contracts.md` for any route-shape, response-shape, or status-code changes introduced by the new boundary
- update `docs/evergreen/architecture.md` once `app/services` is implemented and validated as an earned seam

Likely files:

- `src/doc_forge/app/deps.py`
- `src/doc_forge/app/services/system.py`
- `src/doc_forge/app/services/documents.py`
- `src/doc_forge/app/services/queries.py`
- `src/doc_forge/app/services/internal.py`
- `src/doc_forge/app/schemas.py`
- `src/doc_forge/app/api_examples.py`
- `src/doc_forge/app/routers/*.py`
- `docs/evergreen/api-contracts.md`
- `docs/evergreen/architecture.md`
- tests under `tests/app/`

Tests and checks:

- routers no longer import `structlog`
- routers no longer contain route-specific `try/except` translation logic
- routers no longer build response DTOs inline
- structured logging tests still pass, or are intentionally updated with clear rationale
- route tests cover the implemented HTTP behavior and OpenAPI-visible response models after the redesign
- doc updates match implemented behavior in the same PR

Exit condition:
The app layer is the clear owner of the API-facing boundary for the affected routes, and routers are transport-thin.

Deferred:

- removal of OpenAPI-facing concerns from internal lifecycle/query result models where that cleanup is purely internal

### [ ] PR 3. Internal Service Model Cleanup and Boundary Hardening

Purpose:
Remove leftover app- or OpenAPI-facing concerns from internal result models now that the app layer clearly owns the public boundary.

Deliverables:

- remove `json_schema_extra` and similar OpenAPI-facing metadata from lifecycle or query internal result models where still present
- rename internal result models if needed to reduce confusion with app DTOs
- keep internal result models lightweight and app-agnostic
- perform final cleanup of direct app-schema leakage into internal packages
- update evergreen docs only if this PR changes earned architectural truth beyond what PR 2 already documented

Likely files:

- `src/doc_forge/lifecycle/service.py`
- `src/doc_forge/query/`
- `src/doc_forge/app/schemas.py`
- `src/doc_forge/app/services/*.py`
- tests under `tests/app/`, `tests/lifecycle/`, and `tests/query/`

Tests and checks:

- internal service models no longer carry HTTP-contract concerns
- app-layer tests still pass against app-owned DTOs
- full repo validation passes

Exit condition:
The app boundary is explicit and internal services no longer carry API-contract baggage.

## Merge Order
Recommended merge order:

1. PR 1: router extraction and app assembly
2. PR 2: full app-layer boundary and thin routers
3. PR 3: internal service model cleanup

Do not re-split DTO ownership out of PR 2. That would recreate the partial boundary this workstream is trying to remove.

Do not merge PR 3 before PR 2. Internal model cleanup only makes sense after the app layer clearly owns the API surface.

## Validation Strategy
Primary validation command for each code PR:

```bash
uv run poe verify
```

Additional review expectations:

- inspect the route set and OpenAPI-visible response models after PR 1 and PR 2
- keep structured logging assertions aligned with intended observability behavior after PR 2
- confirm evergreen docs match implemented route behavior whenever contract changes are introduced

## Final Acceptance Criteria
WS-025 is complete when all of the following are true:

- `src/doc_forge/app/api.py` is application assembly only
- route declarations live under `src/doc_forge/app/routers/`
- routers are transport-thin and do not own business logging, domain-error translation, or response DTO construction
- app services own endpoint orchestration and API-facing result shaping
- stable-route behavior is documented accurately in evergreen API docs, even where it changed during WS-025
- `src/doc_forge/app/services/` is an earned internal seam reflected in evergreen architecture docs
- internal lifecycle/query service models no longer carry unnecessary OpenAPI-facing concerns
- `uv run poe verify` passes
