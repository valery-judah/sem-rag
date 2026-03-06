

# Handoff Note Template

Use this template whenever work is being intentionally paused, transferred, or resumed across agents, sessions, or context windows.

A handoff note is a resumability aid. It is not the authoritative source of truth. The task card or workstream card remains authoritative and must be updated before this note is written.

## Usage notes

- Create or update a handoff note when an agent stops before the item is complete.
- Always update the authoritative task or workstream card first.
- Keep the note concise enough to read quickly.
- Include only the context needed to resume safely.
- Preserve the exact current control condition.
- On resume, read the authoritative card first and the handoff note second.

## Copyable template

```md
---
id: H-YYYY-MM-DD-XXX
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
item_type: task | workstream
item_id:
handoff_reason:
current_state:
current_mode:
---

# Item Under Handoff

- item_type:
- item_id:
- title:

# Handoff Reason

<Why this handoff exists: end of session, transfer to reviewer, context pressure, waiting on approval, etc.>

# Current Status

## Plain-language control condition

<Describe the current control boundary clearly and directly.>

Examples:
- `Task is active and ready to continue from the recorded next step.`
- `Task is blocked on missing input fixture; do not continue until the file is available.`
- `Task is at checkpoint; review packet exists and implementation should not continue until the review outcome is recorded.`
- `Workstream is awaiting approval for the next migration stage.`

## Current mode / posture

- current_mode:
- why_this_mode:

## Current next step

<One concrete next action, consistent with the current state and mode.>

# Recent Progress Summary

## What changed in the latest cycle

- <what was done>
- <what was learned>
- <what boundary was reached>

## What remains

- <remaining work>
- <remaining uncertainty>

# Minimum Required Linked Artifacts

- authoritative_card: <task/workstream card path>
- <review packet, decision record, evidence bundle, PR, RFC section, benchmark output, etc.>
- <...>

# Open Risks / Traps

- <risk the next agent should not miss>
- <known fragile assumption>
- <boundary that must not be crossed accidentally>

# Resume Instructions

## If ready to continue

<What the next agent should do first.>

## If not ready to continue

<What must happen before normal execution can resume.>

Examples:
- `Wait for approval outcome before creating the next child task.`
- `Remain in checkpoint/review mode until the review result is recorded.`
- `Verify unblock_condition before resuming active work.`

# Validation Before Resume

Use this quick check before continuing:

- Confirm the authoritative card is still current.
- Confirm no decision, review, approval, or evidence outcome has changed since this note was written.
- Confirm the recorded `next_step` is still valid.
- Confirm the current state still permits the intended work.

# Resume Notes

<Optional section for the next agent to append a short note when resuming or superseding this handoff.>
```

## Field guidance

### Frontmatter fields

#### `id`
Use a stable unique handoff note identifier.

Recommended pattern:
- `H-YYYY-MM-DD-XXX`

Example:
- `H-2026-03-06-001`

#### `item_type`
Use one of:
- `task`
- `workstream`

#### `item_id`
Reference the authoritative task or workstream id.

Examples:
- `T-2026-03-06-001`
- `W-2026-03-segmentation`

#### `handoff_reason`
Describe why the handoff note was created.

Good examples:
- `session ending`
- `checkpoint handoff to reviewer`
- `awaiting approval boundary`
- `context window pressure`
- `transfer to implementation agent`

#### `current_state`
Mirror the current Layer D state from the authoritative card.

Expected values:
- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

#### `current_mode`
Mirror the current Layer B mode when the item is a task.

For workstreams, use the most relevant current posture only if helpful; the workstream card remains primary.

### Item Under Handoff

This section should make it immediately clear what artifact the next agent must open.

Always include:
- item type,
- item id,
- item title.

### Handoff Reason

Be explicit about why the note exists.

This helps the next agent distinguish among:
- routine end-of-session pause,
- review handoff,
- blocked waiting state,
- approval wait,
- implementation transfer,
- coordination transfer.

### Current Status

This is the most important section.

The plain-language control condition should preserve the exact operational boundary.

Do not blur:
- `active` with `blocked`,
- `checkpoint` with `active`,
- `awaiting_approval` with `checkpoint`,
- `validating` with `routine implementation`.

### Current next step

This should expose one concrete next action.

A good next step is:
- specific,
- executable,
- consistent with the current state,
- aligned with the current mode.

Weak examples:
- `continue`
- `pick this up later`
- `finish task`

Strong examples:
- `Write the failing regression test against the isolated nested-list reproduction input referenced in the task card.`
- `Review the linked contract packet and decide whether the stage-1 schema is sufficient to lock.`
- `Wait for approval result; if approved, activate the rollout-readiness child task.`

### Recent Progress Summary

Keep this compact.

The goal is to capture only the most recent meaningful progress so the next agent does not need to reread the whole work log to understand the current handoff.

A good summary answers:
- what changed,
- what was learned,
- what boundary was reached,
- what still remains.

### Minimum Required Linked Artifacts

This section should point to the smallest set of documents or outputs needed for safe resumption.

Typical items:
- authoritative task/workstream card,
- review packet,
- approval packet,
- decision record,
- evidence bundle,
- PR or diff summary,
- RFC section,
- benchmark or test output.

Do not overload this section with every related link.

### Open Risks / Traps

Capture the one or two things most likely to cause incorrect resumption.

Examples:
- hidden dependency not yet validated,
- fragile assumption about schema stability,
- review boundary that should not be crossed,
- blocker that is easy to forget,
- stale benchmark output that should not be reused.

### Resume Instructions

This section is especially useful when the next agent should *not* simply continue execution.

Use it to say what must happen first in cases like:
- blocked state,
- checkpoint,
- approval wait,
- validation-only continuation.

### Validation Before Resume

Keep this short and procedural.

The next agent should verify:
- current state,
- current next step,
- changed decisions,
- changed approvals,
- changed evidence.

### Resume Notes

Use this optionally when the next agent wants to record a short statement such as:
- resumed successfully,
- handoff was stale and replaced,
- approval arrived after note creation,
- blocker cleared,
- work resliced before continuation.

## Minimal examples

### Example 1: active debugging handoff

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
```

### Example 2: checkpoint handoff to reviewer

```md
---
id: H-2026-03-06-002
created_at: 2026-03-06
updated_at: 2026-03-06
item_type: task
item_id: T-2026-03-06-002
handoff_reason: checkpoint handoff to reviewer
current_state: checkpoint
current_mode: contract_builder
---
```

### Example 3: workstream awaiting approval

```md
---
id: H-2026-03-06-003
created_at: 2026-03-06
updated_at: 2026-03-06
item_type: workstream
item_id: W-2026-03-parser-migration
handoff_reason: awaiting approval boundary
current_state: awaiting_approval
current_mode:
---
```

## Maintenance rules

- Never let the handoff note become more accurate than the authoritative card.
- Preserve the current Layer D boundary exactly.
- Keep the note short enough to scan quickly.
- Point to the minimum required artifacts for safe resumption.
- Always include one concrete next step or one explicit wait condition.
- On resume, verify that the note is still current before acting on it.