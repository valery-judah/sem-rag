---
artifact_kind: workstream
id: HR-003
title: Agentic Harness
work_type: refactor
status: active
owner:
created: 2026-03-10
updated: 2026-03-10
tags: []
affected_paths:
  - docs/harness/README.md
  - docs/harness/AGENTS.md
  - docs/harness/taxonomy/workstream-taxonomy.md
  - docs/harness/templates/workstream.md
  - docs/harness/playbooks/
  - docs/harness/scripts/
affected_components:
  - docs harness
  - agent-facing docs routing
  - workstream scaffolding
blockers: []
depends_on: []
evergreen_targets:
  - docs/README.md
adr_links: []
rfc_links: []
validation_evidence: []
gate: none
context_dependencies:
  - docs/harness-maintain/README.md
  - docs/harness/README.md
  - docs/harness/AGENTS.md
  - docs/harness/taxonomy/workstream-taxonomy.md
  - docs/harness/templates/workstream.md
  - docs/harness-maintain/HR-003-agentic-harness/agentic-focused-refactor.md
commands:
  - docs/harness/scripts/list-workstreams.sh
boundaries:
  - Treat `docs/harness/` as internal documentation infrastructure, not product runtime.
  - Do not redefine MVP scope or evergreen semantic authority from harness docs.
  - Keep durable truth in `docs/evergreen/`, doc_forge/runtime execution history in `docs/workstreams/`, and agentic-harness execution history in `docs/harness-maintain/`.
  - Prefer agent-useful routing and scaffolding improvements over broad process theory.
---

# Summary
Maintain the internal agentic documentation harness in `docs/harness/` so humans and agents have a coherent place for templates, playbooks, scripts, taxonomy, and local usage guidance.

## Objective
Keep `docs/harness/` aligned with actual repo usage so starting, updating, and maintaining workstreams and related docs requires minimal guesswork.

## Non-goals
- Build an evaluation harness runtime, dataset loader, or agent orchestration system.
- Reopen semantic-lock decisions already captured in evergreen evaluation docs.
- Move durable product or architecture authority into `docs/harness/`.

## Current status
`docs/harness/` now exists as a reusable docs scaffold with a local README, agent guide, taxonomy, templates, playbooks, and helper scripts. `docs/harness-maintain/` is the execution-history track for maintaining that scaffold. The current work is to keep the docs harness itself consistent, agent-usable, and correctly routed to repo authorities.

## Next step
- Audit the highest-leverage `docs/harness/` entry points and update any stale routing, naming, or scaffold guidance that no longer matches repo usage.

## Relevant context
- paths: `docs/harness/README.md`, `docs/harness/AGENTS.md`, `docs/harness/taxonomy/workstream-taxonomy.md`, `docs/harness/templates/workstream.md`, `docs/harness/playbooks/`, `docs/harness/scripts/`
- components: docs harness, workstream scaffolding, agent-facing routing
- constraints: internal docs infrastructure only, preserve authority split, avoid duplicating evergreen semantics
- read first: `AGENTS.md`, `docs/README.md`, `docs/harness/README.md`, `docs/harness/AGENTS.md`, `docs/harness/taxonomy/workstream-taxonomy.md`, `docs/harness/templates/workstream.md`

## Workflow steps
1. Keep `docs/harness/` aligned with how workstreams and related docs are actually created and maintained in this repo.
2. Update templates, playbooks, scripts, or local routing when agent friction or stale guidance appears.
3. Validate that harness changes preserve the docs authority split and improve day-to-day usability.

## Validation
- Verify harness docs route readers to the correct canonical or local authority docs.
- Verify taxonomy, template, and playbook language matches current repo usage.
- Record any follow-on cleanup if a harness script or scaffold still points to stale paths or workflows.
- Keep reflection notes or historical rationale non-canonical and separate from evergreen docs.

## Worklog
### 2026-03-10
- Reframed the agentic-harness workstream around the `docs/harness/` documentation system instead of evaluation-harness phase planning.
- Established `docs/harness-maintain/README.md` as the anchor for agentic-harness tasks and the `HR` track.
- Updated the workstream scope to track harness-local routing, scaffolding, templates, playbooks, and helper scripts.
- Kept `agentic-focused-refactor.md` as a supporting reflection artifact rather than the primary scope of the workstream.

## Linked artifacts
- Agentic-harness anchor: `docs/harness-maintain/README.md`
- Harness overview: `docs/harness/README.md`
- Harness local agent guide: `docs/harness/AGENTS.md`
- Workstream taxonomy: `docs/harness/taxonomy/workstream-taxonomy.md`
- Workstream template: `docs/harness/templates/workstream.md`
- Supporting reflection note: `docs/harness-maintain/HR-003-agentic-harness/agentic-focused-refactor.md`
