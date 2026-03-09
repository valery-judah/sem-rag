---
artifact_kind: workstream
id: WS-001
title: Global Contract Lock
work_type: feature
status: active
owner:
created: 2026-03-08
updated: 2026-03-08
tags: []
affected_paths:
  - docs/workstreams/WS-001-global-contract-lock/workstream.md
  - docs/workstreams/WS-001-global-contract-lock/contract-lock-rfc.md
  - src/parity/_contracts/
  - tests/test_contracts.py
affected_components:
  - workstream framing
  - shared internal contracts
  - contract validation tests
blockers: []
depends_on: []
evergreen_targets: []
adr_links: []
rfc_links:
  - docs/workstreams/WS-001-global-contract-lock/contract-lock-rfc.md
validation_evidence: []
gate: none
context_dependencies:
  - docs/delivery/service-mvp-1.md
  - docs/delivery/post-mvp-framing-workflow-v2.md
  - docs/delivery/RFC-MVP-Architecture.md
  - docs/evergreen/architecture.md
  - docs/evergreen/api-contracts.md
commands:
  - make fmt
  - make lint
  - make type
  - make test
boundaries:
  - Internal shared contracts only; no public service API design in this phase.
  - Do not lock parsing heuristics, chunk sizing, prompt wording, or evaluation corpus details.
  - Do not treat this workstream as an evergreen architecture freeze.
---

# Summary
Define the minimum shared internal contracts required to let MVP implementation proceed across Platform, Parsing, Search / RAG, and LLMOps without ambiguous object shapes, lifecycle semantics, or provenance guarantees.

## Objective
Lock a narrow cross-domain contract layer for the MVP by defining a shared internal schema set, answer and source-reference semantics, processing lifecycle rules, and domain ownership boundaries, then back those contracts with lightweight validation tests.

## Non-goals
- HTTP or CLI service endpoint design
- Parsing heuristics for Markdown or PDF structure recovery
- Chunk sizing or retrieval tuning policy
- Prompt wording or answer-style experimentation
- Golden Dataset design and evaluation harness work
- Production observability, rollout hardening, or operational policy

## Current status
The repository currently exposes only a retrieval demo through `parity.SemanticIndex` and `python -m parity.cli`. There is no implemented ingestion pipeline, normalization layer, answer-generation runtime, or source-inspection surface yet. The MVP and post-MVP framing docs establish the target system shape, but the shared internal contracts needed to build that system concurrently are not yet defined in code or in a workstream-local contract artifact.

## Next step
- Draft the workstream-local contract RFC and align the initial internal schema package to it.

## Relevant context
- paths:
  - `docs/delivery/service-mvp-1.md`
  - `docs/delivery/post-mvp-framing-workflow-v2.md`
  - `docs/delivery/RFC-MVP-Architecture.md`
  - `src/parity/`
- components:
  - cross-domain contract layer
  - processing lifecycle semantics
  - provenance and answer payload contracts
- constraints:
  - keep Contract Lock narrow and internal
  - preserve MVP invariants around traceability, groundedness, and honest failure
  - avoid freezing local implementation heuristics too early
- read first:
  - `docs/delivery/service-mvp-1.md`
  - `docs/delivery/post-mvp-framing-workflow-v2.md`
  - `docs/evergreen/architecture.md`
  - `docs/evergreen/api-contracts.md`

## Workflow steps
1. Frame the feature scope and relevant constraints.
2. Draft the shared contract RFC and internal schema package.
3. Add contract validation tests and record implementation evidence.

## Validation
- Docs review against the MVP and post-MVP framing documents
- Schema validation tests for required fields and enum constraints
- Answer contract tests for supported and insufficient-evidence behavior
- Lifecycle transition validation for the locked processing states
- Repository validation via `make fmt`, `make lint`, `make type`, and `make test`

## Linked artifacts
- Workstream-local RFC: `docs/workstreams/WS-001-global-contract-lock/contract-lock-rfc.md`
- Background context only: `docs/delivery/RFC-MVP-Architecture.md`
