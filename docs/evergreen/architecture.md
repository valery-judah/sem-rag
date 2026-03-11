# Architecture

**Status:** Verified
**Last verified:** 2026-03-11

## Purpose
This file captures the current architectural truth for `parity` and the gap between today's code and the target product described in [`docs/evergreen/mvp.md`](./mvp.md).

It is the canonical architecture statement for:

- runtime and storage topology
- major bounded contexts and ownership boundaries
- earned internal seams
- the boundary between public API, internal architecture, and planned work

For coding-agent routing, file ownership, edit starting points, and change-impact navigation, use [`docs/evergreen/agent-routing.md`](./agent-routing.md).

## When To Use
- Starting work on a subsystem
- Checking which doc is authoritative before changing code or docs
- Checking whether a capability is implemented, internal-only, or still planned
- Understanding how far current runtime truth has moved toward the MVP

## Topology
The current implementation remains a single-service local runtime:

- one FastAPI application
- one primary relational metadata store through SQLAlchemy and Alembic-managed persistence
- filesystem-backed artifact storage for raw, extracted, and normalized document artifacts
- one internal query domain growing inside the same service boundary as the document lifecycle

This topology is intentionally simple and local. Conceptual query stages are explicit in code and persistence, but not split into separate services.

## Bounded Contexts
The currently relevant bounded contexts are:

- document lifecycle:
  - registration, extraction, normalization, section recovery, chunking, indexing, readiness, retry
- query runtime:
  - query run creation, stable corpus snapshots, interpretation, snapshot-scoped dense retrieval, deterministic selection/evidence-set construction, and stage tracing through Stage 4
- query-facing read model:
  - read-only projection of `READY` lifecycle outputs into a queryable corpus, including retrieval-ready embedded chunks
- persistence:
  - durable metadata for lifecycle state, indexing, query runs, query snapshots, and stage traces
- artifacts:
  - managed filesystem storage owned by the lifecycle side
- evaluation:
  - deterministic harnesses and semantic proof surfaces

## Current Architectural Seams
The currently earned seams are:

- implemented retrieval demo utilities around `SemanticIndex` and the CLI, without stable public API status
- provenance-bearing corpus primitives for documents, sections, chunks, retrieval hits, and answers
- explicit document-processing lifecycle progression with a failure state
- internal FastAPI lifecycle runtime for upload, status, retry, retrieval smoke, health, and artifact inspection
- query-facing read model that admits only `READY` lifecycle documents into the queryable corpus
- stable query-time corpus snapshots with persisted `eligible_doc_ids`
- durable query runs and query snapshots for internal query execution
- deterministic interpreted-query contract, normalization, and unsupported-capability detection
- executable internal `interpret` stage with durable stage traces in `query_stage_traces`
- snapshot-scoped dense retrieval over persisted chunk embeddings with provenance-preserving `RetrievedCandidate` output
- executable internal `retrieve` stage with durable stage traces in `query_stage_traces`
- deterministic selection with duplicate suppression, bounded neighbor expansion, and first-class `EvidenceSet` output
- executable internal `select` stage with durable stage traces in `query_stage_traces`
- internal `POST /queries` execution through Stage 4 selection, with explicit stop before context assembly
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

These seams are implemented internal architecture, not stable public contracts.

## Boundary Between Public API, Internal Architecture, And Planned Work
### Stable Public API
The stable public package interface remains intentionally empty and is defined in [`docs/evergreen/api-contracts.md`](./api-contracts.md). Internal routes such as upload/status/retry/retrieval smoke and `POST /queries`, along with `src/parity/query/` exports, are implemented runtime seams rather than public contracts.

### Implemented Internal Architecture
The `_contracts` layer, query read model, internal query runtime through Stage 4 selection/evidence-set construction, internal lifecycle app, queue worker, executable stages from registration through readiness, artifact store, persistence/indexing helpers, evaluation harness, and devtools exist in code and are exercised by tests. They are current implementation truth, but they are not yet promised as stable external interfaces for downstream callers.

### Planned MVP Capabilities Not Yet Implemented
The target product in [`docs/evergreen/mvp.md`](./mvp.md) still exceeds the runtime that exists today. The following user-facing capabilities are not implemented in `src/parity/`:

- no context-assembly stage
- no support-assessment stage
- no answer-mode decision stage
- no answer-generation service
- no citation-rendering stage
- no stable public service or package API
- no user-facing source-inspection UI beyond internal debug/operator routes

## Gap To MVP
The current runtime has earned lifecycle processing through `READY`, query-time corpus boundary capture, interpretation through Stage 2, snapshot-scoped dense retrieval through Stage 3, and deterministic selection/evidence-set construction through Stage 4.

The main remaining gap to the MVP question-answering service is the rest of the query path:

- context assembly
- support assessment
- answer-mode selection
- grounded answer generation
- citation rendering

The runtime also has not earned a stable public service or package API.

## Agent Guardrails
- Do not treat `src/parity/_contracts/` as public API. It is real implemented architecture, but it is internal until `docs/evergreen/api-contracts.md` says otherwise.
- Do not redefine evaluation semantics here. Support-state, scenario, citation, and failure meanings are owned by the evergreen eval docs.
- Do not treat `docs/delivery/workflow.md` as authority for current implementation truth. It is workflow rationale and promotion guidance, not the current-state source of truth.
- Do not infer public API stability, answer generation, or user-facing source inspection from internal lifecycle routes or worker seams.
- Do not infer context assembly, support assessment, answer-mode selection, generation, or citation rendering from the existence of `InterpretedQuery`, support-state enums, trust-failure labels, or `EvidenceSet` objects in `src/parity/query/contracts.py`.
- When referencing support-state or trust-failure vocabulary, normalize against [`docs/evergreen/eval-support-semantics.md`](./eval-support-semantics.md) and related evergreen eval docs instead of restating workstream-specific framing as runtime fact.
- Do not promote a new seam into evergreen architecture just because it appears in one prototype or one workstream. It should be implemented repo truth and exercised under tests or equivalent validation pressure.

## Routing Note
For file ownership, edit starting points, proving tests, and likely change impact, use [`docs/evergreen/agent-routing.md`](./agent-routing.md).

## Workflow Alignment
This file should only promote seams that have earned their place through implemented behavior and validation pressure, consistent with the model-first workflow in `docs/delivery/workflow.md`.

Future architecture should be promoted here only after it becomes implemented repo truth and survives comparable scenario or failure pressure.

## Documentation Authority
- `docs/evergreen/mvp.md`: product north star and scope boundary
- `docs/evergreen/api-contracts.md`: stable public interfaces that are implemented today
- this file: current architecture, earned internal seams, and gap to the MVP
- `docs/evergreen/agent-routing.md`: coding-agent routing, implementation map, and change-navigation guide
- `docs/README.md`: docs system map
