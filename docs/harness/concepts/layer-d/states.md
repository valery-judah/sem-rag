# Layer D States

## Purpose

This document defines the **eight canonical Layer D lifecycle states** used in the harness model.

Layer D records the **current execution-control status** of a task or workstream. It does not redefine:

- the current work shape from Layer A,
- the current operating mode from Layer B,
- or the control regime / workstream wrapper from Layer C.

Use this file to determine the correct canonical `state` value for a task-scope or workstream-scope lifecycle record.

## How to use this file

Use this file when you need to answer:

- what the current lifecycle state should be,
- whether a state label is being used correctly,
- whether two similar states such as `checkpoint` and `awaiting_approval` are being confused,
- or whether a task or workstream should move to a different canonical state.

Use:

- `phase` for workflow-local progression detail,
- `schema.md` for field definitions and validation expectations,
- `scope-and-transitions.md` for task/workstream scope rules and transition logic.

Do not add new universal states for workflow-local nuance that can live in `phase`, `next_step`, companion fields, or linked artifacts.

## Universal state set

Layer D uses exactly these canonical states:

- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

This set is intentionally small. It covers the minimum shared execution-control distinctions needed across task slices and workstreams:

- not yet actionable,
- executable now,
- unable to proceed,
- paused for review or interpretation,
- stopped at an explicit signoff gate,
- dominated by validation,
- done within scope,
- or intentionally terminated.

## State reference table

| State | Meaning | Use when | Usually avoid when | Typical next states |
|---|---|---|---|---|
| `draft` | Exists, but not yet actionable | the slice is captured but not yet ready to execute | the next step is already executable | `active`, `cancelled` |
| `active` | May proceed now | work can move forward immediately | a blocker, review gate, or approval gate is actually active | `blocked`, `checkpoint`, `awaiting_approval`, `validating`, `complete`, `cancelled` |
| `blocked` | Cannot proceed because of an unresolved dependency or condition | the next step is not executable until something changes | the item is really waiting for review or approval rather than blocked by dependency | `active`, `cancelled` |
| `checkpoint` | Paused at a review or interpretation boundary | continuation depends on review, disposition, or interpretation | explicit signoff is the real gate | `active`, `awaiting_approval`, `complete`, `cancelled` |
| `awaiting_approval` | Waiting on explicit signoff | a hard go/no-go or formal approval gate is active | the item is only waiting for ordinary review or interpretation | `active`, `validating`, `complete`, `cancelled` |
| `validating` | Validation or observation is now the dominant activity | evidence generation, verification, or observation is the main remaining work | execution or debugging is still dominant | `active`, `checkpoint`, `awaiting_approval`, `complete`, `cancelled` |
| `complete` | Done within the declared scope | the scoped work is finished and accepted as done | further execution remains in the same scope | none |
| `cancelled` | Intentionally terminated within the current scope | work is explicitly stopped, dropped, or superseded | the item is merely stalled or forgotten | none |

## 1. `draft`

### Meaning

The work item exists, but is not yet fully actionable.

### Use when

Use `draft` when:

- the request has been captured but not fully framed,
- the current slice has not yet been bounded,
- required classification is still missing,
- essential context is still absent,
- or the first executable next step has not yet been established.

### Do not use when

Do not use `draft` when:

- the next step is already executable,
- the item was executable and later became blocked,
- or the real issue is a review or approval gate.

### Typical companion fields

Typical supporting fields:

- `next_step` pointing to clarification or slice-bounding work,
- optional notes about missing context,
- sometimes `phase` indicating intake or framing.

### Typical next states

Typical next states:

- `active` once the slice is actionable,
- `cancelled` if the request is dropped or superseded before execution begins.

## 2. `active`

### Meaning

The task or workstream may proceed now.

### Use when

Use `active` when:

- no blocker currently prevents continuation,
- no review boundary is currently active,
- no explicit approval gate is currently active,
- and the `next_step` is executable now.

### Do not use when

Do not use `active` when:

- a blocker prevents progress,
- continuation depends on review or interpretation,
- continuation depends on explicit signoff,
- or validation/observation has become the dominant current work.

### Typical companion fields

Typical supporting fields:

- concrete `next_step`,
- current `phase`,
- optional evidence refs as context.

### Typical next states

Typical next states:

- `blocked`,
- `checkpoint`,
- `awaiting_approval`,
- `validating`,
- `complete`,
- `cancelled`.

## 3. `blocked`

### Meaning

The item cannot proceed because an unresolved dependency or condition prevents continuation.

### Use when

Use `blocked` when:

- required context is missing after the item became actionable,
- an external dependency is unavailable,
- a prerequisite deliverable has not landed,
- an environment or infrastructure issue prevents progress,
- or another concrete dependency must be resolved before the next step can execute.

### Do not use when

Do not use `blocked` when:

- the item is waiting for review or interpretation,
- the item is waiting on formal approval,
- the item is merely early and not yet actionable,
- or the state is being used as a vague placeholder for uncertainty.

### Typical companion fields

Typical supporting fields:

- `blocking_reason`,
- `unblock_condition`,
- concrete `next_step` such as escalating, waiting for input, or resuming after dependency resolution.

### Typical next states

Typical next states:

- `active` once the blocker clears,
- `cancelled` if the work is intentionally terminated.

## 4. `checkpoint`

### Meaning

Work is paused at a review or interpretation boundary before continuation.

### Use when

Use `checkpoint` when:

- a review packet is ready,
- findings need interpretation,
- design tradeoffs need disposition,
- acceptance evidence exists but requires human judgment,
- or a required review/control boundary is active before work may continue.

### Do not use when

Do not use `checkpoint` when:

- the real gate is explicit signoff,
- the item is blocked on a dependency rather than paused for review,
- or validation is the dominant activity and no actual pause boundary is active.

### Typical companion fields

Typical supporting fields:

- `checkpoint_reason`,
- packet or evidence references,
- `decision_ref` after the checkpoint resolves,
- concrete `next_step` such as submit packet, await review outcome, or apply review decision.

### Typical next states

Typical next states:

- `active` after review outcome permits continuation,
- `awaiting_approval` if formal signoff becomes the next gate,
- `complete` if the checkpoint closes the work,
- `cancelled` if the checkpoint leads to intentional termination.

## 5. `awaiting_approval`

### Meaning

Work is waiting on explicit signoff at a hard approval gate.

### Use when

Use `awaiting_approval` when:

- the control regime requires formal approval,
- a go/no-go boundary has been reached,
- continuation is not permitted without signoff,
- or closure itself requires explicit approval.

### Do not use when

Do not use `awaiting_approval` when:

- the item only needs review or interpretation,
- the approval requirement is theoretical but the gate is not yet active,
- or the item is blocked for some other reason.

### Typical companion fields

Typical supporting fields:

- `approval_ref` once submitted or decided,
- evidence refs,
- concrete `next_step` such as submit approval packet, await decision, or apply approval outcome.

### Typical next states

Typical next states:

- `active` after approval,
- `validating` if post-approval observation dominates,
- `complete` if approval closes the scope,
- `cancelled` if approval is denied and the work is intentionally terminated.

## 6. `validating`

### Meaning

Validation, verification, or observation is now the dominant activity.

### Use when

Use `validating` when:

- test execution and interpretation dominate,
- offline evaluation dominates,
- rollout observation dominates,
- benchmark comparison dominates,
- acceptance evidence collection dominates,
- or production confirmation is the current primary work.

### Do not use when

Do not use `validating` when:

- execution or debugging still dominates,
- validation is only incidental rather than primary,
- or the item is really paused at a checkpoint or approval gate.

### Typical companion fields

Typical supporting fields:

- `evidence_refs`,
- concrete `next_step` describing the validation action,
- optional local `phase` naming the validation cycle.

### Typical next states

Typical next states:

- `complete` if validation succeeds and scope is done,
- `active` if findings require more work,
- `checkpoint` if interpretation is required,
- `awaiting_approval` if signoff becomes the next active boundary,
- `cancelled` if the slice is intentionally terminated.

## 7. `complete`

### Meaning

The work is done within the declared scope.

### Use when

Use `complete` when:

- the scoped objective has been satisfied,
- required evidence has been gathered and accepted,
- required review or approval has been resolved,
- and no further execution remains inside the current scope.

### Do not use when

Do not use `complete` when:

- further execution remains in the same slice or workstream scope,
- the work is only paused,
- or completion is being used to hide unresolved next actions.

### Typical companion fields

Typical supporting fields:

- evidence refs,
- acceptance summary,
- decision ref,
- optional closeout note.

### Typical next states

Typical next states:

- none.

Completion is terminal for the current scope.

## 8. `cancelled`

### Meaning

The work was intentionally terminated and will not continue in the current scope.

### Use when

Use `cancelled` when:

- the task is explicitly dropped,
- the slice is superseded by another slice,
- the work is terminated by decision,
- or the current scope is intentionally abandoned.

### Do not use when

Do not use `cancelled` when:

- the item is merely blocked,
- the item is paused pending review,
- or the work is passively neglected rather than intentionally stopped.

### Typical companion fields

Typical supporting fields:

- `decision_ref`,
- optional rationale,
- successor or replacement reference when relevant.

### Typical next states

Typical next states:

- none.

Cancellation is terminal for the current scope.

## Important distinctions

### `checkpoint` is not `awaiting_approval`

- `checkpoint` means pause for review, interpretation, or disposition.
- `awaiting_approval` means an explicit signoff gate is active.

These often occur in the same workstream, but they are not interchangeable.

### `validating` is not “some tests exist”

Use `validating` only when validation or observation is the dominant current activity.

A task that is still mainly executing code and happens to run tests is usually still `active`.

### `blocked` is not automatically HITL

A blocked item may be waiting on infrastructure, external context, another team, or a missing prerequisite. It is not necessarily waiting on reviewer or approver action.

### `complete` is scoped completion

`complete` means complete **within the declared current scope**.

A task slice may be complete while the broader workstream remains active.

### `cancelled` is intentional termination

`cancelled` should reflect an explicit stop or replacement decision, not passive abandonment or stale maintenance.

## Not a substitute for Layers A, B, or C

Layer D states must not be used as substitutes for other layers.

Examples of incorrect substitutions:

- `validating` is not a Layer B mode such as `quality_evaluator`
- `checkpoint` is not a `reviewed` control profile
- `awaiting_approval` is not a `change_controlled` control profile
- `feature_cell` is not a lifecycle state

Use:

- Layer A for work shape,
- Layer B for operating posture,
- Layer C for workstream containers and control profiles,
- Layer D for current lifecycle gate/status.

## Minimal examples

### Example 1: task-scope design review pause

A slice is defining an interface boundary and has reached the point where architecture review is required before continuing.

Use:

- `state = checkpoint`
- `checkpoint_reason = architecture review required before implementation`

### Example 2: migration go/no-go gate

A rollout-sensitive migration step has been prepared and cannot continue until explicit signoff is granted.

Use:

- `state = awaiting_approval`
- `approval_ref = <approval packet or decision ref>` once submitted or decided

### Example 3: rollout observation

Implementation is largely done and the current dominant work is observing staged rollout behavior and collecting acceptance evidence.

Use:

- `state = validating`

### Example 4: concrete external blocker

A task was actionable but is now waiting on an upstream schema change.

Use:

- `state = blocked`
- `blocking_reason = upstream schema change not yet landed`
- `unblock_condition = schema change merged and available in target environment`

### Example 5: workstream-scope and task-scope coexistence

A `feature_cell` workstream remains active overall, but one child task is currently blocked on a dependency.

Use:

- workstream-scope `state = active`
- child task `state = blocked`

Do not derive the workstream state mechanically from the child task state.

## Summary

Use the eight canonical Layer D states to record the **current lifecycle control status** of a task or workstream.

Keep the state set small, use companion fields for specificity, use `phase` for workflow-local progression, and keep Layer D cleanly separated from:

- Layer A classification,
- Layer B operating mode,
- and Layer C control-profile / container context.
