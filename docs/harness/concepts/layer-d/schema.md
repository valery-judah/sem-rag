# Schema

## Purpose

This document defines the **canonical Layer D schema** for lifecycle control records.

Layer D records the **current execution-control status** of a tracked item. This file specifies:

- the canonical field shape,
- required and recommended fields,
- companion and adjacent fields,
- schema invariants,
- and boundary rules for what Layer D must not own.

Use:

- `states.md` for the meaning of each universal state,
- `scope-and-transitions.md` for task/workstream scope logic and transition patterns,
- this file for the normative data contract.

## Canonical Layer D record shape

A Layer D record is composed of:

- one canonical `layer_d` block,
- one standard `layer_d_companion` block,
- and, optionally, one adjacent block for repository-local convenience fields.

Canonical conceptual shape:

```yaml
layer_d:
  state: draft | active | blocked | checkpoint | awaiting_approval | validating | complete | cancelled
  phase: <workflow-local phase or null>
  next_step: <explicit next action or null>
  entered_at: <timestamp or null>
  updated_at: <timestamp or null>

layer_d_companion:
  blocking_reason: <string or null>
  unblock_condition: <string or null>
  checkpoint_reason: <string or null>
  approval_ref: <artifact or decision ref or null>
  evidence_refs: []
  decision_ref: <string or null>
  lifecycle_scope: task | workstream

adjacent_control_fields:
  validation_mode: tests | eval | rollout | human_review | mixed | null
  intent: <optional local intent label>
  requires_hitl: <derived boolean or null>
```

The `adjacent_control_fields` block is optional. The canonical Layer D contract consists of `layer_d` plus `layer_d_companion`.

## Core schema

The core Layer D block is the irreducible lifecycle record.

```yaml
layer_d:
  state: draft | active | blocked | checkpoint | awaiting_approval | validating | complete | cancelled
  phase: <workflow-local phase or null>
  next_step: <explicit next action or null>
  entered_at: <timestamp or null>
  updated_at: <timestamp or null>
```

### Field intent

- `state` is the one authoritative lifecycle value.
- `phase` carries workflow-local progression detail.
- `next_step` keeps the record operationally actionable.
- `entered_at` records when the current state was entered.
- `updated_at` records last record mutation time.

## Companion fields

The companion block standardizes the most useful operationally adjacent fields.

```yaml
layer_d_companion:
  blocking_reason: <string or null>
  unblock_condition: <string or null>
  checkpoint_reason: <string or null>
  approval_ref: <artifact or decision ref or null>
  evidence_refs: []
  decision_ref: <string or null>
  lifecycle_scope: task | workstream
```

### Why these are companion fields

These fields help explain or support the current lifecycle state, but they are not the state itself.

Examples:

- `blocking_reason` explains `blocked`,
- `checkpoint_reason` explains `checkpoint`,
- `approval_ref` supports `awaiting_approval`,
- `evidence_refs` support `validating`, `checkpoint`, `awaiting_approval`, or `complete`,
- `lifecycle_scope` distinguishes task-scope from workstream-scope records.

## Optional adjacent fields

Some repositories may want small convenience fields near Layer D without treating them as canonical lifecycle semantics.

```yaml
adjacent_control_fields:
  validation_mode: tests | eval | rollout | human_review | mixed | null
  intent: <optional local intent label>
  requires_hitl: <derived boolean or null>
```

### Guidance

- `validation_mode` is a useful operational hint, but not part of irreducible Layer D.
- `intent` may be convenient locally, but must not replace Layer A or Layer B.
- `requires_hitl` is a derived convenience only. It must never be treated as the authoritative source of lifecycle or control truth.

## Field guidance

### `state`

**Required**

Must be one of:

- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

`state` is the canonical Layer D value.

### `phase`

**Recommended**

Use for workflow-local progression detail.

Examples:

- `contract_drafting`
- `reproduction_and_isolation`
- `cutover_gate`
- `benchmark_run`
- `release_observation`

Do not expand the universal state set when `phase` can carry the detail.

### `next_step`

**Strongly recommended**

For non-terminal items, `next_step` should usually be concrete and executable.

Good examples:

- `reproduce failure on saved fixture`
- `prepare approval packet for rollout`
- `collect benchmark results and compare against baseline`

Bad examples:

- `continue work`
- `make progress`
- `follow up`

`next_step` may be `null` for terminal states such as `complete` or `cancelled`.

### `entered_at`

**Recommended**

Useful for chronology and control clarity.

### `updated_at`

**Recommended**

Useful for maintenance, review rhythm, and stale-record detection.

### `blocking_reason`

**Conditionally required**

Required when `state = blocked`.

This should identify the actual blocking condition, not a vague summary.

### `unblock_condition`

**Recommended when blocked**

Useful when the condition for continuation can be expressed concretely.

### `checkpoint_reason`

**Recommended when `state = checkpoint`**

Describes what review, interpretation, or control boundary is active.

### `approval_ref`

**Recommended when `state = awaiting_approval`**

May initially be `null` before the request is actually submitted, but should usually be populated once the approval boundary is live.

### `evidence_refs`

**Recommended for evidence-bearing states**

Especially useful for:

- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`

### `decision_ref`

**Recommended when a state change is driven by an explicit decision**

Examples:

- approval granted,
- cancellation decision,
- closure decision,
- review disposition.

### `lifecycle_scope`

**Recommended whenever scope ambiguity is possible**

Allowed values:

- `task`
- `workstream`

Use explicitly when both task-scope and workstream-scope Layer D records may coexist.

### `validation_mode`

**Optional adjacent field**

Useful only as a convenience hint.

Allowed values:

- `tests`
- `eval`
- `rollout`
- `human_review`
- `mixed`
- `null`

### `requires_hitl`

**Optional adjacent derived field**

Use only as a derived convenience.

It must not replace:

- canonical `state`,
- Layer C control-profile context,
- or local policy logic.

## Schema invariants

The following invariants should hold regardless of storage format.

1. Every Layer D record has exactly one canonical `state`.
2. `state` must come from the universal eight-state set.
3. `blocked` requires `blocking_reason`.
4. Non-terminal states should normally have a concrete `next_step`.
5. `checkpoint` should usually have `checkpoint_reason`.
6. `awaiting_approval` should usually gain `approval_ref` once the approval request is actually live.
7. `lifecycle_scope` should be explicit when both task-scope and workstream-scope records may exist.
8. Layer D must not encode Layer B mode names as state.
9. Layer D must not encode Layer C preset names or control-profile identity as state.
10. Workstream state must not be inferred mechanically from child task states.
11. `phase` must not be used to smuggle in a second universal state system.
12. Adjacent convenience fields must not override canonical Layer D semantics.

## Boundary rules: what Layer D must not own

Layer D is not the right place to define:

- Layer A classification,
- Layer B operating mode,
- Layer C `feature_cell` identity,
- Layer C `control_profile` obligations,
- reviewer or approver rosters,
- approval-packet semantics,
- rollback requirements,
- evidence policy,
- traceability policy,
- workstream artifact expectations.

Those belong in other layers or local policy artifacts.

A useful shorthand:

- Layer C owns the regime,
- Layer D owns the current gate.

## Representation guidance

The schema is semantic first. Repositories may represent it in different physical forms.

Reasonable implementation forms include:

- YAML blocks,
- JSON records,
- Markdown frontmatter,
- Python dataclasses,
- Pydantic models,
- structured task/workstream card sections.

The representation may vary. The field semantics and invariants should not.

## Minimal examples

### Example 1: blocked task record

```yaml
layer_d:
  state: blocked
  phase: waiting_on_dependency
  next_step: resume implementation when upstream schema lands
  entered_at: 2026-03-07T14:00:00Z
  updated_at: 2026-03-07T14:15:00Z

layer_d_companion:
  blocking_reason: upstream schema change not yet merged
  unblock_condition: upstream schema PR merged to main
  checkpoint_reason: null
  approval_ref: null
  evidence_refs: []
  decision_ref: null
  lifecycle_scope: task
```

### Example 2: checkpoint record with evidence

```yaml
layer_d:
  state: checkpoint
  phase: architecture_review
  next_step: await review outcome and update contract accordingly
  entered_at: 2026-03-07T15:00:00Z
  updated_at: 2026-03-07T15:10:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: architecture interpretation required before continuation
  approval_ref: null
  evidence_refs:
    - docs/rfcs/segmentation-contract.md
    - reports/acceptance-evidence-v1.md
  decision_ref: null
  lifecycle_scope: task
```

### Example 3: awaiting approval record

```yaml
layer_d:
  state: awaiting_approval
  phase: release_gate
  next_step: obtain go/no-go approval for rollout packet
  entered_at: 2026-03-07T16:00:00Z
  updated_at: 2026-03-07T16:20:00Z

layer_d_companion:
  blocking_reason: null
  unblock_condition: approval granted by release authority
  checkpoint_reason: null
  approval_ref: approvals/release-gate-2026-03-07
  evidence_refs:
    - reports/release-readiness.md
    - docs/runbooks/rollback.md
  decision_ref: null
  lifecycle_scope: workstream
```

### Example 4: validating workstream record

```yaml
layer_d:
  state: validating
  phase: rollout_observation
  next_step: review rollout metrics and confirm acceptance thresholds
  entered_at: 2026-03-07T17:00:00Z
  updated_at: 2026-03-07T17:30:00Z

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

adjacent_control_fields:
  validation_mode: rollout
  intent: null
  requires_hitl: true
```

## Summary

Use `schema.md` as the normative Layer D contract file.

It should keep Layer D:

- compact,
- machine-legible,
- separate from Layer A, Layer B, and Layer C,
- explicit about required versus adjacent fields,
- and stable across storage formats.
