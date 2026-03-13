# Architecture

**Status:** Verified
**Last verified:** 2026-03-13

## Purpose
This file captures the current architectural truth for `doc_forge` and the gap between today's code and the target product described in [`docs/evergreen/mvp.md`](./mvp.md).

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

For Docker-backed local operation, answer generation can also use a host-native
Ollama process on Apple Silicon through `host.docker.internal` while keeping the
core runtime topology unchanged.

For local operator workflows, the repo now also has a separate Compose-based
observability stack that indexes query/eval bundle metadata into a dedicated
Postgres instance and centralizes JSON service logs in Loki.

## Bounded Contexts
The currently relevant bounded contexts are:

- document lifecycle:
  - registration, extraction, normalization, section recovery, chunking, indexing, readiness, retry
- query runtime:
  - query run creation, stable corpus snapshots, interpretation, snapshot-scoped dense retrieval, deterministic selection/evidence-set construction, deterministic context assembly, and stage tracing through Stage 5
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

- provenance-bearing corpus primitives for documents, sections, chunks, retrieval hits, and answers
- explicit document-processing lifecycle progression with a failure state
- localhost FastAPI service runtime for health, readiness, document lifecycle, query submission, query review, and environment-toggled Swagger UI
- Docker-local answer-generation defaults that auto-select host Ollama on `Darwin arm64` when it is reachable, while keeping non-Docker process defaults deterministic
- query-facing read model that admits only `READY` lifecycle documents into the queryable corpus
- stable query-time corpus snapshots with persisted `eligible_doc_ids`
- durable query runs, query snapshots, stage traces, and answer artifacts for local query execution
- deterministic interpreted-query contract, normalization, and unsupported-capability detection
- executable internal `interpret` stage with durable stage traces in `query_stage_traces`
- snapshot-scoped dense retrieval over persisted chunk embeddings with provenance-preserving `RetrievedCandidate` output
- executable internal `retrieve` stage with durable stage traces in `query_stage_traces`
- deterministic selection with duplicate suppression, bounded neighbor expansion, and first-class `EvidenceSet` output
- executable internal `select` stage with durable stage traces in `query_stage_traces`
- deterministic context assembly with inspectable `ContextManifest` output and durable `assemble_context` traces
- local `POST /queries` execution through support assessment, answer-mode selection, grounded answer generation, and citation rendering
- queued lifecycle orchestration with a document-scoped worker and stage dispatch
- durable registration of supported PDF and Markdown uploads into `REGISTERED` documents with initial lifecycle events and queued extraction work
- filesystem-backed raw, extracted, and normalized artifact storage with deterministic document-scoped paths
- Markdown and PDF extraction plus persisted extracted artifacts
- Markdown and PDF normalization plus persisted normalized artifacts
- section recovery, chunk production, vector publication, and strict readiness evaluation through `READY`
- SQLite-backed compatibility persistence for corpus primitives with linkage enforcement
- Alembic-backed migration workflow, including lock-protected runtime startup migrations for containerized services, plus lifecycle/indexing repositories for documents, lifecycle events, document jobs, sections, chunks, index entries, and chunk embeddings
- deterministic evaluation of retrieval ordering, supporting evidence, and provenance completeness
- repo devtool support for staged and repository secret scanning
- repo devtool support for Docker-local generator default resolution across Compose, docker-backed e2e, and manual smoke harnesses
- separate local observability services for centralized query/eval metadata
  indexing and service-log browsing over existing filesystem outputs

Most of these seams are implemented internal architecture. The localhost FastAPI service routes are additionally promoted as stable public contracts in [`docs/evergreen/api-contracts.md`](./api-contracts.md).

## Boundary Between Public API, Internal Architecture, And Planned Work
### Stable Public API
The stable public interface is the localhost FastAPI HTTP API defined in [`docs/evergreen/api-contracts.md`](./api-contracts.md). The stable boundary is the running service route set plus its OpenAPI description. The public Python package interface remains intentionally empty.

### Implemented Internal Architecture
The `corpus` layer, query read model, Python query runtime, queue worker, executable stages from registration through readiness, artifact store, persistence/indexing helpers, evaluation harness, and devtools exist in code and are exercised by tests. These package seams are current implementation truth, but they remain internal unless promoted into [`docs/evergreen/api-contracts.md`](./api-contracts.md).

### Planned MVP Capabilities Not Yet Implemented
The target product in [`docs/evergreen/mvp.md`](./mvp.md) still exceeds the runtime that exists today. The following user-facing capabilities are not implemented in `src/doc_forge/`:

- no stable public Python package API
- no end-user source-inspection UI beyond the current HTTP review and artifact-inspection routes

## Gap To MVP
The current runtime has earned lifecycle processing through `READY`, full query execution through grounded answer generation and citation rendering, and a stable localhost HTTP service API.

The main remaining gap to the MVP is product surface and hardening rather than missing core query stages:

- no end-user source-inspection UI beyond the current service routes
- no stable public Python package API
- local-first runtime and operator ergonomics still dominate over broader productization

## Agent Guardrails
- Do not treat `src/doc_forge/corpus/` or `src/doc_forge/lifecycle/` as public package API. They are real implemented architecture, but they remain internal unless `docs/evergreen/api-contracts.md` promotes them.
- Do not redefine evaluation semantics here. Support-state, scenario, citation, and failure meanings are owned by the evergreen eval docs.
- Do not treat `docs/delivery/workflow.md` as authority for current implementation truth. It is workflow rationale and promotion guidance, not the current-state source of truth.
- Do not infer additional public API stability beyond the routes documented in `docs/evergreen/api-contracts.md` from internal lifecycle routes, worker seams, or package exports.
- Do not infer support assessment, answer-mode selection, generation, or citation rendering from the existence of `InterpretedQuery`, support-state enums, trust-failure labels, `EvidenceSet` objects, or `ContextManifest` objects in `src/doc_forge/query/contracts.py`.
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
