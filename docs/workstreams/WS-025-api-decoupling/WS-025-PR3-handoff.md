# PR 3: Internal Service Model Cleanup and Boundary Hardening (WS-025)

## 1. Problem Framing
- **What problem is being solved**: After PR 2, the app layer should own the API-facing boundary. PR 3 finishes the cleanup by removing leftover HTTP/OpenAPI concerns from internal lifecycle and query models so internal packages no longer carry public-contract baggage.
- **What PR 3 now does**: Strip app- and OpenAPI-facing metadata out of internal result models, clarify internal naming where needed, and harden the separation between internal service models and app-owned DTOs.
- **What is in scope**:
  - Remove `json_schema_extra` examples and similar OpenAPI-oriented metadata from internal models.
  - Remove or reduce HTTP-contract-oriented `Field` descriptions where they exist only for public schema generation.
  - Rename internal result models if needed to avoid confusion with app DTOs.
  - Perform final cleanup of direct app-schema leakage into lifecycle/query packages.
  - Keep internal models lightweight and app-agnostic while preserving internal validation that actually protects runtime invariants.
- **What is out of scope**:
  - Business-logic changes in lifecycle processing, query execution, persistence, or worker behavior.
  - Reopening router/app-service ownership decisions settled in PR 2.
  - Deliberate HTTP contract redesign. PR 3 should preserve the HTTP behavior established by PR 2.
- **Success conditions**:
  - Internal lifecycle/query packages no longer present themselves as OpenAPI response-model owners.
  - App-owned DTOs remain the only HTTP-facing models for stable routes.
  - Internal model naming is clearer where previously ambiguous.
  - `uv run poe verify` passes.

## 2. Design Decision
- **Decision**: PR 3 is a boundary-hardening cleanup, not another API redesign pass.
- **Why**: PR 2 should already have moved the API-facing boundary into `src/doc_forge/app/`. PR 3 should now simplify internal packages to reflect that fact, not blur the boundary again.

## 3. Recommended Cleanup Targets
- **Lifecycle package**:
  - `src/doc_forge/lifecycle/service.py`
  - Focus on models such as `UploadDocumentResult`, `DocumentStatusResult`, `RetryDocumentResult`, `RetrievalQueryResult`, and `DocumentArtifactRefs` if they still carry OpenAPI examples or app-contract wording.
- **Query package**:
  - `src/doc_forge/query/review.py`
  - `src/doc_forge/query/contracts.py`
  - Focus on review/query request models that still include OpenAPI examples or descriptions that exist only to serve the HTTP layer.
- **App layer follow-through**:
  - `src/doc_forge/app/schemas.py`
  - `src/doc_forge/app/services/*.py`
  - Any app mappers introduced in PR 2
  - Use these modules to absorb any public-schema metadata removed from internal packages.

## 4. Boundary Rules
- Internal packages **must not** own OpenAPI examples for stable HTTP routes.
- Internal packages **must not** be named or shaped as if they are the public contract when app DTOs already exist.
- Internal packages **may** keep Pydantic validation and `Field(...)` usage where it enforces internal invariants or readability, but not where it exists only for public schema generation.
- App packages **must** remain the owner of HTTP-facing examples, descriptions, and response DTOs.
- PR 3 **should not** require routers to change behavior beyond import or wiring fallout from cleanup.

## 5. Current-System Notes
- Concrete cleanup candidates already visible in repo truth include:
  - `src/doc_forge/lifecycle/service.py`, where several internal result models still carry `json_schema_extra={"example": ...}` and HTTP-oriented field descriptions.
  - `src/doc_forge/query/review.py`, where persisted review models still include schema examples intended for response documentation.
  - `src/doc_forge/query/contracts.py`, where `QueryRequest` still includes example-bearing schema metadata even though request DTO ownership should live in the app layer after PR 2.
- These are not all necessarily bugs by themselves, but they are boundary leakage if PR 2 has already established app-owned DTOs for the stable API.

## 6. Implementation Guidance
- Start from the principle that internal models are allowed to be Pydantic models, but they should read as internal runtime models rather than HTTP artifacts.
- Preserve internal validation that protects runtime correctness.
- Remove example payloads and HTTP-contract phrasing from internal models when that metadata no longer serves internal code.
- If an internal model name is now misleading because the app layer owns the public DTO with the same conceptual role, rename the internal model to make the distinction obvious.
- Prefer small, explicit mapper or adapter updates in the app layer over keeping internal models schema-heavy for convenience.
- Only update evergreen docs in PR 3 if the cleanup reveals an architectural truth not already captured by the PR 2 documentation updates.

## 7. Migration Plan
- Audit `src/doc_forge/lifecycle/service.py` for OpenAPI-facing metadata and remove it where it no longer belongs.
- Audit `src/doc_forge/query/review.py` and `src/doc_forge/query/contracts.py` for the same leakage.
- Rename internal result/request models where ambiguity remains after metadata cleanup.
- Update app-layer services, schemas, and mappers to keep the stable API boundary intact.
- Adjust tests so app-layer tests assert the public contract and internal tests assert internal model behavior separately.

## 8. Risks
- **Over-cleanup**: Removing too much `Field(...)` metadata can accidentally weaken useful internal validation. Keep invariant-enforcing validation.
- **Name churn**: Internal renames can create broad but mechanical edits. Keep them narrow and coherent.
- **Boundary backslide**: If PR 3 solves convenience problems by reusing internal models at the HTTP layer, it defeats the point of PR 2. Avoid that shortcut.

## 9. Validation Focus
- `uv run poe verify`
- Stable-route tests continue to pass against app-owned DTOs.
- Internal lifecycle/query tests still pass with cleaned-up internal models.
- No stable route response model points back at internal lifecycle/query types just because PR 3 cleaned them up.

## 10. Code Mode Handoff
- **Objective**: Remove HTTP/OpenAPI leakage from internal lifecycle/query models after PR 2 has established the app boundary.
- **First safe increment**: Clean up `src/doc_forge/lifecycle/service.py` result models and fix any app-layer fallout.
- **Then**: Clean up `src/doc_forge/query/review.py` and `src/doc_forge/query/contracts.py`, keeping app DTO ownership intact.
- **Important note**: If PR 2 did not fully move a stable route onto app-owned DTOs, fix that boundary first in the smallest possible way before removing metadata from the internal model underneath it.
