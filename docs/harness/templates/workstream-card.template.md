

# Workstream Card Template

Use this template when an effort has been promoted to a `feature_cell` and task-only tracking is no longer adequate.

A workstream card is the authoritative operational record for a long-running multi-slice effort. It coordinates child tasks, milestones, cross-slice decisions, shared risks, and workstream-scope control status. It is not a replacement for task cards and should not absorb detailed execution that belongs inside individual child tasks.

Current workstream cards still use legacy harness-local Layer C shorthand in frontmatter:

- `container: feature_cell`
- `overlays: []` for implied baseline control
- non-empty `overlays` to represent some non-baseline `control_profile`

Canonical Layer C remains the v2 model defined by `feature_cell` and `control_profile`.

## Usage notes

- Create one file per workstream in `docs/harness/active/workstreams/`.
- Use a workstream card only when the effort genuinely needs `feature_cell` treatment.
- Keep the workstream focused on coordination, sequencing, milestones, and cross-slice decisions.
- Keep detailed implementation, investigation, or evaluation work inside child task cards.
- If the workstream boundary becomes too broad or incoherent, split or narrow it rather than turning it into a bucket for every related task.

## Copyable template

```md
---
id: W-YYYY-MM-<slug>
title: <short workstream title>
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
owner: agent
state: active
phase:
next_step:
container: feature_cell
overlays: []
---

# Goal

<What larger effort this workstream is trying to achieve.>

# Scope Boundary

## In scope

- <what belongs to this effort>
- <...>

## Out of scope

- <what is intentionally excluded>
- <...>

## Completion condition

<What it means for the workstream to be complete at effort scope.>

# Promotion Reason

<Why task-only tracking became inadequate and why `feature_cell` now applies.>

# Current Structure

## Active child tasks

- <task id and short role>
- <...>

## Planned / queued child tasks

- <task id or placeholder if already known>
- <...>

## Closed / superseded child tasks

- <optional>
- <...>

# Milestones / Sequencing

- <current milestone or stage>
- <next milestone or stage>
- <important dependency or stage gate>

# Shared References

- <RFC, issue, PR, doc, decision, packet, evidence bundle, etc.>
- <...>

# Layer C

- container: feature_cell
- overlays:
  - <optional: review_gatekeeper>
  - <optional: governance_escalation>

## Layer C rationale

<Why workstream-scope Layer C shorthand does or does not apply.>

# Layer D

- state:
- phase:
- next_step:
- blocking_reason:
- unblock_condition:
- checkpoint_reason:
- approval_ref:
- evidence_refs:
  - <optional>
  - <optional>
- decision_ref:
- lifecycle_scope: workstream

## Current control condition

<Describe the current workstream-level control status in plain language if useful.>

# Decisions / Risks / Notes

## Shared decisions

- <decision or linked decision record>
- <...>

## Shared risks

- <risk affecting multiple child tasks>
- <...>

## Handoff / coordination notes

- <note for future sessions or agents>
- <...>

# Workstream Log

## YYYY-MM-DD

- <coordination action taken>
- <milestone or routing change>
- <child task created / closed / redirected>
- <what should happen next>

# Closure

## Acceptance basis

<How workstream completion will be established: all child slices complete, validation accepted, milestone approved, rollout approved, etc.>

## Closure notes

<Record final completion or cancellation context when the workstream ends.>
```

## Field guidance

### Frontmatter fields

#### `id`
Use a stable unique workstream identifier.

Recommended pattern:
- `W-YYYY-MM-<slug>`

Examples:
- `W-2026-03-segmentation`
- `W-2026-03-parser-migration`

#### `title`
The title should name the larger coordinated effort, not a single child slice.

Good:
- `Hierarchical segmentation feature development`
- `Hybrid parser migration`
- `Evaluation harness rollout`

Bad:
- `Fix parser bug`
- `Write one RFC section`
- `Run evaluation once`

#### `state`
Use only the Layer D lifecycle states defined by the harness.

Expected values:
- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

At workstream scope, these describe the control status of the effort as a whole.

#### `phase`
Use a short freeform description of the current effort-stage if useful.

Examples:
- `discovery coordination`
- `contract formation`
- `implementation sequencing`
- `cross-slice validation`
- `milestone review`

Do not turn `phase` into a rigid universal plan.

#### `next_step`
This should describe the next workstream-level coordination move or clearly point to the next child task to advance.

Good examples:
- `Create child task for intermediate schema definition and link it to milestone: contract formation.`
- `Pause at checkpoint and prepare workstream review packet comparing architecture paths.`
- `Activate evaluation child task after contract approval is recorded.`

#### `container`
For this template, `container` should remain `feature_cell`.

If the effort no longer needs workstream treatment, retire the workstream rather than changing the container value.

#### `overlays`
This field is legacy harness-local shorthand, not the canonical Layer C schema.

Use `overlays: []` when baseline control is implied at workstream scope.

If a non-baseline control regime must be shown in the current card shape, use the existing local values and interpret them as:
- `review_gatekeeper` -> reviewed-style `control_profile`
- `governance_escalation` -> change-controlled or high-assurance `control_profile`

Do not mirror task-scope control context automatically.

### Goal

This should state the larger outcome the coordinated effort is pursuing.

A good goal helps answer whether a child task belongs in the workstream at all.

### Scope Boundary

This is critical.

Use it to define:
- what belongs in the workstream,
- what does not,
- what completion means.

If this boundary becomes vague, the workstream is likely too broad.

### Promotion Reason

State why the work was promoted from task-only tracking.

Common reasons:
- multiple coherent child slices exist,
- staged delivery or sequencing matters,
- the effort spans multiple sessions or agents,
- workstream-level review or governance is needed,
- durable milestones or cross-slice decisions now matter.

### Current Structure

This section should make the workstream legible.

At a glance, another agent should be able to see:
- which child tasks are active,
- which are planned,
- which are done or obsolete.

Do not let old task links accumulate without maintenance.

### Milestones / Sequencing

Keep this lightweight but useful.

You do not need a full project plan. You do need enough structure to answer:
- what stage the effort is in,
- what comes next,
- what decisions or dependencies gate the next stage.

Good milestone examples:
- `discovery complete`
- `contract approved`
- `implementation slice 1 complete`
- `cross-slice validation complete`
- `rollout approval pending`

### Shared References

Use this for artifacts that matter at workstream scope.

Typical items:
- architecture RFC,
- parent issue,
- workstream review packet,
- approval packet,
- readiness evidence bundle,
- linked decision records,
- milestone-specific notes.

### Layer C

At workstream scope, `feature_cell` is already the container.

Add non-baseline control context only when it affects the effort as a whole.

Good rationale examples:
- `reviewed-style control applies because milestone 2 requires architecture review before any new child implementation tasks proceed`
- `change-controlled control applies because migration rollout requires signoff at workstream scope`
- `no workstream-scope non-baseline control profile; control boundaries remain local to child tasks`

### Layer D

This is the control surface for the workstream itself.

Use it to answer:
- can the larger effort continue,
- is it paused for milestone review,
- is approval pending,
- is it blocked at effort scope,
- is cross-slice validation now dominant,
- is the effort complete.

Important:
- do not derive this mechanically from child task states,
- a blocked child task does not always mean a blocked workstream,
- a completed workstream requires closure at effort scope, not just many closed child tasks.

Companion field guidance:
- fill `blocking_reason` and preferably `unblock_condition` when `state = blocked`
- fill `checkpoint_reason` when `state = checkpoint`
- fill `approval_ref` when approval exists or is pending through a linked artifact
- fill `evidence_refs` when readiness, validation, or completion depends on cross-slice evidence
- fill `decision_ref` when a meaningful workstream decision changed the route or closed the effort

### Decisions / Risks / Notes

This section is for context that affects multiple child tasks.

Use it for:
- architecture direction,
- shared tradeoffs,
- effort-level risks,
- coordination notes,
- handoff notes for future agents.

Do not duplicate detailed child-task logs here.

### Workstream Log

Append short entries at meaningful coordination boundaries.

Good entries record:
- new child task created,
- milestone reached,
- milestone blocked,
- review requested,
- approval recorded,
- workstream scope narrowed or split,
- next coordination move.

### Closure

Record both the expected acceptance basis and final closure notes.

Examples of acceptance basis:
- all required child tasks closed with accepted outputs,
- cross-slice validation completed and accepted,
- workstream-level approval recorded,
- rollout or migration stage accepted,
- workstream superseded by replacement structure.

## Minimal examples

### Example 1: feature development workstream

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
```

### Example 2: migration workstream with governance

```md
---
id: W-2026-03-parser-migration
title: Hybrid parser migration
created_at: 2026-03-06
updated_at: 2026-03-06
owner: agent
state: awaiting_approval
phase: stage-2 migration gate
next_step: Wait for approval outcome; if approved, activate rollout-readiness child task.
container: feature_cell
overlays:
  - governance_escalation
---
```

## Maintenance rules

- Use a workstream card only when `feature_cell` is genuinely justified.
- Keep child task lists current.
- Do not let the workstream become a mega-task or a dumping ground.
- Keep milestones and next steps current enough to guide action.
- Do not derive workstream state mechanically from child task states.
- Record workstream-scope decisions, risks, and approvals at the workstream level.
- When the effort ends or is superseded, record closure context rather than silently abandoning the workstream.
