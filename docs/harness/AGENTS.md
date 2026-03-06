

# Harness Agent Instructions

This file contains the direct operating instructions for any coding or design agent working inside `docs/harness/`.

Read this file after `docs/harness/README.md` and before creating or updating any live operational artifact.

## Primary role

When operating under this harness, your job is to:
- convert incoming work into a well-formed current slice,
- choose the correct current operating posture,
- maintain accurate control status,
- keep work resumable across sessions,
- stop at real review or approval boundaries,
- avoid turning the harness into a vague note pile.

You are not here to improvise a new workflow ontology. You are here to operate cleanly within the existing one.

## Authoritative files

Treat these files as authoritative in this order:

1. `docs/harness/README.md`
2. this `docs/harness/AGENTS.md`
3. the relevant workflow file in `docs/harness/workflows/`
4. the relevant template in `docs/harness/templates/`
5. `docs/harness/policies/routing-rules.md`
6. the relevant live artifact in `docs/harness/active/`

If a task or workstream card exists, it is the authoritative operational record for that item.

Handoff notes are resumability aids, not primary source of truth.

## Core operating rules

### 1. Always work on a current slice

Do not operate on a vague broad initiative if you can define a bounded current slice.

If the work is too broad for one current mode to make sense, reslice it.

### 2. Always choose exactly one current Layer B mode

Use only one current operating mode for a task slice.

Allowed modes:
- `research_scout`
- `contract_builder`
- `routine_implementer`
- `refactor_surgeon`
- `debug_investigator`
- `migration_operator`
- `optimization_tuner`
- `quality_evaluator`

Do not use blended labels such as:
- `research + implementation`
- `debug/refactor`
- `planning/execution`

Use `docs/harness/policies/routing-rules.md` when selecting or repairing the mode.

### 3. Keep Layer C sparse

Apply Layer C only when it materially changes control or organization.

Allowed Layer C constructs in this harness:
- overlays:
  - `review_gatekeeper`
  - `governance_escalation`
- container:
  - `feature_cell`

Do not add overlays or containers casually.

### 4. Treat Layer D as authoritative control status

Use Layer D to represent whether the item is:
- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

Do not invent custom state names.
Do not encode workflow semantics into state labels.
Do not continue execution through a real blocker, checkpoint, or approval boundary.

### 5. Always leave a concrete next step

Every non-terminal active artifact must expose one concrete `next_step`.

Weak examples:
- `continue`
- `work on it`
- `finish task`

Strong examples:
- `Write the failing regression test for the isolated nested-list reproduction case.`
- `Draft the schema acceptance section with explicit required fields and invariants.`
- `Prepare the review packet comparing the three migration options.`

### 6. Keep authoritative artifacts current

Before stopping, handing off, or switching modes, update the relevant task card or workstream card.

Do not let chat history or handoff notes become more accurate than the authoritative card.

## Required operating sequence for new work

When new work appears:

1. Read `docs/harness/README.md`.
2. If needed, place the raw item in `docs/harness/active/inbox/`.
3. Run `docs/harness/workflows/intake-loop.md`.
4. Create a task card in `docs/harness/active/tasks/` using `templates/task-card.template.md`.
5. Fill the required Layer A core.
6. Choose exactly one current Layer B mode.
7. Apply Layer C only if justified.
8. Set Layer D `state`, `phase`, and concrete `next_step`.
9. Continue with the appropriate next loop.

## Required behavior for active tasks

If a task card already exists:

1. Read the task card first.
2. Treat it as the current operational truth.
3. Verify that the Layer D state permits the intended work.
4. Continue through `workflows/task-execution-loop.md`.
5. Update the work log and control fields after meaningful progress.
6. Reroute or reslice if the current slice no longer matches the real work.

## Required behavior for workstreams

If the effort already has a `feature_cell` workstream:

1. Read the workstream card first.
2. Then read the relevant active child task cards.
3. Use `workflows/workstream-loop.md` for cross-slice coordination.
4. Keep child task lists, milestones, and workstream-level state current.
5. Do not turn the workstream card into a mega-task.

## Required behavior at review boundaries

If work reaches a real review boundary:

1. Stop normal forward execution.
2. Use `workflows/checkpoint-review-loop.md`.
3. Prepare or update the review packet.
4. Record `checkpoint_reason` and keep Layer D truthful.
5. Do not continue beyond the boundary until the review outcome is recorded.

If the result becomes a hard signoff gate, transition to `awaiting_approval`.

## Required behavior for handoff and resume

When stopping or transferring work:

1. Update the authoritative task or workstream card first.
2. Use `workflows/handoff-resume-loop.md`.
3. Write or update a handoff note only after the authoritative card is current.
4. Preserve the exact current control condition.
5. Expose the smallest useful set of linked artifacts and one concrete next step.

When resuming:

1. Read the authoritative card first.
2. Read the handoff note second.
3. Check whether any decision, approval, review, or evidence changed since the note was written.
4. Resume only if the current Layer D state permits the intended work.

## Artifact creation rules

### Task cards

Create one file per non-trivial task slice in:
- `docs/harness/active/tasks/`

Use:
- `docs/harness/templates/task-card.template.md`

A task card is mandatory for non-trivial work.

### Workstream cards

Create a workstream card only when task-only tracking is inadequate.

Typical reasons:
- multiple meaningful child slices exist,
- the effort spans multiple sessions,
- milestones or sequencing matter,
- workstream-level review or governance is needed.

Create in:
- `docs/harness/active/workstreams/`

Use:
- `docs/harness/templates/workstream-card.template.md`

### Handoff notes

Create or update handoff notes only when work is intentionally paused or transferred.

Use:
- `docs/harness/templates/handoff-note.template.md`

Remember: handoff notes are secondary to authoritative cards.

## Routing discipline

When choosing a mode, ask:
- what is the current slice,
- what is the dominant kind of work required now,
- what does the current `next_step` actually demand,
- whether exactly one mode dominates,
- whether the slice should be resliced instead of forcing a blended route.

Use the routing rules file rather than improvising local routing conventions.

## Control discipline

Before taking action, ask:
- what is the current Layer D state,
- does this state permit the work I am about to do,
- is this actually a blocker, checkpoint, approval gate, validation phase, or active step,
- what exact next step should remain after I act.

If the answer is unclear, repair the artifact before continuing.

## Minimum required fields for a usable task

A non-trivial active task is not usable unless it has at least:
- a meaningful `title`,
- a current slice summary,
- the Layer A core,
- exactly one `current_mode`,
- a truthful Layer D `state`,
- a concrete `next_step`,
- relevant references,
- and a current work log entry when meaningful progress has occurred.

## Minimum required fields for a usable workstream

A workstream is not usable unless it has at least:
- a workstream `title`,
- a clear goal,
- a scope boundary,
- a promotion reason,
- current child task structure,
- current workstream Layer D state,
- a workstream-level `next_step`,
- and current shared references or decisions when relevant.

## Anti-patterns

Avoid these behaviors.

### 1. Using the harness as a dumping ground

Do not accumulate vague notes, stale task cards, and outdated handoff summaries without maintaining the control fields.

### 2. Creating workstreams too early

Do not promote broad-sounding work into `feature_cell` unless the coordination need is real.

### 3. Letting cards go stale

A stale authoritative card breaks resumability and routing.

### 4. Continuing through a boundary

Do not continue implementation or migration through:
- `blocked`
- `checkpoint`
- `awaiting_approval`

unless the correct loop explicitly changes that condition.

### 5. Inventing local ontology

Do not add new state names, blended modes, or new universal layer constructs just because one slice is awkward.

Usually the correct action is to improve slicing, routing, or note quality.

### 6. Leaving terminal work unclosed

Do not leave completed or cancelled work indefinitely in active directories with no closure context.

## Preferred behavior when uncertain

If uncertain:
1. read the current authoritative artifact again,
2. identify the current slice,
3. identify the current control state,
4. identify the one current mode,
5. check whether a review/governance boundary is actually present,
6. repair the artifact if needed,
7. then continue through the correct workflow loop.

When no single mode fits, reslice.
When no action is permitted by current state, stop and record the true boundary.

## Minimal checklist before stopping

Before ending a session or yielding control, confirm:
- the authoritative task/workstream card is current,
- the Layer D state is truthful,
- the current mode is still correct,
- stale blockers/checkpoint reasons were removed or updated,
- the `next_step` is concrete,
- important refs are linked,
- and any handoff note matches the authoritative card.

## Practical shorthand

For any item in this harness, be able to answer:
1. What is the current slice or effort?
2. What is the current control state?
3. What is the one current mode?
4. Is there a real review or governance boundary?
5. What is the concrete next step?

If those five answers are clear in the artifacts, the harness is healthy.