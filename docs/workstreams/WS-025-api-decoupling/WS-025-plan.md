# Implementation Plan: API Decoupling (WS-025)

## Purpose
Turn the WS-025 framing into a reviewable staged delivery plan for stacked PRs.

This plan is implementation guidance. It does not replace the canonical constraints in:

- `[docs/evergreen/architecture.md](/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md)`
- `[docs/evergreen/api-contracts.md](/Users/val/projects/rag/sem-rag/docs/evergreen/api-contracts.md)`
- `[docs/workstreams/WS-025-api-decoupling/WS-025-framing.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-025-api-decoupling/WS-025-framing.md)`

## Execution Unit
Use stacked PRs.

Why this fits WS-025:

- the refactor has multiple earned seams: routers, app services, mappers, DTO ownership, and service-model cleanup
- stable HTTP contract preservation needs small reviewable deltas
- log behavior is already tested and should be kept under tight regression control
- the repo can stay runnable after each step without partial architectural dead ends

Avoid one large refactor PR. It would mix transport moves, DTO ownership changes, and service model cleanup into one review, which is exactly the failure mode this workstream is trying to avoid.

## PR Sizing Rule
Each PR should:

- introduce one primary seam or one primary ownership change
- keep the repo runnable and testable
- preserve stable HTTP behavior unless the PR is explicitly about internal model cleanup only
- include tests that pin the seam added in that PR
- defer follow-up cleanup instead of mixing mechanical and semantic changes

Target size: 4 PRs.

## Review Policy
Each PR description should include:

- purpose
- files expected to change
- invariants added or preserved
- tests added or adjusted
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

- moving business logging out of handlers
- DTO ownership changes
- service model cleanup

### [ ] PR 2. App Services and Thin Routers

Purpose:
Introduce the app-layer orchestration seam so routers stop owning business logging and error translation.

Deliverables:

- create `src/doc_forge/app/services/system.py`
- create `src/doc_forge/app/services/documents.py`
- create `src/doc_forge/app/services/queries.py`
- create `src/doc_forge/app/services/internal.py`
- add dependency providers in `src/doc_forge/app/deps.py` for these app services
- move endpoint-level business logs from route functions into app services
- move known domain/internal error translation into app services
- leave routers responsible only for input parsing, DI, delegation, and returning values

Likely files:

- `src/doc_forge/app/deps.py`
- `src/doc_forge/app/services/system.py`
- `src/doc_forge/app/services/documents.py`
- `src/doc_forge/app/services/queries.py`
- `src/doc_forge/app/services/internal.py`
- `src/doc_forge/app/routers/*.py`
- tests under `tests/app/`

Tests and checks:

- structured logging tests still pass with the same event names and core fields
- route tests still pass with the same status codes and error details
- routers no longer contain route-specific `try/except` translation logic

Exit condition:
Transport concerns and endpoint orchestration are separated by an app-service seam.

Deferred:

- stable-route DTO ownership cleanup
- lifecycle service result-model cleanup

### [ ] PR 3. Stable Route DTO Boundary and Pure Mappers

Purpose:
Make the app layer the clear owner of stable HTTP request/response models and centralize model-to-DTO mapping.

Deliverables:

- create `src/doc_forge/app/mappers/documents.py`
- create `src/doc_forge/app/mappers/queries.py`
- expand `src/doc_forge/app/schemas.py` to own stable route DTOs
- ensure stable routes no longer return internal lifecycle/query models directly
- add explicit request-side app DTO ownership for `POST /queries`, then map to internal `QueryRequest`
- keep internal/debug routes mixed if that avoids unnecessary scope expansion in this PR

Stable routes covered in this PR:

- `GET /healthz`
- `GET /readyz`
- `POST /documents`
- `GET /documents/{doc_id}`
- `GET /documents/{doc_id}/status`
- `GET /documents/{doc_id}/artifacts`
- `POST /documents/{doc_id}/retry`
- `POST /queries`
- `GET /queries/{query_id}`
- `GET /queries/{query_id}/trace`
- `GET /queries/{query_id}/citations`

Likely files:

- `src/doc_forge/app/schemas.py`
- `src/doc_forge/app/mappers/documents.py`
- `src/doc_forge/app/mappers/queries.py`
- `src/doc_forge/app/services/documents.py`
- `src/doc_forge/app/services/queries.py`
- `src/doc_forge/app/routers/*.py`
- tests under `tests/app/`

Tests and checks:

- route tests assert unchanged JSON payloads for stable routes
- focused mapper tests cover lifecycle upload/status/artifact/retry mapping
- focused mapper tests cover query answer/review mapping
- no stable route response model points directly at lifecycle or query internal schema types

Exit condition:
Stable HTTP contract ownership is explicit in the app layer, and mapping is centralized.

Deferred:

- removal of OpenAPI-facing concerns from internal service result models

### [ ] PR 4. Lifecycle Service Model Cleanup and Boundary Hardening

Purpose:
Remove OpenAPI-facing schema concerns from lifecycle service result models and finalize the internal/app boundary.

Deliverables:

- remove `json_schema_extra` and other OpenAPI-facing schema concerns from lifecycle service result models
- rename internal lifecycle result models if needed to avoid confusion with app DTO names
- keep internal result models lightweight and app-agnostic
- adjust imports and tests so the stable API surface continues to use app DTOs only
- perform final cleanup of any leftover direct app-schema leakage or route-layer mapping logic

Likely files:

- `src/doc_forge/lifecycle/service.py`
- `src/doc_forge/app/schemas.py`
- `src/doc_forge/app/mappers/documents.py`
- `src/doc_forge/app/services/documents.py`
- tests under `tests/app/` and `tests/lifecycle/`

Tests and checks:

- `DocumentLifecycleService` no longer owns OpenAPI-oriented examples or app-contract metadata
- stable route payloads are unchanged
- lifecycle service tests still pass on internal models
- full repo validation passes

Exit condition:
The stable HTTP DTO boundary is app-owned, and the lifecycle service no longer carries HTTP-contract concerns.

## Merge Order
Recommended merge order:

1. PR 1: router extraction and app assembly
2. PR 2: app services and thin routers
3. PR 3: stable route DTO boundary
4. PR 4: lifecycle service model cleanup

Do not merge PR 3 before PR 2. The DTO boundary becomes much harder to review if routers still own business logging and error translation.

Do not merge PR 4 before PR 3. Internal model cleanup should happen only after the app layer clearly owns the stable boundary.

## Validation Strategy
Primary validation command for each PR:

```bash
uv run poe verify
```

Additional review expectations:

- inspect the route set and OpenAPI-visible response models after PR 1 and PR 3
- keep structured logging assertions intact after PR 2
- confirm stable JSON shapes remain unchanged for all documented stable routes after PR 3 and PR 4

## Final Acceptance Criteria
WS-025 is complete when all of the following are true:

- `src/doc_forge/app/api.py` is application assembly only
- route declarations live under `src/doc_forge/app/routers/`
- routers are transport-thin and do not own business logging or domain-error translation
- stable routes return DTOs owned by the app layer
- model-to-DTO conversion is centralized in app mappers/services rather than being scattered in route functions
- `DocumentLifecycleService` no longer owns OpenAPI-facing schema concerns
- the stable contract in evergreen API docs remains unchanged
- `uv run poe verify` passes
