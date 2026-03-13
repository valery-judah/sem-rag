# Agent Routing

**Status:** Verified
**Last verified:** 2026-03-11

## Purpose
This file is the coding-agent routing map for `doc_forge`.

Use it to answer practical repo-navigation questions quickly:

- which doc owns the semantics I am about to change?
- which code path owns the behavior?
- which tests prove the seam is real?
- what neighboring files or docs are likely to be affected?

This file is not the canonical architecture statement.
For durable system shape, boundaries, and the gap to MVP, use [`docs/evergreen/architecture.md`](./architecture.md).
For the broader documentation index and read-order map, use [`docs/README.md`](../README.md).

## When To Use
- Starting work on a subsystem
- Figuring out which file owns a behavior before editing
- Finding the proving tests for an implemented seam
- Checking likely downstream docs or tests after a code change

## Canonical Doc Owners
- Product scope: `docs/evergreen/mvp.md`
- Current architecture and durable boundaries: `docs/evergreen/architecture.md`
- Stable localhost HTTP and OpenAPI contract: `docs/evergreen/api-contracts.md`
- Commands and validation guidance: `docs/evergreen/runbook.md`
- Evaluation semantics: `docs/evergreen/eval-vocabulary.md`, `docs/evergreen/eval-support-semantics.md`, `docs/evergreen/eval-scenario-taxonomy.md`, and `docs/evergreen/eval-failure-taxonomy.md`
- Workflow rationale and promotion rules: `docs/delivery/workflow.md` as reference only
- Execution history and prior framing: `docs/workstreams/`

Current Implementation Seams:
- `src/doc_forge/query/`: `Implemented internal`
- `src/doc_forge/readmodels/`: `Implemented internal`
- `src/doc_forge/corpus/`: `Implemented internal`
- `src/doc_forge/app/`: `Implemented internal`
- `src/doc_forge/artifacts/`: `Implemented internal`
- `src/doc_forge/stages/`: `Implemented internal`
- `src/doc_forge/extractors/`: `Implemented internal`
- `src/doc_forge/normalizers/`: `Implemented internal`
- `src/doc_forge/structure/`: `Implemented internal`
- `src/doc_forge/chunking/`: `Implemented internal`
- `src/doc_forge/indexing/`: `Implemented internal`
- `src/doc_forge/persistence/`: `Implemented internal`
- `src/doc_forge/evaluation/`: `Implemented internal`
- `src/doc_forge/devtools/secret_scan.py`: `Implemented internal`

## Implementation Map
- `src/doc_forge/query/contracts.py`, `src/doc_forge/query/interpretation.py`, `src/doc_forge/query/retrieval.py`, `src/doc_forge/query/context_assembly.py`, `src/doc_forge/query/service.py`, `src/doc_forge/query/stages/`, `src/doc_forge/query/persistence.py`, and `src/doc_forge/query/trace.py`: internal query runtime through Stage 5. Open when changing query run state, query-time snapshot semantics, interpreted-query shape, retrieval behavior, context assembly, stage execution, or persisted stage traces.
- `src/doc_forge/readmodels/documents.py`: query-facing corpus read model over lifecycle persistence. Open when changing `READY`-only queryability, snapshot membership capture, fixed-snapshot section/chunk reads, or embedded-chunk retrieval reads.
- `src/doc_forge/corpus/models.py`, `src/doc_forge/lifecycle/status.py`, and `src/doc_forge/lifecycle/state_machine.py`: internal corpus, provenance, answer, and lifecycle seams. Open when changing document, chunk, citation, answer, or processing-state semantics in code.
- `src/doc_forge/app/api.py`, `src/doc_forge/app/deps.py`, and `src/doc_forge/app/settings.py`: internal FastAPI runtime and dependency wiring. Open when changing intake/status/retry/query route shape, dependency assembly, or runtime settings.
- `src/doc_forge/lifecycle/service.py`, `src/doc_forge/lifecycle/orchestrator.py`, and `src/doc_forge/lifecycle/worker.py`: transport-thin lifecycle coordination, queued orchestration, retry behavior, and worker execution. Open when changing document-level control flow or failure handling.
- `src/doc_forge/stages/`, `src/doc_forge/extractors/`, `src/doc_forge/normalizers/`, `src/doc_forge/structure/`, `src/doc_forge/chunking/`, and `src/doc_forge/indexing/`: executable lifecycle stages from extraction through readiness. Open when changing stage invariants, format-specific transforms, vector publication, or readiness semantics.
- `src/doc_forge/artifacts/store.py` and `src/doc_forge/artifacts/schemas.py`: filesystem-backed artifact persistence for raw, extracted, and normalized payloads. Open when changing managed artifact paths or storage payload shapes.
- `src/doc_forge/persistence/sqlite_compat.py`: SQLite compatibility round-trip layer for `Document`, `Section`, and `Chunk`. Open when changing persisted fields, linkage rules, or existing internal repository semantics.
- `src/doc_forge/persistence/models.py`, `src/doc_forge/persistence/jobs.py`, `src/doc_forge/persistence/repositories.py`, and `src/doc_forge/persistence/migrations/`: lifecycle metadata persistence, Alembic-backed migrations, and Postgres-oriented repository seams. Open when changing durable document/job/event storage or migration workflow.
- `src/doc_forge/evaluation/models.py`, `src/doc_forge/evaluation/dataset.py`, `src/doc_forge/evaluation/runner.py`, `src/doc_forge/evaluation/systems.py`, and `src/doc_forge/evaluation/fixtures.py`: deterministic harness scaffolding. Open when changing baseline evaluation cases, provenance checks, or synthetic seam behavior.
- `src/doc_forge/devtools/secret_scan.py`: repo safety tooling. Open when changing secret-pattern detection, reporting, or staged-vs-repo scanning behavior.

## Edit Starting Points


For query runtime changes:
- open `src/doc_forge/query/service.py`
- then inspect `src/doc_forge/query/contracts.py`, `src/doc_forge/query/interpretation.py`, `src/doc_forge/query/retrieval.py`, `src/doc_forge/query/stages/interpret.py`, `src/doc_forge/query/stages/retrieve.py`, and `src/doc_forge/query/persistence.py`
- then inspect `src/doc_forge/readmodels/documents.py`
- then inspect `src/doc_forge/app/api.py` and `src/doc_forge/app/deps.py`
- then inspect `tests/readmodels/test_queryable_corpus_read_model.py`, `tests/query/test_query_service_prepare.py`, `tests/query/test_interpretation.py`, `tests/query/test_query_retrieval.py`, `tests/query/test_query_context_assembly.py`, `tests/query/test_query_service_interpret.py`, `tests/query/test_query_service_retrieve.py`, and `tests/app/test_runtime_api.py`
- if the change would promote query request, snapshot, interpreted-query, or route payloads into a supported downstream interface, update `docs/evergreen/api-contracts.md` first

For internal contract or lifecycle changes:
- open `src/doc_forge/corpus/models.py`
- then inspect `src/doc_forge/lifecycle/status.py` and `src/doc_forge/lifecycle/state_machine.py`
- then inspect `tests/contract/test_contract_models.py`
- then inspect `tests/contract/test_lifecycle_state_machine.py`
- then inspect `tests/contract/test_contract_seam_compat.py`
- if semantics overlap evaluation labels, normalize against the evergreen eval docs instead of inventing local wording

For lifecycle runtime changes:
- open `src/doc_forge/app/api.py`
- then inspect `src/doc_forge/app/deps.py` and `src/doc_forge/app/settings.py`
- then inspect `src/doc_forge/lifecycle/service.py`, `src/doc_forge/lifecycle/orchestrator.py`, and `src/doc_forge/lifecycle/worker.py`
- then inspect the relevant stage module under `src/doc_forge/stages/`
- then inspect `tests/app/test_documents_api.py`, `tests/stages/`, `tests/lifecycle/`, and `tests/pipeline/`
- if the change would create a stable external API, update `docs/evergreen/api-contracts.md` first instead of treating the internal route as public

For persistence changes:
- open `src/doc_forge/persistence/`
- then inspect `tests/persistence/`
- then inspect `src/doc_forge/corpus/` and `src/doc_forge/lifecycle/`

For evaluation harness changes:
- open `src/doc_forge/evaluation/runner.py`
- then inspect `src/doc_forge/evaluation/models.py`, `src/doc_forge/evaluation/dataset.py`, and `src/doc_forge/evaluation/fixtures.py`
- then inspect `tests/test_evaluation_harness.py`
- if you are changing support-state, scenario, citation, or failure meanings, open the evergreen eval docs first

For repo devtool changes:
- open `src/doc_forge/devtools/secret_scan.py`
- then inspect `tests/test_secret_scan.py`

## Validation Routes
Use these proof points to distinguish implemented seams from doc-only intent:

- Query boundary, interpretation, retrieval, selection, and context runtime: `tests/readmodels/test_queryable_corpus_read_model.py`, `tests/query/test_query_service_prepare.py`, `tests/query/test_interpretation.py`, `tests/query/test_query_retrieval.py`, `tests/query/test_query_context_assembly.py`, `tests/query/test_query_service_interpret.py`, `tests/query/test_query_service_retrieve.py`, `tests/app/test_runtime_api.py`
- Contract models and lifecycle rules: `tests/contract/test_contract_models.py`, `tests/contract/test_lifecycle_state_machine.py`, `tests/contract/test_contract_seam_compat.py`
- Lifecycle runtime and operator routes: `tests/app/test_documents_api.py`, `tests/lifecycle/test_worker.py`, `tests/pipeline/test_markdown_to_ready.py`, `tests/pipeline/test_pdf_to_ready.py`, `tests/pipeline/test_retry_recovery.py`
- Artifact storage: `tests/artifacts/test_raw_artifact_store.py`, `tests/artifacts/test_extracted_artifact_store.py`, `tests/artifacts/test_normalized_artifact_store.py`
- Stage invariants: `tests/stages/test_register_stage.py`, `tests/stages/test_extract_stage_markdown.py`, `tests/stages/test_extract_stage_pdf.py`, `tests/stages/test_normalize_stage_markdown.py`, `tests/stages/test_normalize_stage_pdf.py`, `tests/stages/test_section_stage.py`, `tests/stages/test_chunk_stage.py`, `tests/stages/test_index_stage.py`, `tests/stages/test_ready_stage.py`
- Persistence linkage and round-trips: `tests/persistence/test_document_repository.py`, `tests/persistence/test_section_repository.py`, `tests/persistence/test_chunk_repository.py`, `tests/persistence/test_index_entry_repository.py`, `tests/persistence/test_chunk_embedding_repository.py`, `tests/persistence/test_replace_on_retry.py`
- Deterministic evaluation behavior and provenance checks: `tests/test_evaluation_harness.py`, `src/doc_forge/evaluation/fixtures.py`
- Secret scanning behavior: `tests/test_secret_scan.py`

## Change Impact
- Query runtime changes may affect `src/doc_forge/readmodels/`, `src/doc_forge/query/`, `src/doc_forge/app/api.py`, `src/doc_forge/app/deps.py`, `tests/query/`, `tests/readmodels/`, and `tests/app/test_runtime_api.py`.
- Contract or lifecycle changes may affect `src/doc_forge/persistence/`, `src/doc_forge/evaluation/fixtures.py`, `tests/contract/`, `tests/persistence/`, and `tests/test_evaluation_harness.py`.
- Persistence changes may require matching updates to contract fields, ordering assumptions, integrity checks, and migrations.
- Evaluation harness changes may require matching updates to baseline cases, seam fixtures, and evergreen semantic docs if the change is semantic rather than mechanical.
- Semantic doc changes should normalize against the owning evergreen doc instead of inventing parallel labels locally.

## Guardrails
- Do not treat this file as the canonical architecture statement. It is a routing and implementation map.
- Do not infer stable public API from any internal route, package export, fixture, or repository seam unless `docs/evergreen/api-contracts.md` says so.
- Do not promote a seam here unless it is implemented and backed by current validation surfaces.
