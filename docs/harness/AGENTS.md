# Harness Agent Instructions

This file contains the direct operating instructions for any agent working inside this harness.

Read this file after `README.md` and before creating, updating, or relying on any live operational artifact.

## Purpose of this file

This file exists to translate the harness model into direct agent behavior.

When operating under this harness, your job is to:

- convert incoming work into a bounded current slice,
- choose the correct current operating posture,
- maintain truthful control status,
- keep work resumable across sessions,
- stop at real review, approval, and blocker boundaries,
- and preserve a small set of authoritative artifacts instead of letting context dissolve into chat history or loose notes.

This file is an execution contract. It tells you how to behave inside the harness.

## What this file does not do

This file does not:

- redefine the full layered architecture,
- replace the conceptual documents in `concepts/`,
- replace the workflow loops in `workflows/`,
- replace schemas, registries, or templates,
- authorize invention of new local ontology,
- or turn the harness into a second playbook.

Use this file for direct operating behavior. Use the deeper docs only when more detail is actually needed.

## Authority order and context loading

Treat the harness sources as authoritative in this order.

1. `README.md`
2. this `AGENTS.md`
3. the current authoritative task or workstream artifact for the live item
4. the relevant workflow in `workflows/`
5. the relevant template in `templates/`
6. `policies/routing-rules.md` when selecting, repairing, or changing the current mode
7. supporting packets, handoff notes, examples, and related references

When an authoritative task card or workstream card exists, read it first.

A handoff note is a resumability aid, not the primary source of truth.

Indexes, registries, schemas, and examples support operation, but they do not override the authoritative record for a specific live item.

## Startup discovery for fresh agents

If you are entering the harness without a preselected task, start from `indexes/active-tasks.md`.

Use that file as the discovery surface for executable task work, then open the selected authoritative task card in `active/tasks/` before entering execution or resume.

If you want a guided prompt surface for this startup-selection step, use `prompts/startup-task-selector.md` before entering execution or resume.

Treat the queue as derivative only:

- every queue entry should correspond to a real task card,
- authoritative task cards win on any mismatch,
- if the queue is stale, missing, or inconsistent, treat that as harness-maintenance debt and fall back to scanning authoritative task cards directly.

## Core operating invariants

### 1. Always work on a current bounded slice

Do not operate on a vague broad initiative when a narrower current slice can be defined.

If the work is too broad for one current operating mode to make sense, reslice it.

### 2. Always choose exactly one current Layer B mode

Every active task slice must have one current atomic operating mode.

Do not use blended labels such as:

- `research + implementation`
- `debug/refactor`
- `planning/execution`

When the dominant work changes, reroute the slice.

When no single mode clearly dominates, the slice is probably too broad and should be repaired before continuing.

### 3. Keep Layer C sparse

Use Layer C only when it materially changes organization or control.

In this harness, the canonical Layer C constructs are:

- `feature_cell`
- `control_profile`

Use `feature_cell` only when task-only tracking is no longer enough.

Use a non-baseline `control_profile` only when explicit control obligations differ from baseline.

Do not add Layer C context casually.

### 4. Treat Layer D as the authoritative control plane

Layer D says whether work can proceed.

Use only the canonical lifecycle control states defined by the harness.

Do not invent custom state names.
Do not encode routing semantics into state labels.
Do not continue execution through a real blocker, checkpoint, or approval boundary.

### 5. Every non-terminal item must expose a concrete `next_step`

`next_step` must be specific enough that another agent or a human can resume work without reconstructing intent from chat history.

Weak examples:

- `continue`
- `work on it`
- `finish task`

Strong examples:

- `Write the failing regression test for the nested-list rendering case.`
- `Draft the schema acceptance section with explicit required fields and invariants.`
- `Prepare the review packet comparing the three migration options.`

### 6. Keep authoritative artifacts current

Before pausing, handing off, rerouting, or closing work, update the authoritative task card or workstream card.

Do not let chat history, side notes, or handoff notes become more accurate than the authoritative artifact.

### 7. Prefer task-first operation

A task card is the default operational unit.

Do not create a workstream just because an effort sounds important or may become large later.

Promote into `feature_cell` only when coordination pressure, resumability pressure, or workstream-level control needs are real.

## Default agent loop

For ordinary harness operation, use this loop.

1. Read the authoritative artifact if one exists. If none exists, intake the raw request.
2. Define or verify the current bounded slice.
3. Verify that the Layer A core is present or repair it.
4. Verify exactly one current Layer B mode.
5. Verify whether any Layer C context materially applies.
6. Verify the current Layer D state and whether it permits the intended work.
7. Verify that `next_step` is concrete.
8. Perform the current slice of work through the appropriate workflow.
9. Update the authoritative artifact at the relevant boundary.
10. Reslice, reroute, promote, hand off, validate, or close when the work shape changes.

This loop is the default. Do not improvise a parallel operating system inside the harness.

## Workflow routing by current situation

Use the workflow files for stepwise execution.

### New or raw incoming work

Use:

- `workflows/intake-loop.md`

Expected outcome:

- a bounded current slice,
- a task card,
- an initial Layer A core,
- one current Layer B mode,
- truthful Layer D status,
- and a concrete `next_step`.

### Active task execution

Use:

- `workflows/task-execution-loop.md`

Use this when a task card has already been selected and the current Layer D state permits forward work.

### Multi-slice coordinated effort

Use:

- `workflows/workstream-loop.md`

Use this only when the effort has legitimately been promoted into a `feature_cell` workstream wrapper.

### Review or approval boundary

Use:

- `workflows/checkpoint-review-loop.md`

Use this when normal execution must stop because the work has reached a review, checkpoint, or signoff boundary.

### Pause, transfer, or resume

Use:

- `workflows/handoff-resume-loop.md`

Use this when work is intentionally paused, moved between sessions, or transferred between agents.

## Artifact authority and update rules

### Task card

The task card is the default authoritative artifact for a non-trivial task slice.

Use:

- `templates/task-card.template.md`

The task card should carry the operational truth for the item.

### Workstream card

The workstream card is authoritative for a real `feature_cell` workstream wrapper, not for an ordinary task.

Use:

- `templates/workstream-card.template.md`

A workstream card coordinates multiple related task slices. It should not become a mega-task.

### Handoff note

Use:

- `templates/handoff-note.template.md`

Write or update a handoff note only after the authoritative task or workstream artifact is current.

### Review, approval, evidence, and decision artifacts

Use the relevant templates when review, governance, validation, or traceability requires them:

- `templates/review-packet.template.md`
- `templates/approval-packet.template.md`
- `templates/evidence-bundle.template.md`
- `templates/decision-log-entry.template.md`

Introduce these artifacts when they materially improve control clarity. Do not create them for ceremony.

## Role of indexes, registries, schemas, examples, and prompts

### Indexes

Files in `indexes/` provide visibility across live work.

Use them to track and surface status, not as substitutes for authoritative cards.

For fresh task discovery, use `indexes/active-tasks.md` first. It should expose only executable default-queue items in its primary section.

### Registries

Files in `registries/` define canonical controlled vocabularies and related machine-readable catalog data.

Use them to avoid vocabulary drift.

### Schemas

Files in `schemas/` define structural validity.

Schema-valid is necessary but not sufficient. An artifact can be structurally valid and still be operationally stale, misleading, or incomplete.

### Examples

Files in `examples/` are reference material.

Use them to understand the intended artifact shape. Do not treat them as live operational truth.

### Prompts

Files in `prompts/` are guided entry surfaces for agent use.

They support correct operation, but they do not override the harness rules in `README.md`, `AGENTS.md`, workflows, policies, or live artifacts.

Use `prompts/startup-task-selector.md` when no task has yet been selected and the immediate need is to choose one executable task from the live queue before execution or resume.

## Boundary and gate behavior

### `blocked`

Stop forward execution.

Record the blocker concretely and leave a useful `next_step` that reflects the actual blocked condition.

Do not pretend blocked work is active.

### `checkpoint`

Stop normal execution and prepare the work for review or checkpoint evaluation.

Make the reason for the checkpoint explicit.

### `awaiting_approval`

Stop forward execution until the required approval or signoff condition is satisfied.

Do not silently continue through the gate.

### `validating`

Use this when evidence gathering, verification, or interpretation has become the dominant current activity.

Treat validation as real work with its own control status, not as a comment attached to unrelated execution.

### `complete` and `cancelled`

These are terminal states.

When work becomes terminal, close it cleanly and keep the artifact truthful.

## Reslice, reroute, and promote rules

### Reslice when the current unit of work is too broad

Reslice when:

- one current mode no longer makes sense,
- the `next_step` is vague because the slice is too large,
- the task has implicitly split into multiple meaningful subproblems,
- or the artifact is trying to represent multiple different kinds of work at once.

### Reroute when the dominant work changes

The current mode is not a permanent identity.

Reroute when the dominant work has changed, for example from:

- investigation to implementation,
- execution to evaluation,
- debugging to refactoring,
- or remediation to migration.

### Promote to workstream only when coordination pressure is real

Promote into `feature_cell` when one or more of the following are true:

- multiple child task slices exist,
- sequencing or milestones materially matter,
- resumability and handoff pressure are high,
- workstream-level decisions or risks need a stable home,
- or the effort clearly requires long-horizon coordination.

Do not treat long duration alone as sufficient reason to create a workstream.

## Minimum quality bars for live artifacts

### A usable task card must make these items clear

- the current slice,
- the relevant Layer A core,
- exactly one current Layer B mode,
- any applicable Layer C context,
- truthful Layer D state,
- one concrete `next_step`,
- relevant references,
- and current work log or closure context when applicable.

### A usable workstream card must make these items clear

- workstream title and goal,
- scope boundary,
- promotion reason,
- child task structure,
- current workstream Layer D status,
- workstream-level `next_step`,
- shared decisions, risks, and references,
- and current milestone or sequencing context when applicable.

### Operational truth matters more than decorative completeness

A shorter truthful artifact is better than a fuller but stale one.

Do not optimize for template filling. Optimize for operational clarity.

## What to do when uncertain

When uncertain, do not invent new local process.

Instead:

1. reread the authoritative artifact,
2. identify the current slice,
3. identify the current Layer D state,
4. identify the one dominant current mode,
5. check whether a real Layer C construct materially applies,
6. decide whether the work should proceed, pause, reroute, or reslice,
7. repair the artifact if the truth is unclear,
8. continue only through the correct workflow.

If the artifact and the real work disagree, repair the artifact before pretending the work is well-routed.

## Stop and handoff checklist

Before you stop work, hand it off, or end a session, ensure that:

- the authoritative task or workstream artifact is updated,
- Layer D reflects the true current control condition,
- `next_step` is concrete,
- any material decision, review, blocker, or evidence state is recorded,
- the smallest useful linked artifact set is exposed,
- and the handoff note, if one exists, is secondary to the authoritative artifact.

## Anti-patterns

Do not:

- use the harness as a vague note dump,
- create workstreams too early,
- let task cards or workstream cards go stale,
- allow handoff notes to become more accurate than the authoritative artifact,
- continue through real blocked, checkpoint, or approval boundaries,
- invent custom states or blended modes,
- encode multiple unrelated slices into one artifact,
- use schema validity as a substitute for operational truth,
- or leave terminal work unclosed.

## Practical shorthand

For any live item, the harness should make five answers obvious:

1. What is the current slice?
2. What is the current control state?
3. What is the one current mode?
4. Is there a real review, approval, or workstream-control boundary?
5. What is the concrete next step?

If those answers are clear, the harness is likely healthy.
If they are unclear, repair the artifact and routing before doing more work.
