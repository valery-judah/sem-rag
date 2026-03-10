---
artifact_kind: workstream
id: WS-003
title: Agentic Harness
work_type: spike
status: active
owner:
created: 2026-03-10
updated: 2026-03-10
tags: []
# Optional later note: paths that become relevant once framing work starts.
affected_paths:
  - docs/delivery/eval-harness-rfc-sections-1-10.md
  - docs/delivery/eval-harness-rfc-sections-11-15.md
  - docs/evergreen/eval-vocabulary.md
  - docs/evergreen/eval-support-semantics.md
  - docs/evergreen/eval-scenario-taxonomy.md
  - docs/evergreen/eval-failure-taxonomy.md
# Optional later note: components or subsystems involved in the work.
affected_components:
  - evaluation harness
  - agent orchestration
  - dataset authoring flow
blockers: []
depends_on:
  - WS-002
# Optional later note: durable docs that may need review or update.
evergreen_targets: []
adr_links: []
rfc_links:
  - docs/delivery/eval-harness-rfc-sections-1-10.md
  - docs/delivery/eval-harness-rfc-sections-11-15.md
validation_evidence: []
gate: none
# Optional later note: docs worth reading first once framing work begins.
context_dependencies:
  - docs/evergreen/mvp.md
  - docs/evergreen/eval-vocabulary.md
  - docs/evergreen/eval-support-semantics.md
  - docs/evergreen/eval-scenario-taxonomy.md
  - docs/evergreen/eval-failure-taxonomy.md
  - docs/delivery/eval-harness-rfc-sections-11-15.md
  - docs/workstreams/WS-002-semantic-lock/workstream.md
# Optional later note: useful commands discovered during framing or execution.
commands: []
# Optional later note: constraints or non-goals to keep visible.
boundaries:
  - Treat `agentic-harness` as internal infrastructure or tooling work, not a user-visible MVP feature.
  - Inherit the locked evaluation semantics from WS-002 rather than redefining support states, scenario classes, or failure classes locally.
  - Do not broaden supported inputs or product scope beyond the MVP in docs/evergreen/mvp.md.
---

# Summary
Frame the first internal `agentic-harness` work slice so the repo can decide what an agent-driven harness should own, how it relates to the eval-harness phases, and what concrete implementation boundary should be taken first.

## Objective
Define the first coherent internal deliverable for `agentic-harness` and the constraints around it clearly enough that later implementation work can either proceed in this workstream or split into a narrower follow-on with a stable scope.

## Non-goals
- Claim a new user-visible MVP capability.
- Reopen semantic-lock decisions already captured in WS-002.
- Start CI/release-gating or broad productionization work before the first internal harness slice is framed.

## Current status
WS-002 completed the semantic lock and froze the evaluation semantics needed for downstream harness work. There is not yet a dedicated runtime implementation for `agentic-harness`, and the repo still has no implemented eval harness runtime, dataset loader, or agent orchestration layer. A reflective technical note now captures the reasoning and principles behind the semantic-lock and agent-first docs-routing refactors so later harness framing can reuse those lessons rather than rediscover them.

## Next step
- Review the Phase 2 and Phase 3 eval-harness RFC sections and write down the first concrete internal deliverable that `agentic-harness` will own before implementation starts.

## Relevant context
- paths: `docs/delivery/eval-harness-rfc-sections-1-10.md`, `docs/delivery/eval-harness-rfc-sections-11-15.md`, `docs/workstreams/WS-002-semantic-lock/workstream.md`
- components: evaluation harness, agent orchestration, dataset authoring flow
- constraints: internal-only workstream, semantic-lock outputs remain authoritative, first deliverable should be one coherent slice rather than a broad multi-phase bundle
- read first: `docs/evergreen/mvp.md`, `docs/evergreen/eval-vocabulary.md`, `docs/evergreen/eval-support-semantics.md`, `docs/delivery/eval-harness-rfc-sections-11-15.md`, `docs/workstreams/WS-002-semantic-lock/workstream.md`

## Workflow steps
1. Frame the internal `agentic-harness` scope and decide the first concrete deliverable.
2. Shape the implementation and validation approach for that first slice.
3. Execute the chosen slice or spin out a narrower implementation workstream if framing shows the current scope is still too broad.

## Validation
- Record which eval-harness phase and deliverable this workstream owns first.
- Confirm the proposed scope does not redefine evergreen evaluation semantics or MVP product scope.
- Capture any follow-on split if the work needs a narrower implementation workstream after framing.
- Keep reflective notes explicitly non-canonical and linked back to evergreen authority docs.

## Worklog
### 2026-03-10
- Initialized WS-003 as an internal `agentic-harness` spike after WS-002 completed the semantic lock.
- Framed the workstream around deciding the first coherent internal deliverable for agent-driven harness work.
- Added `agentic-focused-refactor.md` as a standalone technical reflection note capturing the reasoning, methods, and extracted principles behind the recent semantic-lock and agent-first docs-routing refactors.

## Linked artifacts
- Semantic lock predecessor: `docs/workstreams/WS-002-semantic-lock/workstream.md`
- RFC core: `docs/delivery/eval-harness-rfc-sections-1-10.md`
- RFC operating model: `docs/delivery/eval-harness-rfc-sections-11-15.md`
- Evergreen semantic docs: `docs/evergreen/eval-vocabulary.md`, `docs/evergreen/eval-support-semantics.md`, `docs/evergreen/eval-scenario-taxonomy.md`, `docs/evergreen/eval-failure-taxonomy.md`
- Technical reflection note: `docs/workstreams/WS-003-agentic-harness/agentic-focused-refactor.md`
