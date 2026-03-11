# Architecture

**Status:** Verified
**Last verified:** 2026-03-11

## Purpose
This file captures the current architectural truth for `parity` and the gap between today's code and the target product described in [`docs/evergreen/mvp.md`](./mvp.md). It is also a local architecture map for coding agents: use it to find the right code entrypoint, the right authority doc, and the current boundary between implemented scaffolding and missing product runtime.

## When To Use
- Starting work on a subsystem
- Figuring out which file owns a behavior before editing
- Checking which doc is authoritative before changing code or docs
- Checking whether a capability is implemented, internal-only, or still planned

## Agent Routes
Product Scope:
- `docs/evergreen/mvp.md`: `Canonical`

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
- `src/parity/retrieval.py` and `src/parity/cli.py`: public retrieval demo surface. Open when changing `SemanticIndex`, ranking behavior, or CLI output.
- `src/parity/_contracts/models.py` and `src/parity/_contracts/lifecycle.py`: internal corpus, provenance, answer, and lifecycle seams. Open when changing document, chunk, citation, answer, or processing-state semantics in code.
- `src/parity/app/api.py`, `src/parity/app/deps.py`, and `src/parity/app/settings.py`: internal FastAPI lifecycle runtime and environment wiring. Open when changing intake/status/retry/query route shape, dependency assembly, or runtime settings.
- `src/parity/lifecycle/service.py`, `src/parity/lifecycle/orchestrator.py`, and `src/parity/lifecycle/worker.py`: transport-thin lifecycle coordination, queued orchestration, retry behavior, and worker execution. Open when changing document-level control flow or failure handling.
- `src/parity/stages/`, `src/parity/extractors/`, `src/parity/normalizers/`, `src/parity/structure/`, `src/parity/chunking/`, and `src/parity/indexing/`: executable lifecycle stages from extraction through readiness. Open when changing stage invariants, format-specific transforms, vector publication, or readiness semantics.
- `src/parity/artifacts/store.py` and `src/parity/artifacts/schemas.py`: filesystem-backed artifact persistence for raw, extracted, and normalized payloads. Open when changing managed artifact paths or storage payload shapes.
- `src/parity/persistence/sqlite_compat.py`: SQLite compatibility round-trip layer for `Document`, `Section`, and `Chunk`. Open when changing persisted fields, linkage rules, or existing internal repository semantics.
- `src/parity/persistence/models.py`, `src/parity/persistence/jobs.py`, `src/parity/persistence/repositories.py`, and `src/parity/persistence/migrations/`: lifecycle metadata persistence, Alembic-backed migrations, and Postgres-oriented repository seams. Open when changing durable document/job/event storage or migration workflow.
- `src/parity/evaluation/models.py`, `src/parity/evaluation/dataset.py`, `src/parity/evaluation/runner.py`, `src/parity/evaluation/systems.py`, and `src/parity/evaluation/fixtures.py`: deterministic harness scaffolding. Open when changing baseline evaluation cases, provenance checks, or synthetic seam behavior.
- `src/parity/devtools/secret_scan.py`: repo safety tooling. Open when changing secret-pattern detection, reporting, or staged-vs-repo scanning behavior.

The implemented architecture is broader than the stable public API, but the user-facing runtime is still narrow.

## Edit Starting Points
For retrieval demo changes:
- open `src/parity/retrieval.py`
- then inspect `src/parity/cli.py`
- then inspect `tests/test_retrieval.py` and `tests/test_cli.py`
- if behavior is public, check `docs/evergreen/api-contracts.md`

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

## Validated By
Use these proof points to distinguish implemented seams from doc-only intent:

- Retrieval demo surface: `tests/test_retrieval.py`, `tests/test_cli.py`
- Contract models and lifecycle rules: `tests/contract/test_contract_models.py`, `tests/contract/test_lifecycle_state_machine.py`, `tests/contract/test_contract_seam_compat.py`
- Lifecycle runtime and operator routes: `tests/app/test_documents_api.py`, `tests/lifecycle/test_worker.py`, `tests/pipeline/test_markdown_to_ready.py`, `tests/pipeline/test_pdf_to_ready.py`, `tests/pipeline/test_retry_recovery.py`
- Artifact storage: `tests/artifacts/test_raw_artifact_store.py`, `tests/artifacts/test_extracted_artifact_store.py`, `tests/artifacts/test_normalized_artifact_store.py`
- Stage invariants: `tests/stages/test_register_stage.py`, `tests/stages/test_extract_stage_markdown.py`, `tests/stages/test_extract_stage_pdf.py`, `tests/stages/test_normalize_stage_markdown.py`, `tests/stages/test_normalize_stage_pdf.py`, `tests/stages/test_section_stage.py`, `tests/stages/test_chunk_stage.py`, `tests/stages/test_index_stage.py`, `tests/stages/test_ready_stage.py`
- Persistence linkage and round-trips: `tests/persistence/test_document_repository.py`, `tests/persistence/test_section_repository.py`, `tests/persistence/test_chunk_repository.py`, `tests/persistence/test_index_entry_repository.py`, `tests/persistence/test_chunk_embedding_repository.py`, `tests/persistence/test_replace_on_retry.py`
- Deterministic evaluation behavior and provenance checks: `tests/test_evaluation_harness.py`, `src/parity/evaluation/fixtures.py`
- Secret scanning behavior: `tests/test_secret_scan.py`

These tests and fixtures are the reason the seams below count as current architecture rather than unexercised design intent.

## Current Architectural Seams
The currently earned seams are:

- stable public demo surface around `SemanticIndex` and the CLI
- provenance-bearing corpus primitives for documents, sections, chunks, retrieval hits, and answers
- explicit document-processing lifecycle progression with a failure state
- internal FastAPI lifecycle runtime for upload, status, retry, retrieval smoke, health, and artifact inspection
- queued lifecycle orchestration with a document-scoped worker and stage dispatch
- durable registration of supported PDF and Markdown uploads into `REGISTERED` documents with initial lifecycle events and queued extraction work
- filesystem-backed raw, extracted, and normalized artifact storage with deterministic document-scoped paths
- Markdown and PDF extraction plus persisted extracted artifacts
- Markdown and PDF normalization plus persisted normalized artifacts
- section recovery, chunk production, vector publication, and strict readiness evaluation through `READY`
- SQLite-backed compatibility persistence for corpus primitives with linkage enforcement
- Alembic-backed migration workflow and lifecycle/indexing repositories for documents, lifecycle events, document jobs, sections, chunks, index entries, and chunk embeddings
- deterministic evaluation of retrieval ordering, supporting evidence, and provenance completeness
- repo devtool support for staged and repository secret scanning

## Boundary Between Public API, Internal Architecture, And Planned Work
### Stable Public API
The stable public package interface remains intentionally empty and is defined in [`docs/evergreen/api-contracts.md`](./api-contracts.md). The new upload route is an internal runtime seam, not a public contract.

### Implemented Internal Architecture
The `_contracts` layer, internal lifecycle app, queue worker, executable stages from registration through readiness, artifact store, persistence/indexing helpers, evaluation harness, and devtools exist in code and are exercised by tests. They are current implementation truth, but they are not yet promised as stable external interfaces for downstream callers.

### Planned MVP Capabilities Not Yet Implemented
The target product in [`docs/evergreen/mvp.md`](./mvp.md) still exceeds the runtime that exists today. The following user-facing capabilities are not implemented in `src/parity/`:

- no answer-generation service
- no stable public service or package API
- no user-facing source-inspection UI beyond internal debug/operator routes

## Agent Guardrails
- Do not treat `src/parity/_contracts/` as public API. It is real implemented architecture, but it is internal until `docs/evergreen/api-contracts.md` says otherwise.
- Do not redefine evaluation semantics here. Support-state, scenario, citation, and failure meanings are owned by the evergreen eval docs.
- Do not treat `docs/delivery/workflow.md` as authority for current implementation truth. It is workflow rationale and promotion guidance, not the current-state source of truth.
- Do not infer public API stability, answer generation, or user-facing source inspection from internal lifecycle routes or worker seams.
- Do not promote a new seam into evergreen architecture just because it appears in one prototype or one workstream. It should be implemented repo truth and exercised under tests or equivalent validation pressure.

## Change Impact
- Retrieval demo changes may affect `docs/evergreen/api-contracts.md`, `tests/test_retrieval.py`, and `tests/test_cli.py`.
- Contract or lifecycle changes may affect `src/parity/persistence/`, `src/parity/evaluation/fixtures.py`, `tests/contract/`, `tests/persistence/`, and `tests/test_evaluation_harness.py`.
- Persistence changes may require matching updates to contract fields, ordering assumptions, and integrity checks in tests.
- Evaluation harness changes may require matching updates to baseline cases, seam fixtures, and evergreen semantic docs if the change is semantic rather than mechanical.
- Semantic doc changes should normalize against the owning evergreen doc instead of inventing parallel labels locally.

## Workflow Alignment
This file should only promote seams that have earned their place through implemented behavior and validation pressure, consistent with the model-first workflow in `docs/delivery/workflow.md`.

Future architecture should be promoted here only after it becomes implemented repo truth and survives comparable scenario or failure pressure.

## Documentation Authority
- `docs/evergreen/mvp.md`: product north star and scope boundary
- `docs/evergreen/api-contracts.md`: stable public interfaces that are implemented today
- this file: current repo shape, code-entry routing, and gap to the MVP
- `docs/README.md`: docs system map
