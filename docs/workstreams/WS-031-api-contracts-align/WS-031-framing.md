# Framing

## Problem
The evergreen contract set is now materially better aligned to runtime truth, but it is not yet a durable system of record. The public API boundary is documented primarily in prose, while the only machine-readable schema surface is optional and broader than the stable public contract. The runbook still contains at least one operationally significant default drift, and the architecture doc identifies a route-layer asymmetry without setting architectural direction for convergence or tolerated debt.

At principal-engineering level, the concern is not just whether the docs are "mostly correct" today. The concern is whether they create a governance mechanism that can resist silent drift as the runtime evolves.

## Scope
- Analyze the evergreen trio as one contract and authority system:
  - `docs/evergreen/api-contracts.md`
  - `docs/evergreen/runbook.md`
  - `docs/evergreen/architecture.md`
- Ground all findings against current runtime wiring and boundary code.
- Capture the decisions and follow-up actions needed to make the doc system enforceable rather than prose-only.

## Constraints
- Evergreen docs are canonical; workstream artifacts may critique and propose but do not override them.
- Scope is limited to documentation, contract framing, and verification strategy. No runtime behavior change is assumed in this framing artifact.
- Current app topology mounts stable public routes and internal-only routes in the same FastAPI app.
- Swagger and OpenAPI exposure are optional at runtime and currently disabled by default.

## Input context
- paths:
  - `docs/evergreen/api-contracts.md`
  - `docs/evergreen/runbook.md`
  - `docs/evergreen/architecture.md`
  - `src/doc_forge/app/api.py`
  - `src/doc_forge/app/settings.py`
  - `src/doc_forge/app/routers/documents.py`
  - `src/doc_forge/app/routers/queries.py`
  - `src/doc_forge/app/routers/system.py`
  - `src/doc_forge/app/routers/internal.py`
- read first:
  - `docs/evergreen/api-contracts.md`
  - `docs/evergreen/architecture.md`
  - `docs/evergreen/runbook.md`
- verification commands:
  - `uv run python - <<'PY' ... create_app(Settings()) ... print(app.docs_url, app.openapi_url) ... PY`
  - `uv run python - <<'PY' ... create_app(Settings(enable_swagger=True)) ... print(sorted(app.openapi()['paths'])) ... PY`
  - `rg -n "DOC_FORGE_EMBEDDING_BACKEND|sentence-transformers|deterministic" docs/evergreen/runbook.md src/doc_forge/app/settings.py`

## Key decisions
- Whether the stable public contract should gain a canonical machine-checkable artifact, such as a filtered OpenAPI document or checked-in contract snapshot.
- Whether the documents boundary pattern should become the intended architectural direction for query, system, and internal route families.
- Whether evergreen verification metadata should be normalized across the trio and tied to an explicit verification procedure.
- Whether the runbook should be narrowed to operational guidance and defer more boundary semantics back to `api-contracts.md`.

## Expected outputs
- A findings-first analysis of the current evergreen trio with concrete runtime evidence.
- A prioritized set of follow-up actions for contract enforcement, runbook correction, and architectural direction-setting.
- Clear problem framing for WS-031 so implementation work can proceed without re-discovering the same issues.

## Exit criteria
- The workstream clearly states what is wrong, why it matters, and what decisions are required next.
- Each non-trivial finding is anchored to concrete doc claims and current runtime/code evidence.
- The next implementer can convert this framing into execution tasks without having to reinterpret the core problem.

## Objective
Establish a decision-quality framing for aligning API contract documentation to runtime truth so that the evergreen trio becomes trustworthy as a long-lived contract, operations, and architecture system rather than a set of individually useful but weakly enforced documents.

## Non-goals
- Rewriting the runtime architecture in this framing pass.
- Promoting new public Python package APIs.
- Treating workstream notes or ADRs as authority over evergreen docs.
- Performing a copy-edit pass focused on style instead of boundary risk.

## Relevant context
- components:
  - FastAPI app assembly in `src/doc_forge/app/api.py`
  - runtime config in `src/doc_forge/app/settings.py`
  - stable document boundary in `src/doc_forge/app/routers/documents.py`
  - query, system, and internal route families in sibling router modules
- evidence anchors:
  - Stable public contract language:
    - `docs/evergreen/api-contracts.md:30-93`
  - Runbook runtime and config statements:
    - `docs/evergreen/runbook.md:85-138`
  - Architecture boundary and asymmetry language:
    - `docs/evergreen/architecture.md:90-106`
  - FastAPI mounting and Swagger gating:
    - `src/doc_forge/app/api.py:43-48`
    - `src/doc_forge/app/api.py:63-66`
    - `src/doc_forge/app/settings.py:29-53`
  - Stable document route boundary:
    - `src/doc_forge/app/routers/documents.py:49-308`
  - Internal-only mounted routes:
    - `src/doc_forge/app/routers/internal.py:14-53`
  - Query and system route families still using HTTP-aware app services:
    - `src/doc_forge/app/routers/queries.py:26-109`
    - `src/doc_forge/app/routers/system.py:18-51`
- constraints:
  - stable public routes and internal-only routes are mounted into the same app
  - OpenAPI and Swagger are not enabled by default
  - the current stable contract is prose-first, not artifact-first
- observed runtime facts:
  - Default app creation currently yields `docs_url=None` and `openapi_url=None`.
  - Swagger-enabled app creation currently yields the mounted path set:
    - `/documents`
    - `/documents/{doc_id}`
    - `/documents/{doc_id}/artifacts`
    - `/documents/{doc_id}/retry`
    - `/documents/{doc_id}/status`
    - `/healthz`
    - `/internal/run-next-job`
    - `/queries`
    - `/queries/{query_id}`
    - `/queries/{query_id}/citations`
    - `/queries/{query_id}/trace`
    - `/readyz`
    - `/retrieval/query`
- findings:
  - Major: the public contract does not yet have a canonical machine-checkable representation.
    Evidence:
    `docs/evergreen/api-contracts.md:58-91` promises stability for path, method, request shape, response shape, and status codes, but the only schema artifact is optional and not the contract definition. In code, `src/doc_forge/app/api.py:43-48` exposes `/docs` and `/openapi.json` only when `settings.docs_enabled` is true, and `src/doc_forge/app/settings.py:29-53` defines that toggle via `enable_swagger=False` by default.
    Runtime check:
    default app creation produces `docs_url=None` and `openapi_url=None`; Swagger-enabled app creation produces paths for both stable public routes and internal-only routes such as `/retrieval/query` and `/internal/run-next-job`.
    Consequence:
    the contract is governed by prose, while the only machine-readable surface is both non-default and broader than the public API.
  - Major: the runbook still contains an operationally meaningful default drift.
    Evidence:
    `docs/evergreen/runbook.md:123-125` states that `DOC_FORGE_EMBEDDING_BACKEND` defaults to `sentence-transformers`, while `src/doc_forge/app/settings.py:44-49` sets the runtime default to `deterministic`.
    Consequence:
    operator expectations about dependency installation, retrieval behavior, and troubleshooting are unreliable.
  - Major: the architecture doc diagnoses route-family asymmetry but does not govern it.
    Evidence:
    `docs/evergreen/architecture.md:97-106` explicitly notes that documents use a facade-plus-edge-mapping split while query, internal, and system route families remain HTTP-aware app services.
    Code alignment:
    document routes depend on `DocumentsFacade` in `src/doc_forge/app/routers/documents.py:69-308`, while internal and query routes still depend directly on app services in `src/doc_forge/app/routers/internal.py:32-53` and `src/doc_forge/app/routers/queries.py:45-109`.
    Consequence:
    contributors can see the asymmetry but have no evergreen guidance on whether to converge or tolerate it as bounded debt.
  - Minor: verification metadata is not yet credible as a trio-level governance signal.
    Evidence:
    `docs/evergreen/api-contracts.md:3-4` now has a newer verification date than `docs/evergreen/architecture.md:3-4`, even though the latter contains recently updated boundary language at `docs/evergreen/architecture.md:92-106`. `docs/evergreen/runbook.md` has no corresponding verification marker.
    Consequence:
    freshness and authority signals are inconsistent across the canonical set.
  - Minor: the runbook still carries more boundary semantics than an operations doc should.
    Evidence:
    the Local HTTP Runtime section at `docs/evergreen/runbook.md:85-105` mixes startup instructions, public-vs-internal route policy, schema interpretation, debug endpoints, observability references, and runtime caveats.
    Consequence:
    it remains useful, but it is under ongoing duplication pressure from `api-contracts.md` and `architecture.md`.
- strengths:
  - `docs/evergreen/api-contracts.md:31-78` now clearly separates stable public routes from runtime-exposed non-public routes.
  - the stable route inventory aligns with the mounted documents, queries, and system routers in `src/doc_forge/app/routers/documents.py`, `src/doc_forge/app/routers/queries.py`, and `src/doc_forge/app/routers/system.py`.
  - `docs/evergreen/architecture.md:123-130` correctly avoids treating internal lifecycle and corpus packages as public API.

## Detached-work handoff
- Treat the findings in this document as the authoritative rationale baseline for WS-031 execution.
- Do not re-open whether the evergreen trio has a problem; that has already been established here. Detached work should focus on resolution strategy and implementation.
- Use the evidence anchors and observed runtime facts above rather than re-deriving them from workstream notes.
- Expected execution slices:
  - contract artifact strategy:
    decide whether to generate a filtered OpenAPI artifact for stable public routes or keep a checked-in contract snapshot validated in tests
  - runbook correction:
    fix documented runtime defaults and reduce repeated boundary policy where possible
  - architecture direction:
    decide whether the documents facade pattern is the intended route-family direction or accepted local asymmetry
  - verification normalization:
    decide how evergreen docs earn and display verification status and dates
- Minimum handoff evidence any detached implementer should preserve:
  - the stable public route set listed in `docs/evergreen/api-contracts.md`
  - the mounted internal routes `/retrieval/query` and `/internal/run-next-job`
  - default Swagger/OpenAPI disabled state
  - the embedding-backend default mismatch between runbook and runtime settings
  - the documented route-family asymmetry in architecture and code

## Workflow steps
1. Preserve this framing as the rationale baseline for WS-031.
2. Convert each major finding into an execution item with an explicit owner artifact:
   - contract artifact strategy
   - runbook default correction
   - architecture direction on route-family convergence
   - verification metadata normalization
3. Decide whether WS-031 ends at docs alignment or also introduces contract-validation tooling.
4. Execute the chosen alignment path and capture resulting evidence back into the workstream.

## Validation and Definition of Done
- The workstream must explicitly resolve whether the stable public contract will remain prose-only or gain a machine-checkable artifact.
- The runbook must match runtime configuration defaults for documented operator-facing settings.
- The architecture doc must either set a direction for route-family convergence or explicitly classify the asymmetry as accepted bounded debt.
- Evergreen verification language must be internally consistent across the trio.
- Final output should leave no ambiguity about the stable public API boundary, optional runtime schema exposure, and internal-only route status.

## Linked artifacts
- `docs/evergreen/api-contracts.md`
- `docs/evergreen/runbook.md`
- `docs/evergreen/architecture.md`
- `docs/workstreams/WS-031-api-contracts-align/WS-031-workstream.md`
