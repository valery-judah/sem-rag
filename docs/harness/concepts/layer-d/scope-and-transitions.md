# Scope and Transitions

## Purpose

This document defines the **scope rules** and **transition principles** for Layer D.

Layer D records the **current lifecycle control status** of work. This file explains:

- how Layer D applies at **task scope** and **workstream scope**,
- how to reason about transitions between states without inventing a large universal state machine,
- how Layer D interacts with Layer C control profiles,
- and which transition patterns are canonical enough to standardize across the harness.

This document does **not** redefine the universal state meanings. Use `states.md` for state definitions and `schema.md` for canonical field structure.

## Core rule

Layer D answers:

> What is the current execution-control status of this tracked item?

It does **not** answer:

- what kind of work this is,
- how the agent should work now,
- what control regime applies in general,
- or what the full workflow semantics are.

In the layered model:

- **Layer A** describes the current work slice.
- **Layer B** selects the current operating mode.
- **Layer C** defines workstream containers and control profiles.
- **Layer D** records the current lifecycle gate/status inside that context.

A useful shorthand:

- **Layer C owns the regime**
- **Layer D owns the current gate**

## How to use this file

Use this file when you need to answer questions such as:

- Should this Layer D record exist at task scope, workstream scope, or both?
- Can a workstream be `active` while one child task is `blocked`?
- What transitions are normal from `checkpoint` or `awaiting_approval`?
- When should validation become the dominant state?
- How should Layer C review or approval obligations affect Layer D without collapsing into state names?

Use:

- `states.md` for canonical state meanings,
- `schema.md` for canonical fields and invariants,
- this file for lifecycle scope and transition logic.

## Lifecycle scope model

Layer D may be tracked at two distinct scopes:

- **task scope**
- **workstream scope**

These scopes are related, but they are not interchangeable.

### Task scope

Task-scope Layer D is the default.

Use task-scope tracking when the item being controlled is a single current work slice with one current Layer B mode and one concrete `next_step`.

Typical task-scope questions:

- can this slice proceed now?
- is it blocked?
- is it at review?
- is it awaiting approval?
- is validation now dominant?
- is this slice complete?

### Workstream scope

Workstream-scope Layer D becomes relevant when a Layer C `feature_cell` exists and the workstream itself has meaningful lifecycle control status beyond any one child task.

Typical workstream-scope questions:

- is the workstream active overall?
- is the workstream waiting on a workstream-level checkpoint?
- is an approval boundary holding the workstream, even if child implementation tasks are done?
- is the workstream validating overall rollout readiness or rollout outcomes?
- is the workstream closed or intentionally cancelled?

### Default rule

Track Layer D at **task scope by default**.

Add workstream-scope Layer D only when the workstream itself has lifecycle status that matters operationally.

Do not create workstream-level lifecycle records just because a workstream card exists.

## Scope interaction rules

### Rule 1. Task and workstream scope may coexist

When `feature_cell` is present, it is normal to track:

- task-scope Layer D for the active slice,
- and workstream-scope Layer D for the overall workstream.

This is often the clearest model.

### Rule 2. Workstream state must not be derived mechanically from child task states

Do **not** assume:

- if one child task is `blocked`, the workstream is `blocked`,
- if one child task is `complete`, the workstream is `complete`,
- if all known children are `complete`, the workstream is automatically `complete`.

The workstream has its own control meaning.

Examples:

- a workstream may be `active` while one child task is `blocked`,
- a workstream may be `checkpoint` while some child tasks are still `active`,
- a workstream may be `awaiting_approval` after child implementation tasks are done,
- a workstream may be `validating` during rollout observation even if no single child task is currently `validating`.

### Rule 3. Scope should follow the controlled object

Use task scope when the gate applies to the current slice.

Use workstream scope when the gate applies to the whole coordinated effort.

Examples:

- architecture review for one design slice → task scope
- go/no-go release approval for a staged migration → often workstream scope
- rollout observation for one bounded deployment slice → task scope or workstream scope depending on how the effort is organized
- closure of a long-running feature effort → workstream scope

### Rule 4. Scope is not a hierarchy of truth

Neither task scope nor workstream scope is inherently more “real.”

Each answers lifecycle questions about a different tracked object.

## Relationship to Layer C

Layer C and Layer D must remain sharply separated.

### Layer C defines the regime

Layer C may indicate:

- a `feature_cell` workstream container,
- a non-baseline `control_profile`,
- review obligations,
- approval obligations,
- evidence or traceability requirements,
- rollback expectations.

These are **standing conditions** under which work proceeds.

### Layer D defines the current gate

Layer D records whether the item is currently:

- active,
- blocked,
- paused for checkpoint,
- awaiting approval,
- validating,
- complete,
- or cancelled.

### Important non-equivalences

Do **not** collapse these:

- `reviewed` != `checkpoint`
- `change_controlled` != `awaiting_approval`
- `high_assurance` != `awaiting_approval`
- `feature_cell` != any state
- `control_profile` != current status

A task or workstream can have:

- a review-bearing control profile and still be `active`,
- an approval-bearing control profile and still be `active`,
- a `feature_cell` and still be `draft`,
- no control profile and still be `blocked`.

### Operational rule

Layer C may make certain Layer D states **more likely**.

Layer C does not determine the current state by itself.

## HITL mapping

Layer D is the operational place where human-in-the-loop boundaries become visible.

A useful minimal mapping:

- **Autonomous zone** → usually `active`
- **Review / interpretation zone** → usually `checkpoint`
- **Approval zone** → usually `awaiting_approval`

This mapping is useful, but it is not complete.

### `blocked` is not automatically HITL

A blocked item may be waiting on:

- missing dependency,
- external deliverable,
- environment issue,
- unavailable context,
- system outage,
- repository access,
- or any other non-review condition.

Do not treat all `blocked` work as review work.

### `validating` is not automatically HITL

Validation may be mostly autonomous if evidence collection is underway.

It only becomes a review or approval boundary if interpretation or signoff is actually required.

## Transition principles

Layer D is not a giant universal state machine.

Use **transition principles** instead of trying to hard-code every path.

### Principle 1. Transition only when the dominant control situation changes

A state transition should reflect a real change in current control status.

Examples:

- from not yet actionable to actionable,
- from executable to blocked,
- from active execution to review checkpoint,
- from active execution to approval boundary,
- from execution to validation,
- from validation back to active because findings created more work,
- from validating to complete because the scoped work is accepted.

### Principle 2. Keep most detail in `phase`, reasons, and linked artifacts

Do not invent new universal states for every workflow nuance.

Use:

- `phase`
- `next_step`
- `blocking_reason`
- `checkpoint_reason`
- `approval_ref`
- `decision_ref`
- linked evidence artifacts

to carry local detail.

### Principle 3. Non-terminal states should usually remain actionable

For non-terminal records, the next move should be visible.

That means:

- `active` should have a concrete next step,
- `blocked` should have a clear unblock condition where possible,
- `checkpoint` should indicate what review boundary is active,
- `awaiting_approval` should show what signoff is missing,
- `validating` should show what evidence is being gathered or interpreted.

### Principle 4. Completion is scoped

`complete` means:

- this tracked scope is done.

It does **not** mean:

- the whole initiative is done,
- the parent workstream is done,
- the broader roadmap is done.

Similarly, `cancelled` is scoped intentional termination.

## Canonical transition patterns

These are not exhaustive. They are the most useful shared patterns.

### Pattern 1. Intake / framing

Typical path:

`draft -> active`

Use when:

- the slice becomes actionable,
- the current mode is selected,
- and a concrete next step exists.

Alternative:

`draft -> cancelled`

Use when:

- the captured request is intentionally dropped,
- superseded,
- or found out-of-scope before execution begins.

### Pattern 2. Execution interruption

Typical path:

`active -> blocked`

Use when a real dependency or condition prevents continuation.

Typical return:

`blocked -> active`

Use when the blocking condition is removed.

Avoid:

- leaving the item `active` when it cannot proceed,
- using `blocked` without a concrete reason.

### Pattern 3. Review / interpretation boundary

Typical path:

`active -> checkpoint`

Use when continuation depends on review, interpretation, or disposition.

Common returns:

- `checkpoint -> active`
- `checkpoint -> awaiting_approval`
- `checkpoint -> complete`
- `checkpoint -> cancelled`

Which return is correct depends on the outcome.

### Pattern 4. Approval boundary

Typical path:

`active -> awaiting_approval`

or, in some workflows:

`checkpoint -> awaiting_approval`

Use when a hard signoff boundary becomes active.

Common returns:

- `awaiting_approval -> active`
- `awaiting_approval -> validating`
- `awaiting_approval -> complete`
- `awaiting_approval -> cancelled`

### Pattern 5. Validation-dominant work

Typical path:

`active -> validating`

Use when the dominant work is now:

- testing,
- benchmarking,
- rollout observation,
- acceptance evidence collection,
- or production confirmation.

Common returns:

- `validating -> complete`
- `validating -> active`
- `validating -> checkpoint`
- `validating -> awaiting_approval`
- `validating -> cancelled`

### Pattern 6. Closure

Typical paths:

- `active -> complete`
- `validating -> complete`
- `checkpoint -> complete`
- `awaiting_approval -> complete`

Use `complete` only when the scoped item is actually done.

### Pattern 7. Intentional termination

Typical paths:

- `draft -> cancelled`
- `active -> cancelled`
- `checkpoint -> cancelled`
- `awaiting_approval -> cancelled`
- `validating -> cancelled`

Use when the item is intentionally stopped rather than merely left stale.

## Transition anti-patterns

### 1. Encoding mode changes as state changes

Bad:
- changing state because the mode changed from `contract_builder` to `routine_implementer`

Mode changes belong to Layer B.
State changes belong to Layer D.

### 2. Encoding control-profile identity as state

Bad:
- treating `reviewed` as if it were a state
- treating `change_controlled` as if it were a state

These belong to Layer C.

### 3. Using `checkpoint` for every pause

A task is not at `checkpoint` merely because it is idle, paused, or waiting on a dependency.

Use `checkpoint` only when a real review/control pause is active.

### 4. Using `awaiting_approval` for ordinary review

Approval is a stronger condition than review or interpretation.

Do not collapse them.

### 5. Skipping `validating` when validation dominates

If the main work is evidence generation or verification, say so explicitly.

Do not leave the item in `active` just because code execution has technically finished.

### 6. Mechanical parent-state derivation

Do not compute workstream state from child states without judgment.

## Minimal examples

### Example 1: task-scope review boundary

A design slice under a review-bearing control profile finishes its draft and now requires architecture interpretation.

Task-scope Layer D:

```yaml
layer_d:
  state: checkpoint
  phase: architecture_review
  next_step: await review outcome and update contract accordingly
```

### Example 2: task-scope approval boundary

A migration slice reaches a cutover gate that requires explicit signoff.

Task-scope Layer D:

```yaml
layer_d:
  state: awaiting_approval
  phase: cutover_gate
  next_step: obtain release approval for cutover packet
```

### Example 3: task-scope validation

A bounded optimization slice has finished implementation and is now running benchmarks.

Task-scope Layer D:

```yaml
layer_d:
  state: validating
  phase: benchmark_run
  next_step: collect benchmark results and compare against baseline
```

### Example 4: workstream active while one child task is blocked

A feature workstream is still progressing overall, but one child task is waiting on an external dependency.

Workstream-scope Layer D:

```yaml
layer_d:
  state: active
  phase: coordinated_execution
  next_step: continue active child slices and monitor blocked dependency
```

Child task Layer D:

```yaml
layer_d:
  state: blocked
  phase: waiting_on_dependency
  next_step: resume implementation when upstream schema lands
```

### Example 5: workstream awaiting approval after child execution

Implementation tasks are complete, but release approval is still pending at workstream scope.

Workstream-scope Layer D:

```yaml
layer_d:
  state: awaiting_approval
  phase: release_gate
  next_step: obtain go/no-go approval for rollout
```

This does not require any child task to currently be `awaiting_approval`.

## Summary

Use Layer D scope and transitions to record the **current control status** of the tracked object:

- at task scope by default,
- at workstream scope when the workstream itself has meaningful lifecycle status,
- with Layer C kept separate as the regime layer,
- and with transitions driven by real control changes rather than taxonomy sprawl.
