# WS-025 Architect Handoff: API Decoupling Finalization

## Problem Framing
PR2 and PR3 introduced the router-thinning and app-DTO boundary patterns. However, `src/doc_forge/app/schemas.py` still leaks internal domain models into the OpenAPI layer by importing them from `doc_forge.query.*`, `doc_forge.lifecycle.*`, `doc_forge.corpus.*`, etc. This means any change to a domain model automatically breaks the API contract, defeating the purpose of the decoupled boundary. Additionally, the `readyz` endpoint in `src/doc_forge/app/routers/system.py` still performs exception-to-HTTP mapping in the router rather than the service.

**Objective:** Cleanly separate the HTTP API DTO boundary from the domain models, and finalize the `readyz` route thinning.

## Constraints & Assumptions
- **Do not change business logic or behavior.**
- Preserve the existing route paths and intended behavior.
- Use explicit DTO mapping over implicit passthroughs.
- `src/doc_forge/app/schemas.py` MUST NOT import anything from `doc_forge.query`, `doc_forge.lifecycle`, `doc_forge.corpus`, `doc_forge.indexing`, `doc_forge.persistence`.

## Recommended Design

### 1. DTO Independence (`src/doc_forge/app/schemas.py`)
- Remove all imports from internal domain modules (`doc_forge.query.*`, `doc_forge.corpus.*`, `doc_forge.indexing.*`, `doc_forge.persistence.*`, `doc_forge.lifecycle.*`).
- Redefine enumerations and structures needed for the API within `schemas.py` or a dedicated app DTO module (e.g., `AppSourceType`, `AppVectorSearchHit`, `AppCorpusSnapshot`, `AppFinalQueryArtifacts`, `AppQueryTraceBundle`, etc.). If names don't conflict, you may keep the original names (e.g., `SourceType` redefined in `schemas.py`), but adding an `App` prefix or similar might help differentiate them in service mapping logic. Given they are nested, redefining them exactly as they are named, but inside `schemas.py`, is preferred.
- Update `UploadDocumentResponse`, `DocumentStatusResponse`, `QueryRunSummaryResponse`, `QueryTraceReviewResponse`, etc., to use these newly defined local DTO types instead of internal domain types.

### 2. Service Boundary Mapping (`src/doc_forge/app/services/*.py`)
- The app services (`queries.py`, `documents.py`, `internal.py`) act as the boundary mappers.
- They must receive internal models from the domain services and explicitly construct the app DTOs from `schemas.py` before returning them to the router.
- Use `TypeAdapter(AppDTO).validate_python(internal_model)` or explicit `AppDTO(**internal_model.model_dump())` mapping where appropriate to translate the deep structures, ensuring full isolation.

### 3. `readyz` Refactor (`src/doc_forge/app/routers/system.py` & `src/doc_forge/app/services/system.py`)
- Move the `try-except` block from `router.get("/readyz")` to `check_readiness()` in `SystemAppService`.
- In the service, when catching `LifecycleReadinessFailedError`, log the failure and `raise HTTPException(...)` directly using a bare `raise` (i.e. `raise HTTPException(...) from e` or `raise HTTPException(...)` inside the except block) so the traceback context is preserved.

## Code Mode Handoff
1. **First safe increment:** Copy all necessary enums and nested structures (like `CorpusSnapshot`, `FinalQueryArtifacts`, `VectorSearchHit`, etc.) into `src/doc_forge/app/schemas.py`. Remove the internal imports. Ensure `schemas.py` passes syntax checks.
2. **Second increment:** Update `queries.py`, `documents.py`, `internal.py` services to explicitly map the domain models to the new DTOs.
3. **Third increment:** Refactor the `readyz` endpoint in `system.py` to move the exception mapping from the router to the service.
4. **Validation:** Run `uv run poe verify`. Check that the generated OpenAPI schema (`docs/api/openapi.json` if it generates, or the FastAPI app itself) no longer leaks internal models.
