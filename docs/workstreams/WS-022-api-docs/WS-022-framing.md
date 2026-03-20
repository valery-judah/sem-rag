# Framing

## Problem
The generated OpenAPI/Swagger documentation lacks rich JSON payload examples for several core models (e.g., `QueryAnswerResponse`, `DocumentDetailResponse`, `ErrorResponse`, `WorkerJobResult`, `SystemStatusResponse`). Additionally, a few system endpoints (`/healthz`, `/readyz`) are missing consistent metadata (`summary`, `description`, explicit `responses`). This creates a sub-optimal developer experience when exploring the API interactively.

## Scope
- Adding `json_schema_extra` to Pydantic models exposed in the FastAPI application (`src/doc_forge/app/api.py` and imported schemas like those in `src/doc_forge/query/review.py`) where they are missing.
- Adding `summary`, `description`, and explicit `responses` to the `/healthz` and `/readyz` endpoints.
- Focusing purely on OpenAPI generation enhancements.

## Constraints
- Do not change any existing field names, types, or routing logic.
- Rely strictly on Pydantic V2's `json_schema_extra` or the `example` kwarg within `Field()` to inject examples without altering runtime validation behavior.

## Input context
- paths: `src/doc_forge/app/api.py`, `src/doc_forge/query/review.py`, `docs/evergreen/api-contracts.md`
- read first: Review current Pydantic models in `src/doc_forge/app/api.py` and `src/doc_forge/query/review.py` to identify missing examples.

## Key decisions
- The standard pattern will be using `json_schema_extra={"example": ...}` in `Field` declarations for individual fields, or defining it in the model's `model_config` for complete payload examples where appropriate.

## Expected outputs
- Updated `src/doc_forge/app/api.py` and `src/doc_forge/query/review.py` containing enriched OpenAPI metadata.
- A fully populated Swagger UI (at `http://localhost:8000/docs`) where every endpoint has clear descriptions and realistic payload examples.

## Exit criteria
- All response models and request bodies exposed on the FastAPI router have concrete examples in the Swagger UI.
- The `/healthz` and `/readyz` endpoints have matching `summary`, `description`, and `responses` definitions.

## Objective
Ensure every endpoint and schema exposed in the local Swagger UI has a concrete, realistic JSON payload example and clear description to reduce friction for developers testing the API.

## Non-goals
- Restructuring the API paths or request/response structures.
- Adding new functional endpoints.
- Documenting internal persistence or subsystem models that are not exposed via the HTTP boundary.

## Relevant context
- paths: `src/doc_forge/app/api.py`, `src/doc_forge/query/review.py`
- components: FastAPI Routers, Pydantic Models
- constraints: Adhere strictly to FastAPI and Pydantic V2 best practices.
- read first: Current implementation of `/healthz`, `/readyz`, and models like `QueryAnswerResponse` and `QueryRunReviewSummary`.

## Workflow steps
1. Audit models in `api.py` and `review.py` for missing `json_schema_extra` examples.
2. Update `QueryAnswerResponse`, `WorkerJobResult`, `ErrorResponse`, `SystemStatusResponse`, and `DocumentDetailResponse` in `api.py` with realistic examples.
3. Update `QueryRunReviewSummary`, `QueryTraceReview`, and `QueryCitationReview` in `review.py` with realistic examples.
4. Update `/healthz` and `/readyz` route decorators with missing `summary`, `description`, and explicit `responses` (e.g., matching the 500 error response structure used by other endpoints).
5. Validate changes by running the local API (`uv run poe run-api`) and inspecting the Swagger UI at `http://127.0.0.1:8000/docs`.

## Validation and Definition of Done
- `uv run poe verify` passes (no typing or format violations).
- Starting the API does not throw Pydantic initialization errors.
- Visual inspection of `http://127.0.0.1:8000/docs` confirms the new examples are visible.

## Linked artifacts
- `docs/workstreams/WS-010-document-lifecycle-refactoring/workstream.md` (which initially established the need for rich examples)
- `docs/adrs/ADR-0001-openapi-swagger-exposure.md` (which dictates Swagger UI availability)
