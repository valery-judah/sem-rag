# Framing

## Objective
Extract FastAPI Pydantic request/response models (DTOs) from `src/doc_forge/app/api.py` into a dedicated `schemas.py` file to separate HTTP routing concerns from API payload definitions.

## Problem
`src/doc_forge/app/api.py` currently mixes FastAPI routing and middleware logic with Pydantic model definitions for API payloads. The file is large (almost 1,000 lines), making it harder to navigate. Additionally, keeping API schemas in the routing file prevents reusing them in other modules without importing the entire FastAPI app and its dependencies.

## Scope
- Extracting the 6 inline Pydantic models (`RetrievalQueryRequest`, `QueryAnswerResponse`, `WorkerJobResult`, `ErrorResponse`, `SystemStatusResponse`, `DocumentDetailResponse`) from `api.py`.
- Creating a new `src/doc_forge/app/schemas.py` file to house these models.
- Updating imports in `api.py` to use the new `schemas` module.

## Non-goals
- Redesigning the API contracts or changing existing JSON schemas.
- Modifying domain models or creating new DTOs for endpoints that currently leak domain models directly (e.g., `UploadDocumentResult`).
- Renaming the endpoint paths or changing HTTP status codes.

## Constraints
- The external API contract (OpenAPI docs, validation, HTTP status codes) must remain completely unchanged.
- The extracted models rely on `src/doc_forge/app/api_examples.py` for OpenAPI schema examples. This dependency must follow the models.
- The project's formatting and typing standards must be maintained (`uv run poe verify` must pass).

## Input context
- paths:
  - `src/doc_forge/app/api.py`
  - `src/doc_forge/app/api_examples.py`
- read first: `src/doc_forge/app/api.py`

## Key decisions
- **Target Location**: `src/doc_forge/app/schemas.py` is chosen over `models.py` because it aligns with FastAPI conventions for Pydantic API payloads, distinguishing them from domain/persistence models.

## Expected outputs
- A new `src/doc_forge/app/schemas.py` file containing the extracted models.
- A refactored `src/doc_forge/app/api.py` with the models removed and imports updated.

## Exit criteria
- Framing document is complete and reviewed.
- Implementation plan is documented in `WS-024-plan.md`.

## Workflow steps
1. Frame the workstream scope and constraints (Done).
2. Shape the implementation and validation approach (Done - see plan).
3. Execute and validation the workstream.

## Validation and Definition of Done
- `uv run poe verify` passes completely (including type checking and linting).
- No changes to the OpenAPI schema or API behavior are observed.

## Linked artifacts
- Implementation Plan: `docs/workstreams/WS-024-api-schemas-extract/WS-024-plan.md`