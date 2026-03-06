

# Example Filled Handoff Note

This example shows what a filled handoff note can look like when a task is being paused and transferred to another agent.

It is intentionally concise. The goal is to show:
- how the handoff note summarizes the current operational truth without replacing the authoritative task card,
- how the current control condition is preserved in plain language,
- how the next agent is pointed to the minimum required artifacts,
- how the next step remains concrete and state-consistent.

```md
---
id: H-2026-03-06-001
created_at: 2026-03-06
updated_at: 2026-03-06
item_type: task
item_id: T-2026-03-06-001
handoff_reason: session ending
current_state: active
current_mode: debug_investigator
---

# Item Under Handoff

- item_type: task
- item_id: T-2026-03-06-001
- title: Investigate parser regression in block normalization

# Handoff Reason

The current session is ending before the regression has been causally isolated. The task is still active and should be resumed by the next agent from the current investigation boundary.

# Current Status

## Plain-language control condition

Task is active and ready to continue from the recorded next step. No review pause, blocker, or approval gate is currently active.

## Current mode / posture

- current_mode: debug_investigator
- why_this_mode: The dominant work is still reproduction and root-cause isolation. The task is not yet ready for a bounded implementation fix.

## Current next step

Isolate the first normalization stage where nested list structure is lost.

# Recent Progress Summary

## What changed in the latest cycle

- Reproduced the nested-list regression using the stored fixture.
- Confirmed that the structure is lost during normalization rather than upstream raw parsing.
- Narrowed the likely failure surface to the normalization path in `src/parsing/normalization.py`.

## What remains

- identify the first failing transformation stage,
- determine whether the failure is a local implementation bug or a hidden contract ambiguity,
- reroute to `routine_implementer` or `contract_builder` once the cause is clear.

# Minimum Required Linked Artifacts

- authoritative_card: `docs/harness/active/tasks/T-2026-03-06-001-parser-regression.md`
- relevant code path: `src/parsing/normalization.py`
- failing fixture: `tests/fixtures/nested_list_regression.md`
- related test file: `tests/parsing/test_block_normalization.py`

# Open Risks / Traps

- Risk: scope may drift into broad normalization cleanup before the first failing stage is isolated.
- Risk: older undocumented expectations about nested-list output may look like a regression when the real issue is contract ambiguity.
- Do not jump into implementation until the causal stage is confirmed.

# Resume Instructions

## If ready to continue

Start by reading the authoritative task card, then inspect the normalization path step by step against the failing fixture until the first structure-breaking transformation is identified.

## If not ready to continue

If new information shows the task is no longer `active`, do not continue normal debugging. Respect the updated state on the authoritative card and move into the correct loop.

# Validation Before Resume

Use this quick check before continuing:

- Confirm the authoritative card is still current.
- Confirm no review, approval, or decision outcome has changed since this note was written.
- Confirm the recorded `next_step` is still valid.
- Confirm the task is still `active` and not blocked or paused.

# Resume Notes

No resume note added yet.
```

## Why this example is shaped this way

A few things are deliberate here:

- The note points back to the authoritative task card instead of trying to replace it.
- The control condition is stated plainly so the next agent does not accidentally cross a boundary.
- The linked artifacts are minimal and directly useful for safe resumption.
- The next step is concrete enough that another agent can continue without replaying the full task history.

## What to notice

This example is a good reference when:
- a task remains `active` across sessions,
- the work has made meaningful progress but is not yet complete,
- the next agent should continue from a narrow existing boundary,
- the handoff should stay concise and operational rather than narrative-heavy.

## Possible variations

A handoff note like this would look different if:
- the task were `checkpoint`, in which case the note should point to the review packet and explicitly say not to continue implementation,
- the task were `blocked`, in which case the unblock condition should be stated clearly,
- the item were a workstream, in which case the note should point first to the workstream card and then to the relevant child tasks.