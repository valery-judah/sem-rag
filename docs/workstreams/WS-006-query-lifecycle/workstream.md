---
artifact_kind: workstream
id: WS-006
title: Query Lifecycle
work_type: feature
status: active
owner:
created: 2026-03-11
updated: 2026-03-11
---

# Summary
Implement the explicit query lifecycle for grounded QA over the `READY` corpus, preserving support semantics, traceability, and provenance-bearing evidence structures.

## Objective
Ship the MVP query path as explicit executable stages:
`Interpret -> Retrieve -> Select -> Assemble Context -> Assess Support -> Decide Answer Mode -> Generate -> Cite or Abstain`.

## Non-goals
- Replacing the staged lifecycle with one fused retrieval-plus-prompt loop.
- Promoting internal query runtime seams into a stable public API before the runtime path is complete.
- Treating retrieved text or evidence sets as sufficient proof without explicit support assessment.

## Current status
- Stages 1 through 5 are implemented: queryable corpus boundary, interpretation, retrieval, selection/evidence-set construction, and deterministic context assembly.
- Internal `POST /queries` now executes through Stage 5 and persists `interpret`, `retrieve`, `select`, and `assemble_context` traces.
- The main remaining implementation gap is Stage 6 onward: support assessment, answer-mode policy, generation, and citation rendering.

## Next step
- Design and implement Stage 6 support assessment and answer-mode policy over interpreted queries, evidence sets, and context manifests.

## Relevant context
- paths:
- `src/parity/query/`
- `src/parity/readmodels/`
- `src/parity/app/api.py`
- components:
- query service orchestration
- snapshot-scoped retrieval and selection
- durable query stage tracing
- constraints:
- only `READY` documents are queryable
- each query executes against a stable corpus snapshot
- later stages may narrow answer posture but must not widen it
- read first:
- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/workstreams/WS-006-query-lifecycle/07_design.md`
- `docs/workstreams/WS-006-query-lifecycle/query_subsystem_staged_implementation_plan.md`

## Workflow steps
1. Frame the feature scope and relevant constraints.
2. Shape the implementation and validation approach.
3. Execute and validate the workstream.

## Validation
- Stage-specific query tests under `tests/query/`
- route behavior under `tests/app/test_runtime_api.py`
- contract coverage under `tests/contract/test_query_contract_models.py`
- repo validation through `make test`, plus stronger checks when internal API or package behavior changes

## Linked artifacts
- Add related notes, decisions, evidence, ADRs, and evergreen docs here when they exist.
- `00_requirements-v0.md`
- `01_requirements-critique.md`
- `05_decisions-baseline.md`
- `07_design.md`
- `query_subsystem_staged_implementation_plan.md`
- `10_stage-0-foundation-design.md`
- `11_stage-1-queryable-corpus-boundary-design.md`
- `12_stage-2-interpretation-foundation-design.md`
- `13_stage-3-retrieval-foundation-design.md`
- `14_stage-4-selection-evidence-set-construction-design.md`
- `15_stage-5-deterministic-context-assembly-design.md`
