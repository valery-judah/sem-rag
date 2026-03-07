# Active Tasks Index

This file is the live derivative queue for executable task-scope work in the harness.

Status: live executable-task queue. Every entry in the default queue must correspond to a real authoritative task card in `docs/harness/active/tasks/`.

It is not the authoritative source of truth for any individual task. Each task card in `docs/harness/active/tasks/` remains authoritative. This index exists to make the executable task queue legible at a glance for fresh-agent discovery and everyday task selection.

Use this file to answer questions such as:
- which task slices are executable now,
- what mode each executable task is currently in,
- what state each executable task is currently in,
- what should move next,
- which non-executable items exist in clearly separated secondary sections.

## Usage notes

- Keep this index short and readable.
- Update it when active task membership or status meaningfully changes.
- Do not duplicate full task-card detail here.
- Link or reference the authoritative task card for each item.
- Remove or archive entries when tasks are no longer active.
- If this queue is stale, incomplete, or inconsistent with the task cards, authoritative task cards win and the queue must be repaired before relying on it.

## Suggested update rule

Refresh this index when any of the following occur:
- a new executable task is created,
- an executable task changes current mode,
- an executable task changes Layer D state,
- a task enters or leaves the executable queue,
- a task is promoted into or detached from a workstream,
- the ordering of what should move next changes materially.

## Default executable queue

| Task ID | Title | Mode | State | Workstream | Next step | Notes |
|---|---|---|---|---|---|---|
| `T-2026-03-07-001` | Define explicit parser contract for canonical output and degraded behavior | `contract_builder` | `active` |  | Draft the parser contract delta covering anchor completeness, metadata schema, supported content-type behavior, and degraded-output rules. | Bounded parser contract-definition slice; baseline Layer C only. |

## Suggested ordering

Use this section to express lightweight priority or execution ordering within the executable queue without turning the index into a project plan.

1. `T-2026-03-07-001` — active parser contract-definition slice that can proceed immediately and should clarify the next parser enforcement task.

## Secondary non-executable views

These sections remain derivative visibility aids. They do not belong to the default executable queue.

### Draft

- none currently listed

### Checkpoint

- none currently listed

### Blocked

- none currently listed

### Awaiting approval

- none currently listed

## Attention flags

Use this section for lightweight operational reminders.

- `T-2026-03-07-001` should keep the contract delta focused on the parser boundary rather than expanding into a full parser redesign.

## Maintenance guidance

Use `docs/harness-maintain/main.md` for harness-wide index policy.

This file should remain a short derivative summary of the authoritative task cards, not a second source of truth.
