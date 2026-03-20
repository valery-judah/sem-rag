# Framing

## Problem
The documentation currently lacks practical usage examples for the standard API workflow. Specifically, there are no `curl` or payload examples demonstrating how to upload a document (`POST /documents` requiring a multipart form with `workspace_id` and `file`) and how to perform a query (`POST /queries` requiring a JSON body with `workspace_id` and `question`). This gap increases the friction for developers attempting to test or integrate with the API.

## Scope
- Document the standard user journey: Uploading a document and then querying it.
- Create practical, copy-pasteable `curl` examples for `POST /documents` and `POST /queries`.
- Describe the required payloads, content types (multipart form vs. JSON), and expected responses.
- Integrate these examples into the appropriate evergreen documentation (e.g., `docs/evergreen/api-contracts.md`, `docs/evergreen/runbook.md`, or the main `README.md`).

## Constraints
- The documented examples must accurately reflect the current routing and payload expectations defined in the FastAPI application (`src/doc_forge/app/api.py`).
- Examples must be syntactically valid `curl` commands.

## Input context
- paths: `src/doc_forge/app/api.py`, `docs/evergreen/api-contracts.md`, `README.md`
- read first: Review current endpoint definitions in `src/doc_forge/app/api.py` to confirm field names and response shapes.

## Key decisions
- **Documentation Location**: Determine whether these examples belong in a dedicated "Getting Started" section in the `README.md`, an updated `docs/evergreen/api-contracts.md`, or a new dedicated guide. 

## Expected outputs
- Updated markdown documentation containing clear examples of how to invoke the core API endpoints.
- Concrete `curl` snippets for:
  - Document Upload: `POST /documents` (multipart/form-data with `workspace_id` and `file`).
  - Query: `POST /queries` (application/json with `workspace_id` and `question`).

## Exit criteria
- The `curl` examples are documented and confirmed to match the API signature.
- The documentation changes are merged.

## Objective
To provide clear, practical, and executable examples for the core API workflows (uploading and querying documents) so that consumers can easily understand how to interact with the API.

## Non-goals
- Documenting every possible configuration, edge case, or error response for these endpoints.
- Replacing or modifying the automated OpenAPI/Swagger generation provided by FastAPI.
- Changing the actual API implementation or endpoints.

## Relevant context
- Placeholder section. Fill later when relevant context becomes clearer.
- paths: `src/doc_forge/app/api.py`
- components: FastAPI Routers
- constraints: Existing schema validation requirements
- read first: Current implementation of `/documents` and `/queries` endpoints.

## Workflow steps
1. Inspect `src/doc_forge/app/api.py` and related schemas to verify the exact payload requirements for `/documents` and `/queries`.
2. Decide on the best location to host the practical API usage guide (e.g., `docs/evergreen/api-contracts.md` or a new API quickstart guide).
3. Draft the `curl` examples for `POST /documents`, explicitly detailing the `multipart/form-data` structure (`workspace_id` and `file`).
4. Draft the `curl` examples for `POST /queries`, explicitly detailing the `application/json` body (`workspace_id` and `question`).
5. Include example JSON responses for both commands to illustrate success.
6. Review and commit the documentation updates.

## Validation and Definition of Done
- The newly written `curl` commands have been reviewed against the current codebase implementation for accuracy.
- Documentation successfully builds/renders locally without markdown formatting errors.
- The core "upload" and "query" user journey is clearly explained step-by-step.

## Linked artifacts
- None yet.
