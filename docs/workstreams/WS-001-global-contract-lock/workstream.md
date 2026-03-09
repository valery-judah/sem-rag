---
artifact_kind: workstream
id: WS-001
title: Global Contract Lock
work_type: feature
status: active
owner:
created: 2026-03-08
updated: 2026-03-09
tags: []
affected_paths:
  - docs/workstreams/WS-001-global-contract-lock/workstream.md
  - docs/workstreams/WS-001-global-contract-lock/contract-lock.md
  - docs/workstreams/WS-001-global-contract-lock/seam.md
  - docs/workstreams/WS-001-global-contract-lock/status.md
  - docs/workstreams/WS-001-global-contract-lock/handoff.md
  - src/parity/_contracts/
  - tests/test_contracts.py
  - tests/test_contract_seam.py
affected_components:
  - workstream framing
  - shared internal contracts
  - contract validation tests
  - contract seam tests
blockers: []
depends_on: []
evergreen_targets: []
adr_links: []
rfc_links:
  - docs/workstreams/WS-001-global-contract-lock/contract-lock.md
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
The repository still exposes only a retrieval demo through `parity.SemanticIndex` and `python -m parity.cli`; there is no real ingestion pipeline, normalization runtime, answer-generation path, or source-inspection surface yet. WS-001 now has a canonical contract artifact, a dedicated seam note, status and handoff records, an internal contract package in `src/parity/_contracts/`, and separate test layers for contract shape and seam behavior.

## Next step
- Run repository validation against the locked Phase 1 package and docs, then capture evidence for downstream Phase 2 and Phase 3 consumers.

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
2. Lock the shared contract RFC, seam note, and workstream-local status / handoff artifacts.
3. Validate the internal schema package with contract-shape and seam-flow tests.

## Validation
- Docs review against the MVP and post-MVP framing documents
- Schema validation tests for required fields and enum constraints
- Answer contract tests for supported and insufficient-evidence behavior
- Lifecycle transition validation for the locked processing states
- Repository validation via `make fmt`, `make lint`, `make type`, and `make test`

## Linked artifacts
- Workstream-local RFC: `docs/workstreams/WS-001-global-contract-lock/contract-lock.md`
- Contract seam note: `docs/workstreams/WS-001-global-contract-lock/seam.md`
- Status tracker: `docs/workstreams/WS-001-global-contract-lock/status.md`
- Handoff note: `docs/workstreams/WS-001-global-contract-lock/handoff.md`
- Background context only: `docs/delivery/RFC-MVP-Architecture.md`
