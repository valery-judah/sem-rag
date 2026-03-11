# Agent Routing

**Status:** Verified
**Last verified:** 2026-03-11

## Purpose
This file is the coding-agent routing map for `parity`.

Use it to answer practical repo-navigation questions quickly:

- which doc owns the semantics I am about to change?
- which code path owns the behavior?
- which tests prove the seam is real?
- what neighboring files or docs are likely to be affected?

This file is not the canonical architecture statement.
For durable system shape, boundaries, and the gap to MVP, use [`docs/evergreen/architecture.md`](./architecture.md).

## When To Use
- Starting work on a subsystem
- Figuring out which file owns a behavior before editing
- Finding the proving tests for an implemented seam
- Checking likely downstream docs or tests after a code change

## Agent Routes
Product Scope:
- `docs/evergreen/mvp.md`: `Canonical`

Current Architecture:
- `docs/evergreen/architecture.md`: `Canonical`

Stable Public Package API:
- `docs/evergreen/api-contracts.md`: `Canonical`

Commands And Validation:
- `docs/evergreen/runbook.md`: `Canonical`

Evaluation Semantics:
- `docs/evergreen/eval-vocabulary.md`: `Canonical`
- `docs/evergreen/eval-support-semantics.md`: `Canonical`
- `docs/evergreen/eval-scenario-taxonomy.md`: `Canonical`
- `docs/evergreen/eval-failure-taxonomy.md`: `Canonical`

Workflow Rationale And Promotion Rules:
- `docs/delivery/workflow.md`: `Reference only`

Execution History And Prior Framing:
- `docs/workstreams/`: `Execution history`

Current Implementation Seams:
- `src/parity/retrieval.py`: `Implemented internal`
- `src/parity/query/`: `Implemented internal`
- `src/parity/readmodels/`: `Implemented internal`
- `src/parity/_contracts/`: `Implemented internal`
- `src/parity/app/`: `Implemented internal`
- `src/parity/artifacts/`: `Implemented internal`
- `src/parity/stages/`: `Implemented internal`
- `src/parity/extractors/`: `Implemented internal`
- `src/parity/normalizers/`: `Implemented internal`
- `src/parity/structure/`: `Implemented internal`
- `src/parity/chunking/`: `Implemented internal`
- `src/parity/indexing/`: `Implemented internal`
- `src/parity/persistence/`: `Implemented internal`
- `src/parity/evaluation/`: `Implemented internal`
- `src/parity/devtools/secret_scan.py`: `Implemented internal`

## Implementation Map
- `src/parity/retrieval.py` and `src/parity/cli.py`: implemented retrieval demo utilities. Open when changing `SemanticIndex`, ranking behavior, or CLI output. These modules are not a stable public API.
- `src/parity/query/contracts.py`, `src/parity/query/interpretation.py`, `src/parity/query/service.py`, `src/parity/query/stages/`, `src/parity/query/persistence.py`, and `src/parity/query/trace.py`: internal query runtime through Stage 2. Open when changing query run state, query-time snapshot semantics, interpreted-query shape, interpretation execution, or persisted stage traces.
- `src/parity/readmodels/documents.py`: query-facing corpus read model over lifecycle persistence. Open when changing `READY`-only queryability, snapshot membership capture, or fixed-snapshot section/chunk reads.
- `src/parity/_contracts/models.py` and `src/parity/_contracts/lifecycle.py`: internal corpus, provenance, answer, and lifecycle seams. Open when changing document, chunk, citation, answer, or processing-state semantics in code.
- `src/parity/app/api.py`, `src/parity/app/deps.py`, and `src/parity/app/settings.py`: internal FastAPI runtime and dependency wiring. Open when changing intake/status/retry/query route shape, dependency assembly, or runtime settings.
- `src/parity/lifecycle/service.py`, `src/parity/lifecycle/orchestrator.py`, and `src/parity/lifecycle/worker.py`: transport-thin lifecycle coordination, queued orchestration, retry behavior, and worker execution. Open when changing document-level control flow or failure handling.
- `src/parity/stages/`, `src/parity/extractors/`, `src/parity/normalizers/`, `src/parity/structure/`, `src/parity/chunking/`, and `src/parity/indexing/`: executable lifecycle stages from extraction through readiness. Open when changing stage invariants, format-specific transforms, vector publication, or readiness semantics.
- `src/parity/artifacts/store.py` and `src/parity/artifacts/schemas.py`: filesystem-backed artifact persistence for raw, extracted, and normalized payloads. Open when changing managed artifact paths or storage payload shapes.
- `src/parity/persistence/sqlite_compat.py`: SQLite compatibility round-trip layer for `Document`, `Section`, and `Chunk`. Open when changing persisted fields, linkage rules, or existing internal repository semantics.
- `src/parity/persistence/models.py`, `src/parity/persistence/jobs.py`, `src/parity/persistence/repositories.py`, and `src/parity/persistence/migrations/`: lifecycle metadata persistence, Alembic-backed migrations, and Postgres-oriented repository seams. Open when changing durable document/job/event storage or migration workflow.
- `src/parity/evaluation/models.py`, `src/parity/evaluation/dataset.py`, `src/parity/evaluation/runner.py`, `src/parity/evaluation/systems.py`, and `src/parity/evaluation/fixtures.py`: deterministic harness scaffolding. Open when changing baseline evaluation cases, provenance checks, or synthetic seam behavior.
- `src/parity/devtools/secret_scan.py`: repo safety tooling. Open when changing secret-pattern detection, reporting, or staged-vs-repo scanning behavior.

## Edit Starting Points
For retrieval demo changes:
- open `src/parity/retrieval.py`
- then inspect `src/parity/cli.py`
- then inspect `tests/test_retrieval.py` and `tests/test_cli.py`
- check `docs/evergreen/api-contracts.md` before describing any retrieval demo behavior as public or stable

For query runtime changes:
- open `src/parity/query/service.py`
- then inspect `src/parity/query/contracts.py`, `src/parity/query/interpretation.py`, `src/parity/query/stages/interpret.py`, and `src/parity/query/persistence.py`
- then inspect `src/parity/readmodels/documents.py`
- then inspect `src/parity/app/api.py` and `src/parity/app/deps.py`
- then inspect `tests/readmodels/test_queryable_corpus_read_model.py`, `tests/query/test_query_service_prepare.py`, `tests/query/test_interpretation.py`, `tests/query/test_query_service_interpret.py`, and `tests/app/test_runtime_api.py`
- if the change would promote query request, snapshot, interpreted-query, or route payloads into a supported downstream interface, update `docs/evergreen/api-contracts.md` first

For internal contract or lifecycle changes:
- open `src/parity/_contracts/models.py`
- then inspect `src/parity/_contracts/lifecycle.py`
- then inspect `tests/contract/test_contract_models.py`
- then inspect `tests/contract/test_lifecycle_state_machine.py`
- then inspect `tests/contract/test_contract_seam_compat.py`
- if semantics overlap evaluation labels, normalize against the evergreen eval docs instead of inventing local wording

For lifecycle runtime changes:
- open `src/parity/app/api.py`
- then inspect `src/parity/app/deps.py` and `src/parity/app/settings.py`
- then inspect `src/parity/lifecycle/service.py`, `src/parity/lifecycle/orchestrator.py`, and `src/parity/lifecycle/worker.py`
- then inspect the relevant stage module under `src/parity/stages/`
- then inspect `tests/app/test_documents_api.py`, `tests/stages/`, `tests/lifecycle/`, and `tests/pipeline/`
- if the change would create a stable external API, update `docs/evergreen/api-contracts.md` first instead of treating the internal route as public

For persistence changes:
- open `src/parity/persistence/`
- then inspect `tests/persistence/`
- then inspect `src/parity/_contracts/`

For evaluation harness changes:
- open `src/parity/evaluation/runner.py`
- then inspect `src/parity/evaluation/models.py`, `src/parity/evaluation/dataset.py`, and `src/parity/evaluation/fixtures.py`
- then inspect `tests/test_evaluation_harness.py`
- if you are changing support-state, scenario, citation, or failure meanings, open the evergreen eval docs first

For repo devtool changes:
- open `src/parity/devtools/secret_scan.py`
- then inspect `tests/test_secret_scan.py`

## Validation Routes
Use these proof points to distinguish implemented seams from doc-only intent:

- Retrieval demo surface: `tests/test_retrieval.py`, `tests/test_cli.py`
- Query boundary and interpretation runtime: `tests/readmodels/test_queryable_corpus_read_model.py`, `tests/query/test_query_service_prepare.py`, `tests/query/test_interpretation.py`, `tests/query/test_query_service_interpret.py`, `tests/app/test_runtime_api.py`
- Contract models and lifecycle rules: `tests/contract/test_contract_models.py`, `tests/contract/test_lifecycle_state_machine.py`, `tests/contract/test_contract_seam_compat.py`
- Lifecycle runtime and operator routes: `tests/app/test_documents_api.py`, `tests/lifecycle/test_worker.py`, `tests/pipeline/test_markdown_to_ready.py`, `tests/pipeline/test_pdf_to_ready.py`, `tests/pipeline/test_retry_recovery.py`
- Artifact storage: `tests/artifacts/test_raw_artifact_store.py`, `tests/artifacts/test_extracted_artifact_store.py`, `tests/artifacts/test_normalized_artifact_store.py`
- Stage invariants: `tests/stages/test_register_stage.py`, `tests/stages/test_extract_stage_markdown.py`, `tests/stages/test_extract_stage_pdf.py`, `tests/stages/test_normalize_stage_markdown.py`, `tests/stages/test_normalize_stage_pdf.py`, `tests/stages/test_section_stage.py`, `tests/stages/test_chunk_stage.py`, `tests/stages/test_index_stage.py`, `tests/stages/test_ready_stage.py`
- Persistence linkage and round-trips: `tests/persistence/test_document_repository.py`, `tests/persistence/test_section_repository.py`, `tests/persistence/test_chunk_repository.py`, `tests/persistence/test_index_entry_repository.py`, `tests/persistence/test_chunk_embedding_repository.py`, `tests/persistence/test_replace_on_retry.py`
- Deterministic evaluation behavior and provenance checks: `tests/test_evaluation_harness.py`, `src/parity/evaluation/fixtures.py`
- Secret scanning behavior: `tests/test_secret_scan.py`

## Change Impact
- Retrieval demo changes may affect `docs/evergreen/api-contracts.md`, `tests/test_retrieval.py`, and `tests/test_cli.py`.
- Query runtime changes may affect `src/parity/readmodels/`, `src/parity/query/`, `src/parity/app/api.py`, `src/parity/app/deps.py`, `tests/query/`, `tests/readmodels/`, and `tests/app/test_runtime_api.py`.
- Contract or lifecycle changes may affect `src/parity/persistence/`, `src/parity/evaluation/fixtures.py`, `tests/contract/`, `tests/persistence/`, and `tests/test_evaluation_harness.py`.
- Persistence changes may require matching updates to contract fields, ordering assumptions, integrity checks, and migrations.
- Evaluation harness changes may require matching updates to baseline cases, seam fixtures, and evergreen semantic docs if the change is semantic rather than mechanical.
- Semantic doc changes should normalize against the owning evergreen doc instead of inventing parallel labels locally.

## Guardrails
- Do not treat this file as the canonical architecture statement. It is a routing and implementation map.
- Do not infer stable public API from any internal route, package export, fixture, or repository seam unless `docs/evergreen/api-contracts.md` says so.
- Do not promote a seam here unless it is implemented and backed by current validation surfaces.
