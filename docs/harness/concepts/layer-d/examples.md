# Examples

## Purpose

This document provides **worked Layer D examples** for the lifecycle control plane.

The goal is not to enumerate every possible path. The goal is to show how to apply:

- the universal Layer D state set,
- task-scope versus workstream-scope lifecycle records,
- separation from Layer A, Layer B, and Layer C,
- and common transition patterns in operationally realistic cases.

Use:

- `states.md` for the canonical meanings of each state,
- `schema.md` for the normative field contract,
- `scope-and-transitions.md` for lifecycle scope and transition principles,
- this file for concrete examples.

## How to read these examples

In each case, keep four questions separate:

1. **What is the shape of the work?** → Layer A
2. **How should the agent work now?** → Layer B
3. **What control regime or workstream wrapper applies?** → Layer C
4. **What is the current execution-control status?** → Layer D

These examples focus on Layer D while keeping the other layers visible enough to preserve the boundary.

---

## Example 1: newly captured task is not yet actionable

### Situation

A request has been captured, but the current slice is not yet bounded and the task still lacks enough context to proceed responsibly.

### Why this is `draft`

The item exists, but it is not yet actionable.

This is not:
- `blocked`, because the task has not yet become truly executable and then lost a dependency,
- `active`, because there is no concrete executable next step yet,
- or `checkpoint`, because no review boundary is active.

### Layer sketch

- **Layer A** is still incomplete
- **Layer B** may not be chosen yet
- **Layer C** is usually baseline / absent at this point
- **Layer D** is `draft`

### Layer D record

```yaml
layer_d:
  state: draft
  phase: intake
  next_step: bound the current slice and fill the required Layer A core
  entered_at: 2026-03-07T10:00:00Z
  updated_at: 2026-03-07T10:05:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs: []
  decision_ref: null
  lifecycle_scope: task
```

### Important distinction

`draft` means not yet actionable in the current scope. It does not mean abandoned or low priority.

---

## Example 2: task is executable now

### Situation

A bounded implementation slice has been classified, routed, and is ready to proceed.

### Why this is `active`

The current slice can move forward now and has a concrete next step.

### Layer sketch

- **Layer A** indicates implementation-ready bounded work
- **Layer B** is `routine_implementer`
- **Layer C** remains baseline
- **Layer D** is `active`

### Layer D record

```yaml
layer_d:
  state: active
  phase: implementation
  next_step: implement bounded schema refactor and update associated tests
  entered_at: 2026-03-07T11:00:00Z
  updated_at: 2026-03-07T11:10:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs: []
  decision_ref: null
  lifecycle_scope: task
```

### Important distinction

`active` does not say anything about the mode beyond “may proceed.” The current working posture still belongs to Layer B.

---

## Example 3: dependency block after work became actionable

### Situation

A migration slice was ready to proceed, but an upstream schema change has not landed.

### Why this is `blocked`

The slice cannot continue because a real dependency is unresolved.

### Layer sketch

- **Layer A** still describes the same migration slice
- **Layer B** may remain `migration_operator`
- **Layer C** may still include a control profile, but that does not determine the current state
- **Layer D** is `blocked`

### Layer D record

```yaml
layer_d:
  state: blocked
  phase: waiting_on_dependency
  next_step: resume migration step when upstream schema lands
  entered_at: 2026-03-07T12:00:00Z
  updated_at: 2026-03-07T12:15:00Z

layer_d_companion:
  blocking_reason: upstream schema dependency not yet merged
  unblock_condition: upstream schema change merged and available in main branch
  checkpoint_reason: null
  approval_ref: null
  evidence_refs: []
  decision_ref: null
  lifecycle_scope: task
```

### Important distinction

`blocked` is not automatically a review or approval state. It may be purely dependency-driven.

---

## Example 4: review boundary becomes active

### Situation

A design slice has reached the point where continuation depends on architecture interpretation.

### Why this is `checkpoint`

The current gate is a review / interpretation boundary.

This is not `awaiting_approval`, because the issue is not a hard signoff gate yet.

### Layer sketch

- **Layer A** shows elevated interpretation burden
- **Layer B** may still be `contract_builder`
- **Layer C** includes a review-bearing control profile
- **Layer D** is `checkpoint`

### Layer D record

```yaml
layer_d:
  state: checkpoint
  phase: architecture_review
  next_step: await review outcome and update contract accordingly
  entered_at: 2026-03-07T13:00:00Z
  updated_at: 2026-03-07T13:20:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: architecture interpretation required before continuation
  approval_ref: null
  evidence_refs:
    - docs/rfcs/segmentation-contract.md
    - reports/design-tradeoff-summary.md
  decision_ref: null
  lifecycle_scope: task
```

### Important distinction

A review-bearing control profile does not automatically mean the item is currently at `checkpoint`. It only means that checkpoint transitions may occur at defined boundaries.

---

## Example 5: explicit approval gate is active

### Situation

A rollout-sensitive migration has reached the go/no-go boundary and cannot continue without signoff.

### Why this is `awaiting_approval`

The active gate is formal approval, not merely review.

### Layer sketch

- **Layer A** indicates elevated blast radius, hard reversibility, and sensitivity
- **Layer B** is `migration_operator`
- **Layer C** includes an approval-bearing control profile
- **Layer D** is `awaiting_approval`

### Layer D record

```yaml
layer_d:
  state: awaiting_approval
  phase: release_gate
  next_step: obtain go/no-go approval for rollout packet
  entered_at: 2026-03-07T14:00:00Z
  updated_at: 2026-03-07T14:20:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: approval granted by release authority
  checkpoint_reason: null
  approval_ref: approvals/release-gate-2026-03-07
  evidence_refs:
    - reports/release-readiness.md
    - docs/runbooks/rollback.md
  decision_ref: null
  lifecycle_scope: task
```

### Important distinction

An approval-bearing control profile does not mean the task is always `awaiting_approval`. It only means approval becomes the correct state when that boundary is actually active.

---

## Example 6: validation is now the dominant activity

### Situation

An optimization slice has finished implementation and is now running benchmark comparison against baseline.

### Why this is `validating`

The dominant current work is evidence generation and assessment.

### Layer sketch

- **Layer A** indicates heavy validation burden
- **Layer B** may still be `optimization_tuner` or may have rerouted depending on how the work is organized
- **Layer C** may still be baseline
- **Layer D** is `validating`

### Layer D record

```yaml
layer_d:
  state: validating
  phase: benchmark_run
  next_step: collect benchmark results and compare against baseline
  entered_at: 2026-03-07T15:00:00Z
  updated_at: 2026-03-07T15:30:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs:
    - reports/benchmark-run-2026-03-07.md
  decision_ref: null
  lifecycle_scope: task
```

### Important distinction

`validating` is not just “tests exist.” It means validation or observation is the dominant current posture.

---

## Example 7: validation creates more work

### Situation

Benchmark evidence shows the optimization target was not met. The slice must return to active execution.

### Transition pattern

`validating -> active`

### Layer D record after transition

```yaml
layer_d:
  state: active
  phase: followup_optimization
  next_step: revise caching strategy to address benchmark regression
  entered_at: 2026-03-07T16:00:00Z
  updated_at: 2026-03-07T16:10:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs:
    - reports/benchmark-run-2026-03-07.md
  decision_ref: decisions/benchmark-followup-2026-03-07
  lifecycle_scope: task
```

### Important distinction

Validation is not a terminal ritual. It may reopen active work when findings require further execution.

---

## Example 8: scoped task is complete

### Situation

A bounded refactor slice has been implemented, preservation evidence is sufficient, and no more work remains in the current scope.

### Why this is `complete`

The current tracked scope is done.

### Layer sketch

- **Layer A** still described the bounded slice
- **Layer B** may have been `refactor_surgeon`
- **Layer C** may remain baseline
- **Layer D** is `complete`

### Layer D record

```yaml
layer_d:
  state: complete
  phase: null
  next_step: null
  entered_at: 2026-03-07T17:00:00Z
  updated_at: 2026-03-07T17:15:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs:
    - reports/refactor-preservation-check.md
  decision_ref: decisions/task-closure-2026-03-07
  lifecycle_scope: task
```

### Important distinction

`complete` is scoped completion. It does not imply that the entire parent initiative or workstream is finished.

---

## Example 9: intentionally terminated work

### Situation

A research slice is closed because the direction is explicitly dropped in favor of another approach.

### Why this is `cancelled`

The work is intentionally terminated in its current scope.

### Layer D record

```yaml
layer_d:
  state: cancelled
  phase: null
  next_step: null
  entered_at: 2026-03-07T18:00:00Z
  updated_at: 2026-03-07T18:05:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs:
    - reports/research-comparison.md
  decision_ref: decisions/direction-change-2026-03-07
  lifecycle_scope: task
```

### Important distinction

`cancelled` is an explicit decision, not silent neglect.

---

## Example 10: workstream remains active while one child task is blocked

### Situation

A feature workstream continues progressing overall, but one child task is waiting on an external dependency.

### Why this matters

This example shows why workstream state must not be derived mechanically from child states.

### Workstream-scope Layer D

```yaml
layer_d:
  state: active
  phase: coordinated_execution
  next_step: continue active child slices and monitor blocked dependency
  entered_at: 2026-03-07T19:00:00Z
  updated_at: 2026-03-07T19:20:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs: []
  decision_ref: null
  lifecycle_scope: workstream
```

### Child task Layer D

```yaml
layer_d:
  state: blocked
  phase: waiting_on_dependency
  next_step: resume implementation when upstream schema lands
  entered_at: 2026-03-07T19:00:00Z
  updated_at: 2026-03-07T19:10:00Z

layer_d_companion:
  blocking_reason: upstream schema dependency not landed
  unblock_condition: upstream schema merged and released
  checkpoint_reason: null
  approval_ref: null
  evidence_refs: []
  decision_ref: null
  lifecycle_scope: task
```

### Important distinction

The workstream is still `active` because the coordinated effort can continue overall.

---

## Example 11: workstream waits at release approval after child execution tasks finish

### Situation

Child implementation tasks are complete, but the workstream as a whole is at a release gate.

### Why this is workstream-scope `awaiting_approval`

The hard signoff applies to the coordinated effort, not just one child slice.

### Workstream-scope Layer D

```yaml
layer_d:
  state: awaiting_approval
  phase: release_gate
  next_step: obtain go/no-go approval for workstream rollout
  entered_at: 2026-03-07T20:00:00Z
  updated_at: 2026-03-07T20:25:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: approval granted by release authority
  checkpoint_reason: null
  approval_ref: approvals/workstream-release-2026-03-07
  evidence_refs:
    - reports/workstream-readiness.md
    - docs/runbooks/workstream-rollback.md
  decision_ref: null
  lifecycle_scope: workstream
```

### Important distinction

The workstream may be `awaiting_approval` even when no child task is currently in that state.

---

## Example 12: workstream validates overall rollout after delivery

### Situation

A long-running feature has shipped and now the coordinated effort is in rollout observation.

### Why this is workstream-scope `validating`

The dominant work at workstream scope is evidence gathering and interpretation across the release as a whole.

### Workstream-scope Layer D

```yaml
layer_d:
  state: validating
  phase: rollout_observation
  next_step: review rollout metrics and confirm acceptance thresholds
  entered_at: 2026-03-07T21:00:00Z
  updated_at: 2026-03-07T21:30:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs:
    - dashboards/release-metrics
    - reports/post-rollout-observation.md
  decision_ref: null
  lifecycle_scope: workstream
```

### Important distinction

This is not automatically “complete just because implementation is complete.” At workstream scope, validation may still be the dominant lifecycle state.

---

## Summary

These examples show the main Layer D patterns:

- not yet actionable work → `draft`
- executable work → `active`
- dependency stop → `blocked`
- review / interpretation boundary → `checkpoint`
- hard signoff boundary → `awaiting_approval`
- evidence-dominant work → `validating`
- scoped completion → `complete`
- explicit termination → `cancelled`
- task-scope and workstream-scope lifecycle may coexist
- workstream state must not be mechanically derived from child task states

The key rule throughout is:

- Layer C defines the regime,
- Layer D defines the current gate,
- and the tracked scope determines which Layer D record is meaningful.
