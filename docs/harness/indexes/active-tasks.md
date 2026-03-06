# Active Tasks Index

This file is the lightweight live index of current task-scope work in the harness.

It is not the authoritative source of truth for any individual task. Each task card in `docs/harness/active/tasks/` remains authoritative. This index exists to make the current active queue legible at a glance.

Use this file to answer questions such as:
- which task slices are currently active,
- what mode each task is currently in,
- what state each task is currently in,
- what should move next,
- which items are blocked, paused, or close to review.

## Usage notes

- Keep this index short and readable.
- Update it when active task membership or status meaningfully changes.
- Do not duplicate full task-card detail here.
- Link or reference the authoritative task card for each item.
- Remove or archive entries when tasks are no longer active.

## Suggested update rule

Refresh this index when any of the following occur:
- a new active task is created,
- an active task changes current mode,
- an active task changes Layer D state,
- an active task moves to checkpoint, blocked, complete, or cancelled,
- a task is promoted into or detached from a workstream,
- the ordering of what should move next changes materially.

## Current task queue

| Task ID | Title | Mode | State | Workstream | Next step | Notes |
|---|---|---|---|---|---|---|
| `T-2026-03-06-001` | Investigate parser regression in block normalization | `debug_investigator` | `active` |  | Isolate the first normalization stage where nested list structure is lost. | Local debugging slice; no Layer C overlays active. |
| `T-2026-03-06-002` | Define intermediate schema acceptance contract | `contract_builder` | `checkpoint` | `W-2026-03-segmentation` | Review the linked contract packet and decide whether the phase-1 schema can be locked with targeted clarifications. | Paused at real review boundary; implementation should not continue yet. |
| `T-2026-03-06-003` | Outline segmentation logic boundaries for phase 1 | `contract_builder` | `active` | `W-2026-03-segmentation` | Draft the boundary notes describing what segmentation logic belongs in phase 1 versus later phases. | Active child task under segmentation workstream. |
| `T-2026-03-06-004` | Draft evaluation harness outline for segmentation acceptance | `quality_evaluator` | `draft` | `W-2026-03-segmentation` | Finish shaping the task into an actionable evaluation-planning slice with explicit acceptance scenarios. | Still in draft; not yet ready for full execution. |

## Suggested ordering

Use this section to express lightweight priority or execution ordering without turning the index into a project plan.

1. `T-2026-03-06-001` — active local debugging slice with immediate bounded next step.
2. `T-2026-03-06-002` — waiting on review outcome before downstream implementation-aligned work should proceed.
3. `T-2026-03-06-003` — may continue in parallel while the contract review remains local to schema acceptance.
4. `T-2026-03-06-004` — keep in draft until the evaluation-planning slice is shaped more precisely.

## State summary

### Active

- `T-2026-03-06-001`
- `T-2026-03-06-003`

### Draft

- `T-2026-03-06-004`

### Checkpoint

- `T-2026-03-06-002`

### Blocked

- none currently listed

### Awaiting approval

- none currently listed

## Workstream-linked active tasks

### `W-2026-03-segmentation`

- `T-2026-03-06-002` — contract review boundary
- `T-2026-03-06-003` — segmentation-logic boundary notes
- `T-2026-03-06-004` — evaluation-planning draft slice

## Attention flags

Use this section for lightweight operational reminders.

- `T-2026-03-06-002` should not return to implementation-aligned execution until the review outcome is recorded.
- `T-2026-03-06-001` should stay narrowly scoped to regression isolation and not drift into broad parser cleanup.
- `T-2026-03-06-004` should be tightened before moving from `draft` to `active`.

## Maintenance guidance

This index is healthy when:
- it is short enough to scan quickly,
- each entry clearly points to a real current task slice,
- mode and state match the authoritative task cards,
- the `next_step` field is concrete enough to support triage,
- and stale tasks are removed promptly.

This index is unhealthy when:
- it becomes more detailed than the actual task cards,
- task mode/state here diverges from authoritative artifacts,
- completed or cancelled tasks linger as if active,
- or it starts functioning as a second source of truth.
