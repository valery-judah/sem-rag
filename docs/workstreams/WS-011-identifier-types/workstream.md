---
artifact_kind: workstream
id: WS-011
title: Identifier Types
work_type: refactor
status: proposed
owner:
created: 2026-03-12
updated: 2026-03-12
---

# Summary
Introduce shared `WorkspaceId` and `DocId` value types in one dedicated module and thread them through the localhost API, lifecycle domain, query domain, artifact store, and persistence seams without changing database column types.

## Objective
Replace the current ad hoc `str` usage for `workspace_id` and `doc_id` with shared identifier types owned by one file, most likely [`src/doc_forge/identifiers.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/identifiers.py), so the codebase gets one validation rule set, clearer type intent, and safer filesystem path construction.

## Non-goals
- No workspace registry or richer workspace domain model.
- No database type migration away from `TEXT`.
- No immediate promotion of `query_id`, `chunk_id`, or `section_id` unless the first pass proves clean.
- No broad package reorganization beyond introducing the shared identifier module.

## Current status
- `workspace_id` and `doc_id` are passed as plain `str` across FastAPI, Pydantic models, repositories, and artifact path builders.
- Validation is inconsistent. Some boundaries require only `min_length=1`, while many internal models accept any `str`.
- `workspace_id` is interpolated directly into filesystem paths, so values containing separators or special path segments can reshape the managed directory layout.
- `doc_id` is generated and compared consistently, but it still lacks a shared nominal type and a single import location.

## Why this refactor exists
- The current codebase duplicates identifier semantics across HTTP inputs, domain models, persistence models, and filesystem storage instead of owning them in one place.
- `workspace_id` has a real correctness and safety problem, not just a style problem:
  - it is accepted from HTTP input with only `min_length=1`
  - it is interpolated into `PurePosixPath` path segments under `raw/`, `extracted/`, and `normalized/`
  - values such as `"."` or `"a/b"` can change the managed path shape even though `_resolve_relative_path(...)` blocks absolute paths and `..`
- `doc_id` is more disciplined operationally because it is generated internally, but it is still just an unowned string type that can be mixed accidentally with `workspace_id`, `query_id`, or other IDs.
- The repo already runs `mypy` in strict mode, so a nominal or semi-nominal shared identifier type can pay off during refactoring and future feature work.

## Recommended decision
Use a thin validated scalar type owned by one module, not a rich domain object.

### Preferred first-pass shape
- Create [`src/doc_forge/identifiers.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/identifiers.py).
- Define `WorkspaceId` and `DocId` there.
- Keep them easy to serialize through Pydantic and SQLAlchemy.
- Keep database columns as `TEXT`.
- Keep runtime behavior string-compatible at API and persistence boundaries.

### Why not a richer wrapper class first
- The current system treats workspaces as opaque scope keys, not as a richer workspace domain with behavior or invariants beyond validation.
- Rich wrapper classes would create immediate friction in:
  - Pydantic model definitions
  - SQL row serialization and deserialization
  - equality checks in tests and fixtures
  - string formatting and path composition
- The first migration should solve the real problems:
  - centralized validation
  - safer path usage
  - clearer type intent
  - reduced `workspace_id`/`doc_id` mixups

### Why not leave them as plain `str`
- Validation would remain duplicated and drift-prone.
- The artifact path issue would remain easy to reintroduce.
- Type checkers would continue to treat all IDs as interchangeable.
- Any future public contract work would still lack a canonical identifier definition.

## Next step
- Define the canonical identifier rules and the exact shape of the shared module before changing call sites.

## Relevant context
- paths:
  - [`src/doc_forge/app/api.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/app/api.py)
  - [`src/doc_forge/lifecycle/service.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/lifecycle/service.py)
  - [`src/doc_forge/stages/register.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/stages/register.py)
  - [`src/doc_forge/corpus/models.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/corpus/models.py)
  - [`src/doc_forge/persistence/models.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/persistence/models.py)
  - [`src/doc_forge/persistence/repositories.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/persistence/repositories.py)
  - [`src/doc_forge/persistence/sqlite_compat.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/persistence/sqlite_compat.py)
  - [`src/doc_forge/query/contracts.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/query/contracts.py)
  - [`src/doc_forge/query/persistence.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/query/persistence.py)
  - [`src/doc_forge/readmodels/documents.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/readmodels/documents.py)
  - [`src/doc_forge/artifacts/store.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/artifacts/store.py)
  - [`src/doc_forge/artifacts/schemas.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/artifacts/schemas.py)
  - [`src/doc_forge/structure/sections.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/structure/sections.py)
- components:
  - FastAPI request models
  - lifecycle registration and persistence
  - query request, run, and snapshot contracts
  - filesystem artifact layout
  - section and chunk identity derivation
- constraints:
  - keep HTTP behavior backward compatible unless a validation tightening is intentional and documented as a contract change
  - keep SQL columns as `TEXT`
  - preserve simple Pydantic serialization and SQLAlchemy row conversion
  - preserve existing generated `doc_<hex>` values
  - preserve existing JSON payload field names and route shapes
- read first:
  - [`docs/evergreen/api-contracts.md`](/Users/val/projects/rag/sem-rag/docs/evergreen/api-contracts.md)
  - [`docs/evergreen/architecture.md`](/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md)

## Migration surface
### Primary code touchpoints
- HTTP boundary:
  - upload form parameter `workspace_id`
  - route path parameters using `doc_id`
  - query request payload `workspace_id`
- Lifecycle and corpus:
  - `Document`
  - `PersistedDocument`
  - `RegisterDocumentRequest`
  - `DocumentLifecycleService.upload_document(...)`
- Query runtime:
  - `QueryRequest`
  - `QueryRun`
  - `CorpusSnapshot`
  - review and replay read models
- Persistence:
  - document repository protocols and implementations
  - query persistence row mapping
  - sqlite compatibility helpers
- Filesystem artifacts:
  - raw path construction
  - extracted and normalized path construction
  - `RawArtifactRef`

### Secondary code touchpoints
- section IDs currently incorporate `document.doc_id`, so `DocId` string compatibility matters for downstream derived IDs
- query selection, support assessment, and context assembly use `doc_id` heavily for grouping and deterministic ordering
- e2e fixtures, helper factories, and diagnostics interpolate `doc_id` into logs, filenames, and assertions

## Validation gap summary
- `workspace_id` currently has weak validation at the FastAPI form boundary and query contracts.
- core lifecycle and persistence models accept raw `str` without a shared validator.
- `doc_id` is structurally trusted because it is generated in service code, but its type identity is still not modeled explicitly.
- no shared module currently defines what a valid workspace or document identifier is.

## Path-safety reasoning
- `workspace_id` is used as a path segment under:
  - `raw/{workspace_id}/{doc_id}/source.*`
  - `extracted/{workspace_id}/{doc_id}/extracted.json`
  - `normalized/{workspace_id}/{doc_id}/normalized.json`
- `_resolve_relative_path(...)` prevents absolute paths and `..`, but it does not prevent path-shape drift caused by embedded separators or ambiguous segments in the identifier itself.
- Examples that should be treated as invalid for `WorkspaceId`:
  - `"."`
  - `".."`
  - `"a/b"`
  - `"a\\b"`
  - values that become empty after trim
  - values with leading or trailing whitespace

## Compatibility notes
- The stable localhost HTTP API is now documented in evergreen docs, so input-validation tightening can be a contract change if it rejects values that previously passed.
- In practice, rejecting malformed workspace IDs is still desirable, but the migration should state that behavior change explicitly.
- This refactor should not require database migrations if SQL columns remain `TEXT` and row payloads remain plain strings on persistence boundaries.
- This refactor should not change API field names such as `workspace_id` and `doc_id`.

## Workflow steps
1. Introduce `src/doc_forge/identifiers.py` with shared `WorkspaceId` and `DocId` definitions plus one canonical validation rule set.
2. Decide the representation strategy:
   - preferred first pass: thin validated scalar aliases compatible with Pydantic and static typing
   - defer richer wrapper classes unless a real behavior need appears
3. Add focused tests for identifier validation and path-safety before broad annotation churn.
4. Replace public and transport boundaries first:
   - FastAPI form/body inputs
   - request and response models
   - lifecycle and query contract models
5. Replace internal domain and persistence annotations next:
   - corpus models
   - persisted models
   - repository protocols and implementations
   - artifact refs and artifact store method signatures
6. Tighten path safety:
   - reject `/`, `\\`, `.`, `..`, and ambiguous whitespace for `WorkspaceId`
   - keep `DocId` compatible with existing generated `doc_<hex>` values
7. Update fixtures and tests to use the shared types while preserving existing payload shapes.
8. Reassess whether `query_id` should follow in a second pass after `WorkspaceId` and `DocId` land cleanly.

## Proposed implementation phases
### Phase 1: shared module and focused validation
- add `identifiers.py`
- add unit tests for accepted and rejected values
- update artifact path tests to prove invalid `WorkspaceId` values fail early

### Phase 2: API and contract adoption
- update FastAPI parameters and top-level Pydantic models
- update query request, run, and snapshot contracts
- verify JSON serialization remains unchanged

### Phase 3: lifecycle and persistence adoption
- update corpus and persisted models
- update repository interfaces
- update sqlite compatibility helpers and row mapping

### Phase 4: fixtures and cleanup
- normalize helper factories and tests to import the shared types where useful
- remove duplicated inline validation
- document whether `query_id` should use the same pattern later

## Proposed identifier rules
- `WorkspaceId`
  - required
  - trimmed, non-empty
  - path-segment safe
  - opaque scope key with no extra behavior
- `DocId`
  - required
  - trimmed, non-empty
  - compatible with current generated values such as `doc_<hex>`
  - no path separators

## Open decisions
- whether the shared types should be:
  - pure constrained aliases
  - aliases plus helper constructors
  - `NewType` layered over validation aliases for stronger static separation
- whether `DocId` should be path-safe to the same degree as `WorkspaceId` or only reject separators
- whether HTTP boundaries should trim input silently or reject surrounding whitespace explicitly
- whether `query_id` should be pulled into the same module immediately after `DocId`

## Risks
- Tightening validation can reject previously accepted but poor-quality input values.
- Nominal typing can create high annotation churn across tests and helper factories.
- Wrapper classes would increase friction in Pydantic, SQL serialization, and equality checks, so the first pass should stay thin.
- The repo has a wide test surface using string literals for IDs, so a large mechanical patch can hide behavior regressions if not phased carefully.
- `doc_id` participates in derived IDs such as section IDs, so any normalization beyond validation could create subtle downstream mismatches.

## Acceptance criteria
- one shared identifier module exists and is the only owner of `WorkspaceId` and `DocId` validation rules
- API payload field names remain unchanged
- SQL schema and stored values remain string-backed
- invalid `WorkspaceId` values that would distort artifact paths fail before path creation
- existing generated `doc_<hex>` values remain valid
- type checks pass with the new annotations
- repository, lifecycle, query, artifact, and API tests still pass

## Validation
- `make fmt-check`
- `make lint`
- `make type`
- `make test`

## Proving tests to touch or add
- API and route behavior:
  - [`tests/app/test_documents_api.py`](/Users/val/projects/rag/sem-rag/tests/app/test_documents_api.py)
  - [`tests/app/test_runtime_api.py`](/Users/val/projects/rag/sem-rag/tests/app/test_runtime_api.py)
- artifact layout and storage:
  - [`tests/artifacts/test_raw_artifact_store.py`](/Users/val/projects/rag/sem-rag/tests/artifacts/test_raw_artifact_store.py)
  - [`tests/artifacts/test_extracted_artifact_store.py`](/Users/val/projects/rag/sem-rag/tests/artifacts/test_extracted_artifact_store.py)
  - [`tests/artifacts/test_normalized_artifact_store.py`](/Users/val/projects/rag/sem-rag/tests/artifacts/test_normalized_artifact_store.py)
- lifecycle and registration:
  - [`tests/stages/test_register_stage.py`](/Users/val/projects/rag/sem-rag/tests/stages/test_register_stage.py)
  - [`tests/lifecycle/test_service.py`](/Users/val/projects/rag/sem-rag/tests/lifecycle/test_service.py)
- query and read-model seams:
  - [`tests/readmodels/test_queryable_corpus_read_model.py`](/Users/val/projects/rag/sem-rag/tests/readmodels/test_queryable_corpus_read_model.py)
  - [`tests/query/test_query_service_prepare.py`](/Users/val/projects/rag/sem-rag/tests/query/test_query_service_prepare.py)
  - [`tests/query/test_query_retrieval.py`](/Users/val/projects/rag/sem-rag/tests/query/test_query_retrieval.py)
- persistence:
  - [`tests/persistence/test_document_repository.py`](/Users/val/projects/rag/sem-rag/tests/persistence/test_document_repository.py)

## Linked artifacts
- [`docs/evergreen/api-contracts.md`](/Users/val/projects/rag/sem-rag/docs/evergreen/api-contracts.md)
- [`docs/evergreen/architecture.md`](/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md)
