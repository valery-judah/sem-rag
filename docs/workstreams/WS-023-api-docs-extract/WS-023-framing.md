# Framing

## Problem
In `WS-022-api-docs`, rich, realistic JSON payload examples and endpoint descriptions were added directly into the Pydantic models in `src/doc_forge/app/api.py` and `src/doc_forge/query/review.py`. These inline dictionary literals are large, clutter the core model definitions, and caused issues with code linting tools (e.g. `ruff` E501 line length limits). 

## Scope
- Extracting the large JSON dictionary examples from the `json_schema_extra` definitions in `src/doc_forge/app/api.py`.
- Extracting the large JSON dictionary examples from the `json_schema_extra` definitions in `src/doc_forge/query/review.py`.
- Extracting the large descriptions from the `/healthz` and `/readyz` endpoint decorators in `src/doc_forge/app/api.py`.
- Creating companion Python modules (e.g. `_examples.py` or similar) to hold these payload constants.
- Updating the Pydantic models and endpoint decorators to import and use these constants.

## Constraints
- Must not change the output of the OpenAPI schema. The API documentation must look exactly the same before and after the refactor.
- Must not change any runtime routing, parsing, or application logic.
- Must continue to pass all formatting, linting, and type checking (`uv run poe verify`).
- Companion files must be colocated with the files they support (e.g., `src/doc_forge/app/api_examples.py`).

## Input context
- paths:
  - `src/doc_forge/app/api.py`
  - `src/doc_forge/query/review.py`
- read first:
  - `docs/workstreams/WS-022-api-docs/WS-022-framing.md` (for the previous context).

## Key decisions
- **Where do the examples live?** We will use "Companion Python Modules". `api.py` will have `api_examples.py` and `review.py` will have `review_examples.py`.
- **How are variables named?** Upper snake case since they are constants (e.g., `QUERY_ANSWER_RESPONSE_EXAMPLE`).

## Expected outputs
- `src/doc_forge/app/api_examples.py` created and populated.
- `src/doc_forge/query/review_examples.py` created and populated.
- Refactored `src/doc_forge/app/api.py` using imported constants.
- Refactored `src/doc_forge/query/review.py` using imported constants.

## Exit criteria
- All hardcoded dictionary examples and large multiline descriptions are removed from the main `.py` model definitions.
- The `uv run poe verify` suite passes without errors.
- The Swagger UI renders the identical schemas and examples as before.


## Objective
Refactor the OpenAPI JSON schema examples into separate companion Python modules to clean up Pydantic model definitions while maintaining exactly the same generated OpenAPI schema.

## Non-goals
- Changing the actual contents of the mock examples.
- Refactoring models beyond the `model_config` and `json_schema_extra`.
- Moving to a pure schema-first (OpenAPI YAML) framework.

## Relevant context
- components: `app` (FastAPI), `query.review` (Pydantic Models)

## Workflow steps
1. Create `src/doc_forge/app/api_examples.py`.
2. Move endpoint descriptions and `json_schema_extra` dicts from `api.py` into constants in `api_examples.py`.
3. Update `api.py` to import and use the new constants.
4. Create `src/doc_forge/query/review_examples.py`.
5. Move `json_schema_extra` dicts from `review.py` into constants in `review_examples.py`.
6. Update `review.py` to import and use the new constants.
7. Validate with `uv run poe fmt` and `uv run poe verify`.

## Validation and Definition of Done
- Validation: `uv run poe fmt && uv run poe verify` passes completely.
- Definition of Done: The codebase has companion example files and no large dict literals in the main model definitions.

## Linked artifacts
- `docs/workstreams/WS-022-api-docs` (Previous workstream that added the schemas)
