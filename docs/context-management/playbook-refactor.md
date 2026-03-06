# Playbook Refactor Plan

## Summary

This refactor exists to make the feature-playbook workflow easier for agents to execute, resume, and review. The target improvements are:

- agent legibility
- resumable execution
- progress tracking
- blocker visibility
- rollout evidence

This pass does not change feature-contract authority. The existing model remains in place: `01_rfc.md` stays normative for feature behavior, while the playbook and templates define how that behavior is planned, executed, and tracked.

## Current State

The current playbook stack is structurally sound, but it is still optimized more for documentation completeness than for agent execution.

- `docs/context-management/feature-playbooks/00_playbook.md` defines the artifact sequence, required/optional docs, and documentation-level authority, but it does not define a strong live execution flow for agents.
- `docs/context-management/feature-playbooks/templates/04_workplan.template.md` supports PR slicing at a high level, but it is too thin to act as a durable handoff and resume surface across multiple agent runs.
- `docs/context-management/feature-playbooks/templates/06_rollout.template.md` is currently only a stub and does not define measurable rollout stages or evidence expectations.
- `docs/03_agent_protocol.md` already expects agents to update workplan status as part of each iteration, but the current workplan template does not strongly support that behavior.
- `docs/PLANS.md` already serves as a repo-level router for active and historical plans, and it should remain that way rather than becoming a second execution tracker.

## Problems To Solve

- There is no canonical live-status surface inside a feature folder.
- Handoff and resume support for the next agent run is weak.
- There is no standard place to record blockers, assumptions, and execution evidence.
- Rollout planning is disconnected from measurable stage gates.
- The templates do not tell an agent what to read first or when design/workplan docs must be updated.

## Locked Decisions

- Live feature progress stays in `04_workplan.md`.
- The playbook should optimize for attended-handoff execution, not fully unattended autonomy.
- The artifact set stays lean; do not add `07_status.md`.
- `01_rfc.md` remains normative for behavior.
- `06_rollout.md` owns rollout-stage evidence only.
- `docs/PLANS.md` remains repo-level routing only.

## Planned Changes

### Workstream A: `00_playbook.md`

Update `docs/context-management/feature-playbooks/00_playbook.md` so the playbook explicitly states that the feature-doc set must support:

- design
- execution
- resumption

Add language that distinguishes artifact ownership more clearly:

- `01_rfc.md` owns behavior and invariants
- `04_workplan.md` owns live execution progress and handoff state
- `06_rollout.md` owns staged rollout evidence

Extend the documentation definition of done so it includes agent-operability expectations, not just artifact presence and internal consistency.

### Workstream B: `04_workplan.template.md`

Refactor `docs/context-management/feature-playbooks/templates/04_workplan.template.md` into the canonical live-status surface for a feature.

Add top-of-file metadata fields:

- `Status`
- `Current slice`
- `Last updated`
- `Primary blocker`

Replace the current loose PR outline with a fixed slice structure that requires:

- objective
- in scope
- out of scope
- depends on
- touched modules
- acceptance checks
- required commands/tests
- evidence to collect
- handoff notes
- exit criteria

Add two explicit progress sections:

- `Execution Log`
- `Next Recommended Slice`

The result should let a new agent identify the current slice, recent progress, evidence gathered, blockers, and the exact next starting point without reconstructing history from multiple docs.

### Workstream C: Supporting Templates

Update the supporting templates so they better scaffold agent execution.

For `docs/context-management/feature-playbooks/templates/00_context.template.md`:

- add feature entrypoints
- add minimum-read surfaces for an agent starting work on the feature

For `docs/context-management/feature-playbooks/templates/03_design.template.md`:

- add a section for frozen decisions
- add change triggers that tell the agent when a design or workplan update is required

For `docs/context-management/feature-playbooks/templates/06_rollout.template.md`:

- replace the current stub with a stage-gate structure that captures:
  - entry criteria
  - agent evidence
  - success metrics
  - abort triggers
  - owner/comms

### Workstream D: Repo-Level Alignment

Update `docs/01_artifact_contracts.md` so `04_workplan.md` formally owns live execution state in addition to PR sequencing and acceptance checks.

Update `docs/03_agent_protocol.md` so each agent run is expected to record:

- status updates
- execution evidence
- blockers

Those updates should be written back into the feature workplan rather than scattered across other docs.

## Verification

This refactor should be considered correct when all of the following are true:

- a new agent can identify the active slice and next step from a feature workplan alone
- a partially completed feature can be resumed without reconstructing history from multiple docs
- blocker state and open assumptions are visible in one screen near the top of `04_workplan.md`
- rollout docs can represent staged release gates with measurable evidence
- no contract authority moves out of `01_rfc.md`
- the revised templates remain consistent with `docs/PLANS.md` and `docs/03_agent_protocol.md`

## Assumptions

- This document is a control-plane planning artifact, not a replacement for the playbook itself.
- The first implementation pass should update the generic playbook and templates before retrofitting existing feature folders.
- An optional follow-up can test the new structure against one active feature workplan such as PDF pipeline or E2E.
