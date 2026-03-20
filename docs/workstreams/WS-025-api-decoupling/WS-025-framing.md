# Framing

## Problem
`[src/doc_forge/app/api.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/api.py)` currently owns too many responsibilities at once:

- FastAPI app creation and Swagger toggling
- request middleware and global exception handling
- route declarations and endpoint metadata
- endpoint-level business logging
- domain-error to HTTP-error translation
- ad hoc model-to-DTO conversion

The current file is therefore the transport layer, part of the application layer, and part of the HTTP contract layer at the same time.

A second coupling problem exists at the HTTP boundary: some stable routes already use app-layer DTOs from `[src/doc_forge/app/schemas.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/schemas.py)`, while others expose internal lifecycle/query models directly from `[src/doc_forge/lifecycle/service.py](/Users/val/projects/rag/sem-rag/src/doc_forge/lifecycle/service.py)` and `[src/doc_forge/query/review.py](/Users/val/projects/rag/sem-rag/src/doc_forge/query/review.py)`. That makes it unclear where the stable API contract actually lives.

## Canonical Constraints
- The stable HTTP contract in `[docs/evergreen/api-contracts.md](/Users/val/projects/rag/sem-rag/docs/evergreen/api-contracts.md)` must remain unchanged.
- The current runtime topology in `[docs/evergreen/architecture.md](/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md)` remains one FastAPI service with internal lifecycle/query seams; this workstream is an internal refactor, not a service split.
- No business behavior changes are in scope for lifecycle processing, query execution, readiness checks, or review loading.
- No route additions, removals, path changes, request-shape changes, or response-shape changes are allowed for stable routes.

## In Scope
- Split `[src/doc_forge/app/api.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/api.py)` into app assembly plus router modules.
- Introduce an app-layer service seam that owns endpoint orchestration, endpoint business logging, HTTP error translation, and DTO mapping.
- Define and enforce where model-to-DTO conversion happens.
- Move stable HTTP request/response DTO ownership into the app layer.
- Remove OpenAPI-oriented schema concerns from lifecycle service result models.

## Out Of Scope
- Changing `DocumentLifecycleService`, `QueryService`, or `QueryReviewService` business behavior.
- Changing the stable localhost API described in evergreen contracts.
- Creating class-based controllers.
- Introducing a public Python package API.
- Reworking query-stage internals, persistence layout, or worker behavior.

## Current Repo Truth
Today the route layer is mixed:

- stable routes such as `GET /documents/{doc_id}` and `POST /queries` already build app DTOs in `api.py`
- other stable routes return internal models directly, including lifecycle result models and query review models
- internal/debug routes such as `POST /retrieval/query` and `POST /internal/run-next-job` are also defined in `api.py`
- endpoint-level logs such as `document.upload.accepted`, `query.api.started`, and `review.summary.loaded` are emitted directly inside route functions
- `DocumentLifecycleService` includes internal result models with OpenAPI-oriented `Field` metadata and examples, which is HTTP-contract leakage into the service layer

## Decisions
### 1. Controller shape
Use router modules, not controller classes.

“Controller” in this workstream means the route module plus its thin endpoint functions. Endpoint functions should only:
- declare FastAPI metadata
- parse HTTP inputs
- resolve dependencies
- call one app service method
- return the mapped DTO

### 2. App-layer orchestration
Introduce app services under `src/doc_forge/app/` for transport-adjacent behavior. These services own:
- endpoint business logging
- domain/service invocation
- HTTPException translation
- domain/internal-model to app-DTO mapping

Routers must not contain business logging or domain-error handling.

### 3. DTO boundary
Enforce app-layer DTOs for stable public routes only.

Stable routes must return DTOs owned by the app layer. Internal/debug routes may remain on internal models in the first increment if that keeps the refactor smaller and clearer.

### 4. Domain model policy
Do not require dataclasses specifically.

Internal lifecycle/query result models may remain Pydantic models or other lightweight internal models, but they must not carry OpenAPI-facing concerns such as `json_schema_extra` or app-contract naming. The key rule is boundary ownership, not the concrete model base class.

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
- `services/*.py`: endpoint orchestration, endpoint logs, exception translation, mapping invocation
- `mappers/*.py`: pure conversion helpers from internal/domain models to app DTOs
- `schemas.py`: stable HTTP DTOs and request models, including OpenAPI examples

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

## Mapping Strategy
Model-to-DTO conversion happens in the app layer, immediately before returning from an app service to a router.

Rules:
- routers do not construct response DTOs inline, except for trivial constant responses if explicitly chosen
- domain services and query services do not import app DTOs
- stable-route request parsing ends at app DTO/request model level, then the app service maps into internal request models as needed
- internal/debug routes may continue returning internal models until the stable-route split is complete

Required mapping coverage:
- lifecycle upload/status/artifact/retry results -> app response DTOs
- persisted document model -> `DocumentDetailResponse`
- query runtime state -> `QueryAnswerResponse`
- query review internal models -> app review DTOs for summary, trace, and citations

## Logging and Error Policy
- request-scoped middleware logging stays in `api.py`
- endpoint business logs move from route functions into app services
- existing event names and key structured fields should be preserved so current log-based tests stay valid
- app services translate known domain/internal errors into `HTTPException`
- global unhandled-exception handling remains app-level in `api.py`

This workstream does not introduce a second custom app-exception hierarchy unless implementation shows a clear simplification benefit.

## Dependency Wiring
`[src/doc_forge/app/deps.py](/Users/val/projects/rag/sem-rag/src/doc_forge/app/deps.py)` should continue building domain services and also add provider functions for the new app services. Routers depend on app services, not directly on `DocumentLifecycleService`, `QueryService`, or `QueryReviewService`.

## Implementation Sequence
1. Create router, app-service, and mapper modules with no behavioral change.
2. Move route functions out of `api.py` into routers and keep them thin.
3. Move endpoint logging and try/except translation into app services.
4. Introduce pure mappers and stop building DTOs inline in route functions.
5. Move stable HTTP DTO ownership into the app layer.
6. Strip OpenAPI-facing schema metadata from lifecycle service result models.
7. Leave internal/debug routes mixed only if needed to keep the stable-route refactor focused.

## Validation and Exit Criteria
- `api.py` contains only app assembly concerns plus middleware and global exception handlers.
- All route declarations live under `app/routers/`.
- Routers do not contain endpoint business logging or domain-error translation.
- Stable routes return DTOs owned by the app layer.
- `DocumentLifecycleService` no longer owns OpenAPI-facing examples or HTTP-contract schema concerns.
- Existing stable route paths, methods, request bodies, response shapes, and status codes remain unchanged.
- Existing structured logging expectations still pass.
- Validation command for the implementation work is `uv run poe verify`.

## Implementation Notes
- Prefer explicit mapper functions over implicit `model_dump()` passthrough at the HTTP boundary.
- Keep internal lifecycle/query model names distinct from app DTO names to avoid contract confusion.
- If moving all stable DTOs into one file becomes noisy, it is acceptable to split `schemas.py` into app-owned schema modules later, but this workstream should begin with app ownership first and file shuffling second.

## Linked Artifacts
- Implementation Plan: `[docs/workstreams/WS-025-api-decoupling/WS-025-plan.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-025-api-decoupling/WS-025-plan.md)`
