

# Task Card Template

Use this template for every non-trivial task slice in the harness.

A task card is the authoritative operational record for a single current slice of work. It should be small enough that one current Layer B mode makes sense and explicit enough that another agent can resume from it without replaying the whole history.

## Usage notes

- Create one file per task in `docs/harness/active/tasks/`.
- Use the task card as the primary source of truth for the slice.
- Update the card whenever the slice, mode, overlays, state, or next step changes materially.
- Keep detailed execution notes in the work log, but keep the top of the card clean enough to function as a control surface.
- If the task grows beyond one coherent slice, reslice it or promote the larger effort to a workstream rather than turning this card into a catch-all.

## Copyable template

```md
---
id: T-YYYY-MM-DD-XXX
title: <short title for the current slice>
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
owner: agent
workstream_id:
state: draft
phase:
next_step:
current_mode:
overlays: []
container:
---

# Summary

## Request / problem

<What is being asked or what problem this slice addresses.>

## Current slice boundary

<What this task covers now. Keep this narrow and explicit.>

## Out of scope for this slice

<What is intentionally excluded from this task.>

# Inputs / References

- <repo path, issue, PR, doc, note, or other relevant artifact>
- <...>

# Layer A Snapshot

- intent:
- problem_uncertainty:
- dependency_complexity:
- knowledge_locality:
- specification_maturity:
- validation_burden:
- blast_radius:
- execution_horizon:

## Notes on classification

<Record any uncertainty or short rationale if useful.>

# Layer B

- current_mode:
- reason:
- reroute_triggers:
  - <optional>
  - <optional>

# Layer C

- overlays:
  - <optional: review_gatekeeper>
  - <optional: governance_escalation>
- container:
  <optional: feature_cell>

## Layer C rationale

<Why an overlay or container does or does not apply.>

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
- lifecycle_scope: task

## Current control condition

<Describe the current control status in plain language if useful.>

# Work Log

## YYYY-MM-DD

- <What was done>
- <What was observed>
- <What changed>
- <What should happen next>

# Open Questions / Risks

- <open question>
- <risk or trap>

# Closure

## Acceptance basis

<How this slice will be considered complete: tests, eval, explicit review, approval, implementation done, etc.>

## Closure notes

<Record final completion or cancellation context when the task ends.>
```

## Field guidance

### Frontmatter fields

#### `id`
Use a stable unique task identifier.

Recommended pattern:
- `T-YYYY-MM-DD-XXX`

Example:
- `T-2026-03-06-001`

#### `title`
The title should describe the current slice, not the whole initiative.

Good:
- `Investigate parser regression in block normalization`
- `Draft RFC structure for hierarchical segmentation`
- `Define intermediate schema acceptance contract`

Bad:
- `Improve parser`
- `Fix RAG`
- `Build segmentation feature`

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

#### `phase`
Use a short freeform description of the current local phase if helpful.

Examples:
- `reproduction`
- `contract drafting`
- `implementation`
- `evaluation pass`
- `review packet preparation`

Do not turn `phase` into a second state machine.

#### `next_step`
This is mandatory for every non-terminal task.

A good `next_step` is:
- concrete,
- local to the current slice,
- executable by another agent,
- consistent with the current mode and state.

#### `current_mode`
Use exactly one current Layer B operating mode.

Expected values:
- `research_scout`
- `contract_builder`
- `routine_implementer`
- `refactor_surgeon`
- `debug_investigator`
- `migration_operator`
- `optimization_tuner`
- `quality_evaluator`

#### `overlays`
Use only when Layer C overlays actually apply.

Typical values:
- `review_gatekeeper`
- `governance_escalation`

Leave empty when no overlay is needed.

#### `container`
Use `feature_cell` only when this task belongs to a workstream that genuinely requires long-running multi-slice coordination.

### Summary section

This section should tell another agent:
- what the task is,
- what the current slice is,
- what is intentionally out of scope.

If this section becomes vague, the task likely needs reslicing.

### Inputs / References

Include only the references that materially help execution or review.

Typical items:
- repo files,
- issues,
- PRs,
- docs,
- RFCs,
- benchmark outputs,
- review packets,
- evidence bundles,
- related task/workstream links.

### Layer A Snapshot

Fill at least the required Layer A core fields.

Use this section to capture the current problem shape, not long-term identity.

Update it only when the shape materially changes.

### Layer B

This section explains why the task is currently being approached in one specific mode.

`reason` should explain why this mode is dominant now.

`reroute_triggers` should capture the conditions that would justify changing posture.

Examples:
- `If root cause is identified and implementation path becomes clear, reroute to routine_implementer.`
- `If issue is actually undefined contract behavior, reroute to contract_builder.`

### Layer C

This section should stay sparse.

Use it only when overlays or the `feature_cell` container materially change how the task is governed or organized.

Good rationale examples:
- `review_gatekeeper applied because RFC must be reviewed before implementation begins`
- `governance_escalation applied because migration step has production rollback risk`
- `no overlays; current slice can proceed under baseline control`

### Layer D

This is the control surface for the task.

Use it to answer:
- can work continue,
- is the task blocked,
- is it paused for review,
- is approval pending,
- is validation now dominant,
- is the slice done.

Companion field guidance:
- fill `blocking_reason` and preferably `unblock_condition` when `state = blocked`
- fill `checkpoint_reason` when `state = checkpoint`
- fill `approval_ref` when approval exists or is pending through a linked artifact
- fill `evidence_refs` when validation, checkpoint, or completion depends on evidence
- fill `decision_ref` when a meaningful decision changed the route or closed the task

### Work Log

Append short entries at meaningful boundaries.

A good work log entry records:
- action taken,
- observation,
- effect on understanding or routing,
- resulting next move.

Do not let the work log replace the summary, mode, state, or next-step fields at the top of the card.

### Open Questions / Risks

Use this section for the few unresolved issues or traps that matter operationally.

Examples:
- missing acceptance criteria,
- likely hidden dependency,
- risk of crossing a review boundary accidentally,
- known fragile assumption.

### Closure

Record both the expected acceptance basis and final closure notes.

Examples of acceptance basis:
- regression reproduced and fixed with passing test,
- RFC section reviewed and accepted,
- evaluation evidence produced and accepted,
- migration readiness approved,
- task superseded and cancelled with replacement reference.

## Minimal examples

### Example 1: debugging slice

```md
---
id: T-2026-03-06-001
title: Investigate parser regression in block normalization
created_at: 2026-03-06
updated_at: 2026-03-06
owner: agent
workstream_id:
state: active
phase: reproduction
next_step: Isolate the first normalization stage where nested list structure is lost.
current_mode: debug_investigator
overlays: []
container:
---
```

### Example 2: contract drafting slice with review boundary

```md
---
id: T-2026-03-06-002
title: Define intermediate schema acceptance contract
created_at: 2026-03-06
updated_at: 2026-03-06
owner: agent
workstream_id: W-2026-03-segmentation
state: checkpoint
phase: contract draft ready for review
next_step: Review the linked contract packet and decide whether stage-1 schema can be locked.
current_mode: contract_builder
overlays:
  - review_gatekeeper
container: feature_cell
---
```

## Maintenance rules

- Every non-terminal task must have a concrete `next_step`.
- Every task must have exactly one current mode.
- Do not keep stale overlays, stale blockers, or stale checkpoint reasons.
- If the title or summary no longer describes the current slice, reslice the task.
- If the work clearly spans multiple slices over time, link it to a workstream or promote the larger effort.
- When a task ends, record closure context rather than silently abandoning it.