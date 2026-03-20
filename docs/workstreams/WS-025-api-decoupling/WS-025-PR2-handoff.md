# PR 2: App-Layer Boundary and Router Decoupling (WS-025)

## 1. Problem Framing
- **What problem is being solved**: The FastAPI routers currently own too much application behavior: endpoint-level structured logging, domain-to-HTTP exception mapping, and response DTO construction. That leaves the HTTP transport layer tightly coupled to application orchestration.
- **What PR 2 now does**: PR 2 establishes a full app-layer seam under `src/doc_forge/app/services/` and moves endpoint orchestration into that layer. Routers become transport adapters only.
- **What is in scope**:
  - Introduce app services for the router groups: `system.py`, `documents.py`, `queries.py`, and `internal.py`.
  - Move endpoint business logging into app services.
  - Move domain-error to `HTTPException` mapping into app services.
  - Move response DTO construction into app services.
  - Update the stable HTTP contract where doing so improves the boundary.
  - Update evergreen docs to reflect the new contract and architecture truth.
- **What is out of scope**:
  - Business-logic changes inside lifecycle, query, persistence, or worker internals.
  - Unrelated route additions or removals.
  - Broader product-surface redesign outside the endpoints already in play for this workstream.
- **Success conditions**:
  - The router modules are thin and contain only FastAPI metadata, request parsing, DI, and one-call delegation.
  - `src/doc_forge/app/services/*.py` owns endpoint orchestration, logging, exception translation, and response shaping.
  - Any HTTP or OpenAPI-visible changes are reflected in `docs/evergreen/api-contracts.md`.
  - `docs/evergreen/architecture.md` reflects `app/services` as an earned internal seam after implementation.
  - `uv run poe verify` passes.

## 2. Design Decision
- **Decision**: Do not preserve the old split where routers still build API responses. If we are willing to revise HTTP contracts and evergreen docs, the app layer should own the full API-facing boundary for these endpoints.
- **Why**: Keeping DTO assembly in routers would leave the HTTP boundary partially coupled to transport concerns and would make PR 2 a half-step instead of a clean seam.

## 3. Recommended Structure
- **Service classes**:
  - `SystemAppService`
  - `DocumentsAppService`
  - `QueriesAppService`
  - `InternalAppService`
- **Dependency providers**:
  - `get_system_app_service`
  - `get_documents_app_service`
  - `get_queries_app_service`
  - `get_internal_app_service`
- **Responsibility split**:
  - `routers/*.py`: route declarations, request parsing, FastAPI metadata, DI, and direct delegation.
  - `services/*.py`: endpoint orchestration, structured logging, domain-to-HTTP translation, response DTO construction.
  - `deps.py`: wiring for app services and their underlying domain services.

## 4. Boundary Rules
- Routers **must not** import `structlog`.
- Routers **must not** contain business logging.
- Routers **must not** contain `try/except` blocks for domain-error translation.
- Routers **should not** construct response DTOs inline.
- App services **must** be the place where endpoint behavior is assembled from domain services and exposed as API-facing results.
- Domain services remain internal architecture. They should not be reshaped merely to mirror HTTP concerns.

## 5. HTTP Contract Policy
- **Explicit change policy**: Stable HTTP contracts may change in this PR where that change materially improves the app-layer boundary.
- **Required follow-through**:
  - Any route shape, response shape, or documented status-code change must be reflected in `docs/evergreen/api-contracts.md`.
  - OpenAPI-visible changes must stay aligned with actual FastAPI route declarations and response models.
  - If examples in `src/doc_forge/app/api_examples.py` become stale, they must be updated in the same PR.
- **Guardrail**: Contract changes should be deliberate and motivated by the boundary redesign, not incidental cleanup.

## 6. Current-System Notes
- The routers currently contain the orchestration we want to remove:
  - `src/doc_forge/app/routers/documents.py`
  - `src/doc_forge/app/routers/queries.py`
  - `src/doc_forge/app/routers/system.py`
  - `src/doc_forge/app/routers/internal.py`
- Today those routers perform some combination of:
  - request-scoped structured logging
  - domain exception handling and `HTTPException` translation
  - inline response DTO construction
- `src/doc_forge/app/deps.py` currently exposes domain services directly to routers. PR 2 should interpose app services between those routers and domain services.

## 7. Migration Plan
- Create `src/doc_forge/app/services/__init__.py`.
- Create the four app-service modules and move endpoint orchestration into them.
- Add `get_*_app_service` providers to `src/doc_forge/app/deps.py`.
- Refactor the four router modules to inject only app services and delegate immediately.
- Update any affected response models or API-facing schemas in `src/doc_forge/app/schemas.py`.
- Update `docs/evergreen/api-contracts.md` for any contract changes introduced by the new seam.
- Update `docs/evergreen/architecture.md` once the seam exists in code and is validated.

## 8. Implementation Guidance
- App services should instantiate their own module-level logger via `doc_forge.app.logging.get_logger`.
- Log event names and fields should remain stable unless there is a deliberate observability change worth documenting.
- Where a route currently returns domain results directly, prefer moving that adaptation into the app service rather than preserving router-owned shaping.
- Keep `src/doc_forge/app/api.py` unchanged unless a small import or wiring adjustment is genuinely required.

## 9. Risks
- **Scope growth**: This is no longer a transport-only refactor. It is an API-boundary redesign for the affected endpoints.
- **Contract churn**: Response models or documented status codes may change. That is acceptable only if the evergreen docs and OpenAPI stay aligned.
- **Observability drift**: Moving logs out of routers can unintentionally change logger names or fields. Preserve event names and core fields unless a change is intentional.

## 10. Code Mode Handoff
- **Objective**: Implement a full app-layer boundary for the current route groups.
- **First safe increment**: Start with `system.py` and one document endpoint to establish the pattern for DI, logging, exception mapping, and response shaping.
- **Then**: Apply the same pattern to the remaining document, query, and internal routes.
- **Validation focus**:
  - `uv run poe verify`
  - OpenAPI-visible route behavior remains internally consistent
  - Evergreen docs match the implemented HTTP surface
- **Important note**: PR 2 now absorbs the response-boundary cleanup that would otherwise have been deferred. Do not preserve router-owned DTO construction just to honor the earlier split.
