

# Example Filled Workstream Card

This example shows what a filled workstream card can look like after a broad effort has been promoted into a `feature_cell`.

It is intentionally lightweight. The goal is to show:
- how the workstream stays focused on coordination rather than detailed execution,
- how child tasks are linked,
- how Layer C and Layer D look at workstream scope,
- how milestones, shared decisions, and next steps are recorded.

This example keeps the current workstream-card compatibility shape: `container` and `overlays` remain legacy harness-local Layer C shorthand. Canonical Layer C still uses `feature_cell` and `control_profile`.

```md
---
id: W-2026-03-segmentation
title: Hierarchical segmentation feature development
created_at: 2026-03-06
updated_at: 2026-03-06
owner: agent
state: active
phase: contract formation
next_step: Create child task for intermediate schema definition and link it to milestone: contract approval.
container: feature_cell
overlays: []
---

# Goal

Define, validate, and stage the first operational version of hierarchical segmentation for the retrieval pipeline.

# Scope Boundary

## In scope

- define the segmentation feature boundary for phase 1
- define the intermediate output schema used between parsing and segmentation
- specify acceptance conditions for the first segmentation slice
- create initial child tasks for schema, logic outline, and evaluation planning
- coordinate cross-slice decisions and handoffs

## Out of scope

- full production rollout
- advanced optimization of retrieval quality
- generalized document graph construction
- downstream UI changes
- all future segmentation variants beyond phase 1

## Completion condition

This workstream is complete when the phase-1 segmentation contract is defined, required child slices are completed, and the resulting design is accepted as ready for implementation and evaluation.

# Promotion Reason

Task-only tracking became inadequate because the work expanded into multiple coherent slices: schema definition, segmentation logic design, and evaluation planning. The effort also requires resumability across sessions and shared milestone tracking.

# Current Structure

## Active child tasks

- `T-2026-03-06-002` — Define intermediate schema acceptance contract
- `T-2026-03-06-003` — Outline segmentation logic boundaries for phase 1

## Planned / queued child tasks

- `T-2026-03-06-004` — Draft evaluation harness outline for segmentation acceptance
- `T-2026-03-06-005` — Prepare review packet for phase-1 contract approval

## Closed / superseded child tasks

- `T-2026-03-06-001` — Initial broad feature request; superseded by workstream promotion and child slicing

# Milestones / Sequencing

- current milestone: phase-1 contract definition in progress
- next milestone: contract approved for implementation-aligned slices
- important dependency or stage gate: intermediate schema must be reviewed before implementation child tasks begin

# Shared References

- `docs/harness/concepts/operational-playbook.md`
- `docs/harness/concepts/layer-a-taxonomy.md`
- `docs/harness/concepts/layer-b-operating-modes.md`
- `docs/harness/policies/routing-rules.md`
- `docs/rfc/hierarchical-segmentation.md`

# Layer C

- container: feature_cell
- overlays:

## Layer C rationale

`feature_cell` applies because this effort now spans multiple meaningful child slices and requires shared milestones and resumable coordination. No workstream-scope non-baseline control profile is active yet because review and approval boundaries are still local to specific child tasks.

# Layer D

- state: active
- phase: contract formation
- next_step: Create child task for intermediate schema definition and link it to milestone: contract approval.
- blocking_reason:
- unblock_condition:
- checkpoint_reason:
- approval_ref:
- evidence_refs:
- decision_ref:
- lifecycle_scope: workstream

## Current control condition

The workstream is active. Coordination can continue, and the next move is to complete the contract-shaping child slices before a milestone review boundary is introduced.

# Decisions / Risks / Notes

## Shared decisions

- phase 1 will use a bounded segmentation scope rather than attempting full hierarchical graph construction
- the first milestone is contract definition, not implementation

## Shared risks

- schema design may drift if child tasks proceed without a shared acceptance boundary
- evaluation planning may become premature if contract questions remain unresolved
- broad feature pressure may cause accidental scope expansion beyond phase 1

## Handoff / coordination notes

- keep task titles narrow and slice-specific
- do not create implementation tasks until the contract milestone is reviewed
- if the schema task reveals unresolved interface ambiguity, route affected slices through `contract_builder` rather than `routine_implementer`

# Workstream Log

## 2026-03-06

- promoted initial broad segmentation request into a `feature_cell`
- created initial child-task structure for schema and logic-definition slices
- set current milestone to phase-1 contract formation
- next coordination move is to add the schema child task and keep the workstream active until review is needed

# Closure

## Acceptance basis

The workstream will be considered complete when all required phase-1 contract and planning child tasks are complete, the contract milestone has been reviewed, and the effort is either accepted as ready for implementation or intentionally closed with a documented decision.

## Closure notes

Not yet complete.
```

## Why this example is shaped this way

A few things are deliberate here:

- The workstream card does not try to duplicate detailed child-task logs.
- The goal and scope boundary are explicit, so another agent can tell what belongs here.
- Layer C is minimal: only the `feature_cell` container is active.
- Layer D is workstream-scoped and answers only the control question for the larger effort.
- The next step is coordination-oriented rather than implementation-oriented.

## What to notice

This example is a good reference when:
- a broad effort has clearly split into multiple slices,
- the agent needs to coordinate child tasks without losing the larger goal,
- the effort is still active but not yet at a workstream-level checkpoint,
- the workstream should remain lightweight and readable.
