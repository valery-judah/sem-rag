---
id: W-YYYY-MM-<slug>
title: <short workstream title>
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
owner: <agent-or-human>
---

# Workstream Card

## Purpose

Use this card only when a **Layer C `feature_cell`** is justified.

This card coordinates a longer-running workstream across multiple task slices. It is not a mega-task and it should not absorb detailed execution that belongs in child task cards.

Use a workstream card when one or more are true:

- `execution_horizon = multi_pr` or longer,
- `handoff_need = high`,
- multiple meaningful child slices must be coordinated,
- milestones or sequencing materially matter,
- multiple Layer B mode transitions are expected over time,
- or workstream-scope review / approval control is needed.

Do not create a workstream card merely because:

- the work feels important,
- there are many notes,
- the task might grow later,
- or someone wants to keep options open.

## Goal

State the workstream outcome being pursued.

- What is the intended result?
- What is the bounded outcome for this workstream?
- What would count as meaningful completion?

## Scope Boundary

Describe what this workstream includes and excludes.

Include:

- the kinds of child slices that belong here,
- the main boundaries of coordination,
- and what should still become a separate workstream or separate task.

## Promotion Reason

Explain why a workstream wrapper is justified now.

Typical reasons:

- staged multi-slice execution,
- cross-slice dependency,
- high resumability / handoff pressure,
- rollout-sensitive coordination,
- workstream-level checkpoint or approval points,
- milestone tracking materially improves control.

## Current Structure

List the child tasks or expected child slices.

- active child tasks:
  - `docs/harness/active/tasks/<task-file>.md`
- upcoming child tasks:
  - `docs/harness/active/tasks/<task-file>.md`
- completed child tasks:
  - `docs/harness/active/tasks/<task-file>.md`

Use links or stable refs where possible.

## Milestones / Sequencing

Keep this sparse.

Use only the milestones that materially improve coordination.

Example:

- contract frozen
- implementation slices merged
- readiness evidence assembled
- rollout approved
- rollout validated

## Shared References

Put cross-cutting references here.

Examples:

- RFCs
- design docs
- rollout plans
- dashboards
- evaluation reports
- migration runbooks
- decision logs

## Layer C

Use canonical Layer C structure here.

`control_profiles: []` means no non-baseline workstream-level control profile has been materialized.

```yaml
layer_c:
  feature_cell:
    scope: workstream
    slug: <stable-workstream-slug>
    title: <short workstream title>
    goal: <bounded workstream goal>
    reason: <why feature_cell is justified>
    entered_at: YYYY-MM-DD

    status_ref: null
    operating_package_ref: null

    slices_ref:
      - docs/harness/active/tasks/<task-file>.md

    milestones:
      - <milestone>

    decision_log_ref: null
    handoff_ref: null
    evidence_refs: []
    control_profile_refs: []
    notes: null

  control_profiles: []
```

### Guidance

- Keep `feature_cell` workstream-scoped.
- Materialize workstream-level `control_profile` records only when explicit obligations differ from baseline.
- Do not use legacy `container` / `overlays` shorthand.
- Do not encode Layer D state inside Layer C.

## Layer D

This is the **workstream-scope** lifecycle record.

Do not derive this mechanically from child task states.

A workstream may be:

- `active` while one child task is `blocked`,
- `checkpoint` while some child tasks are still `active`,
- `awaiting_approval` after child implementation tasks are complete,
- `validating` during rollout observation,
- `complete` only when the workstream scope is actually done.

```yaml
layer_d:
  state: draft | active | blocked | checkpoint | awaiting_approval | validating | complete | cancelled
  phase: <workflow-local phase or null>
  next_step: <explicit next coordination step or null>
  entered_at: YYYY-MM-DD
  updated_at: YYYY-MM-DD

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs: []
  decision_ref: null
  lifecycle_scope: workstream
```

### Guidance

- `next_step` should be a coordination step, not a child implementation step.
- `blocked` requires a real `blocking_reason`.
- `checkpoint` should usually have `checkpoint_reason`.
- `awaiting_approval` should usually gain `approval_ref` once the approval boundary is live.
- Use workstream-scope Layer D only when it adds operational clarity.

## Decisions / Risks / Notes

### Decisions

Record only decisions that materially affect coordination.

- YYYY-MM-DD — <decision summary> — ref: <decision ref>

### Risks / Constraints

Keep only active workstream-level risks or constraints.

- <risk or constraint>
- <required mitigation or dependency>

### Notes

Use sparingly. Prefer links, refs, and explicit fields over narrative bulk.

## Workstream Log

Record only meaningful workstream-level changes.

Examples:

- workstream created
- new child slice opened
- workstream control profile added
- major reroute across slices
- checkpoint packet prepared
- approval granted
- rollout observation started
- workstream closed

Format:

- YYYY-MM-DD — <event>

## Closure

Use this section only when the workstream is being closed or cancelled.

### Closure summary

- why the workstream is complete or cancelled,
- what evidence or decision refs support closure,
- what follow-up work, if any, remains outside this workstream.

### Closure refs

- evidence:
  - <ref>
- decisions:
  - <ref>

## Maintenance Rules

- Keep the workstream card focused on coordination, not detailed execution.
- Update it at meaningful boundaries, not continuously for show.
- Keep child task refs current.
- Keep milestone and decision lists sparse.
- Keep workstream-scope Layer D truthful.
- Keep Layer C explicit and canonical.
- Prefer linked task cards over bloating this file.

## Minimal Example

```md
---
id: W-2026-03-parser-block-schema-migration
title: Parser migration to structured block schema
created_at: 2026-03-07
updated_at: 2026-03-07
owner: agent
---

# Goal

Migrate parser outputs to the new block schema with validation and safe rollout support.

# Scope Boundary

Includes schema definition, parser model migration, validation, rollout readiness, and rollout observation.
Excludes unrelated parser cleanup not required for the migration.

# Promotion Reason

Staged multi-slice migration with rollout sensitivity, cross-slice dependency, and high handoff pressure.

# Current Structure

- active child tasks:
  - docs/harness/active/tasks/define-block-schema.md
  - docs/harness/active/tasks/refactor-parser-model.md
- upcoming child tasks:
  - docs/harness/active/tasks/run-validation.md
  - docs/harness/active/tasks/prepare-rollout.md
- completed child tasks:
  - none

# Milestones / Sequencing

- target schema finalized
- migration evidence assembled
- rollout approved
- rollout validated

# Shared References

- docs/rfcs/parser-schema-migration.md
- reports/parser-migration-validation.md
- docs/runbooks/parser-rollback.md

# Layer C

```yaml
layer_c:
  feature_cell:
    scope: workstream
    slug: parser-block-schema-migration
    title: Parser migration to structured block schema
    goal: migrate parser outputs to the new block schema with validation and safe rollout support
    reason: staged multi-slice migration with rollout sensitivity and high handoff pressure
    entered_at: 2026-03-07
    status_ref: null
    operating_package_ref: null
    slices_ref:
      - docs/harness/active/tasks/define-block-schema.md
      - docs/harness/active/tasks/refactor-parser-model.md
      - docs/harness/active/tasks/run-validation.md
      - docs/harness/active/tasks/prepare-rollout.md
    milestones:
      - target schema finalized
      - migration evidence assembled
      - rollout approved
      - rollout validated
    decision_log_ref: docs/harness/active/workstreams/parser-block-schema-migration-decision-log.md
    handoff_ref: null
    evidence_refs:
      - reports/parser-migration-validation.md
    control_profile_refs:
      - docs/harness/active/control-profiles/parser-migration-change-controlled.yaml
    notes: null

  control_profiles: []
```

# Layer D

```yaml
layer_d:
  state: active
  phase: coordinated_execution
  next_step: complete active child slices and prepare readiness packet for rollout gate
  entered_at: 2026-03-07
  updated_at: 2026-03-07

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs:
    - reports/parser-migration-validation.md
  decision_ref: null
  lifecycle_scope: workstream
```

# Decisions / Risks / Notes

## Decisions

- 2026-03-07 — migration will use staged rollout with rollback packet — ref: decisions/parser-migration-rollout-approach.md

## Risks / Constraints

- rollout must preserve downstream compatibility during cutover
- rollback plan must remain current before approval boundary

# Workstream Log

- 2026-03-07 — workstream created
```
