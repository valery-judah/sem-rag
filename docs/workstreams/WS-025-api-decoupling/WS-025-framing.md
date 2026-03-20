# Framing

## Problem
`[src/doc_forge/app/api.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/api.py)` and the extracted router modules still sit too close to application orchestration and HTTP contract concerns at the same time.

The underlying coupling problems are:

- routers and route-adjacent code own transport concerns, endpoint orchestration, business logging, and error translation all at once
- some stable routes expose app-owned DTOs while others expose internal lifecycle/query models directly
- internal lifecycle and query packages still carry OpenAPI-facing examples and schema language that should belong to the app layer once the boundary is cleaned up

That makes it unclear where the public HTTP contract actually lives and keeps the app boundary weaker than it should be.

## Canonical Constraints
- The current runtime topology in `[docs/evergreen/architecture.md](/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md)` remains one FastAPI service with internal lifecycle/query seams; this workstream is boundary cleanup, not a service split.
- No business behavior changes are in scope for lifecycle processing, query execution, readiness checks, or review loading.
- Stable HTTP contracts may change during this workstream when that change materially improves boundary ownership and is updated in `[docs/evergreen/api-contracts.md](/Users/val/projects/rag/sem-rag/docs/evergreen/api-contracts.md)`.
- Evergreen docs must stay aligned with implemented behavior. If the HTTP surface changes, `docs/evergreen/api-contracts.md` must change with it. If a new internal seam is earned, `docs/evergreen/architecture.md` should reflect it after implementation and validation.

## In Scope
- Split app assembly from routers and keep `api.py` focused on runtime assembly concerns.
- Introduce an app-layer service seam that owns endpoint orchestration, endpoint business logging, HTTP error translation, and response shaping.
- Make the app layer the owner of stable HTTP request/response DTOs.
- Update stable HTTP contracts where needed to make that ownership explicit and coherent.
- Remove OpenAPI-oriented schema concerns from internal lifecycle/query service and review models after the app boundary is established.

## Out Of Scope
- Changing `DocumentLifecycleService`, `QueryService`, or `QueryReviewService` business behavior.
- Splitting the service into multiple deployable services.
- Creating class-based controllers.
- Introducing a public Python package API.
- Reworking query-stage internals, persistence layout, or worker behavior beyond boundary fallout from the refactor.

## Current Repo Truth
Today the route layer is still mixed:

- route declarations live in router modules, but the routers still own business logging, `HTTPException` translation, and some response shaping
- some stable routes already use app-layer DTOs from `[src/doc_forge/app/schemas.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/schemas.py)`
- other routes still expose internal models directly from `[src/doc_forge/lifecycle/service.py](/Users/val/projects/rag/sem-rag/src/doc_forge/lifecycle/service.py)` and `[src/doc_forge/query/review.py](/Users/val/projects/rag/sem-rag/src/doc_forge/query/review.py)`
- internal lifecycle/query models still contain example metadata and HTTP-facing schema phrasing that belongs at the app boundary instead

## Decisions
### 1. Router shape
Use router modules with thin endpoint functions, not controller classes.

Endpoint functions should only:
- declare FastAPI metadata
- parse HTTP inputs
- resolve dependencies
- call one app service method
- return the result

### 2. App-layer orchestration
Introduce app services under `src/doc_forge/app/` for transport-adjacent behavior. These services own:
- endpoint business logging
- domain/service invocation
- `HTTPException` translation
- domain/internal-model to app-DTO mapping

Routers must not contain business logging or domain-error handling.

### 3. DTO boundary
The app layer owns the stable HTTP boundary.

That means:
- stable routes should return DTOs owned by `src/doc_forge/app/`
- stable request payload ownership should also live in the app layer where practical
- internal/debug routes may continue returning internal models when that keeps the design simpler and does not blur the stable public boundary

### 4. Contract change policy
This workstream is allowed to change stable HTTP contracts if the change is in service of a cleaner boundary and the evergreen contract docs are updated in the same implementation step.

This is no longer framed as a strict no-contract-change internal refactor.

### 5. Domain model policy
Do not require dataclasses specifically.

Internal lifecycle/query result models may remain Pydantic models or other lightweight internal models, but they must not carry OpenAPI-facing concerns once the app layer owns the public boundary. The key rule is ownership, not the concrete model base class.

## Target Structure
Target module layout:

```text
src/doc_forge/app/
  api.py
  deps.py
  schemas.py
  routers/
    system.py
    documents.py
    queries.py
    internal.py
  services/
    system.py
    documents.py
    queries.py
    internal.py
  mappers/
    documents.py
    queries.py
```

Responsibilities:

- `api.py`: create app, configure logging, register middleware, register global exception handlers, include routers
- `routers/*.py`: route declarations, FastAPI metadata, request parsing, DI, one-call delegation to app services
- `services/*.py`: endpoint orchestration, endpoint logs, exception translation, mapping invocation, response shaping
- `mappers/*.py`: pure conversion helpers from internal/domain models to app DTOs where a separate mapper module remains worthwhile
- `schemas.py`: app-owned HTTP DTOs and request models, including OpenAPI examples

## Route Ownership
Router grouping:

- `system.py`
  - `GET /healthz`
  - `GET /readyz`
- `documents.py`
  - `POST /documents`
  - `GET /documents/{doc_id}`
  - `GET /documents/{doc_id}/status`
  - `GET /documents/{doc_id}/artifacts`
  - `POST /documents/{doc_id}/retry`
  - `DELETE /documents/{doc_id}`
- `queries.py`
  - `POST /queries`
  - `GET /queries/{query_id}`
  - `GET /queries/{query_id}/trace`
  - `GET /queries/{query_id}/citations`
- `internal.py`
  - `POST /retrieval/query`
  - `POST /internal/run-next-job`

Stable-route DTO ownership applies to:
- `/healthz`
- `/readyz`
- `POST /documents`
- `GET /documents/{doc_id}`
- `GET /documents/{doc_id}/status`
- `GET /documents/{doc_id}/artifacts`
- `POST /documents/{doc_id}/retry`
- `POST /queries`
- `GET /queries/{query_id}`
- `GET /queries/{query_id}/trace`
- `GET /queries/{query_id}/citations`

Internal/debug routes may remain on internal models if that produces a cleaner boundary with less incidental complexity.

## Mapping Strategy
Model-to-DTO conversion happens in the app layer, immediately before returning from an app service to a router.

Rules:
- routers do not construct response DTOs inline, except for trivial constant responses if explicitly chosen
- domain services and query services do not import app DTOs
- stable-route request parsing should end at app DTO/request model level, then the app service maps into internal request models as needed
- internal/debug routes may continue returning internal models where appropriate

Required mapping coverage:
- lifecycle upload/status/artifact/retry results to app response DTOs where those routes are part of the stable boundary
- persisted document model to `DocumentDetailResponse`
- query runtime state to `QueryAnswerResponse`
- query review internal models to app review DTOs if PR 2 chooses to stop exposing `query.review` models directly

## Logging and Error Policy
- request-scoped middleware logging stays in `api.py`
- endpoint business logs move from route functions into app services
- existing event names and key structured fields should remain stable unless there is a deliberate observability change
- app services translate known domain/internal errors into `HTTPException`
- global unhandled-exception handling remains app-level in `api.py`

This workstream does not introduce a second custom app-exception hierarchy unless implementation shows a clear simplification benefit.

## Dependency Wiring
`[src/doc_forge/app/deps.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/deps.py)` should continue building domain services and also add provider functions for the new app services. Routers depend on app services, not directly on `DocumentLifecycleService`, `QueryService`, or `QueryReviewService`.

## Implementation Sequence
1. Extract routers and keep `api.py` focused on app assembly.
2. Introduce app services and move endpoint logging, error translation, and response shaping into them.
3. Make the app layer the clear owner of stable-route DTOs and update evergreen API docs for any contract changes required by that boundary.
4. Remove leftover OpenAPI-facing schema metadata from internal lifecycle/query models.
5. Tighten internal naming and boundary clarity without changing business behavior.

## Validation and Exit Criteria
- `api.py` contains only app assembly concerns plus middleware and global exception handlers.
- All route declarations live under `app/routers/`.
- Routers do not contain endpoint business logging, domain-error translation, or response DTO construction.
- Stable routes return DTOs owned by the app layer.
- Internal lifecycle/query packages no longer own unnecessary OpenAPI-facing examples or schema concerns.
- Evergreen API docs accurately describe the implemented stable HTTP contract, including any deliberate changes made during the workstream.
- Existing structured logging expectations still pass, or are updated intentionally with clear rationale.
- Validation command for implementation work is `uv run poe verify`.

## Implementation Notes
- Prefer explicit mapper functions over implicit `model_dump()` passthrough at the HTTP boundary.
- Keep internal lifecycle/query model names distinct from app DTO names to avoid contract confusion.
- If moving all stable DTOs into one file becomes noisy, it is acceptable to split `schemas.py` into app-owned schema modules later, but app ownership matters more than file layout.

## Linked Artifacts
- Implementation Plan: `[docs/workstreams/WS-025-api-decoupling/WS-025-plan.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-025-api-decoupling/WS-025-plan.md)`
- PR 2 handoff: `[docs/workstreams/WS-025-api-decoupling/WS-025-PR2-handoff.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-025-api-decoupling/WS-025-PR2-handoff.md)`
- PR 3 handoff: `[docs/workstreams/WS-025-api-decoupling/WS-025-PR3-handoff.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-025-api-decoupling/WS-025-PR3-handoff.md)`
