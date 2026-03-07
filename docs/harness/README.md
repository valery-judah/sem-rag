# Operational Harness

This directory contains the minimal operational harness for running long-lived coding and design work with an agent under the Layer A–D model.

The harness is designed to make work:
- classifiable,
- routable,
- control-legible,
- resumable,
- reviewable,
- and maintainable across sessions.

It is intentionally smaller than a full project-management system. Its purpose is not to model every workflow detail. Its purpose is to give the agent and the human operator a stable operating surface for incoming tasks, active execution, workstream coordination, review boundaries, and handoffs.

## What this harness is

At a high level, this harness provides:
- a shared conceptual model in `concepts/`,
- operational loops in `workflows/`,
- reusable artifact templates in `templates/`,
- default policies in `policies/`,
- live operating state in `active/`,
- and prompt fragments in `prompts/`.

The harness is built around four layers:
- **Layer A** — classification snapshot of the current work slice
- **Layer B** — current atomic operating mode
- **Layer C** — workstream containers and control profiles
- **Layer D** — lifecycle control plane

Those concepts are defined in the `concepts/` directory. This README explains how to use them operationally.

## What this harness is not

This harness is not:
- a giant workflow engine,
- a universal state machine for all work,
- a replacement for judgment,
- a guarantee that every task needs a workstream,
- or a heavy project-management stack.

If a task is small and bounded, the harness should remain small and bounded too.

## Directory layout

```text
docs/harness/
  README.md
  AGENTS.md
  maintainining.md

  concepts/
    layer-a-taxonomy.md
    layer-b-operating-modes.md
    layer-c/
      README.md
      feature-cell.md
      control-profiles.md
      presets.md
      schema.md
      examples.md
    layer-d-lifecycle-control-plane.md
    operational-playbook.md

  workflows/
    intake-loop.md
    task-execution-loop.md
    workstream-loop.md
    checkpoint-review-loop.md
    handoff-resume-loop.md

  templates/
    task-card.template.md
    workstream-card.template.md
    handoff-note.template.md

  policies/
    routing-rules.md

  active/
    inbox/
    tasks/
    workstreams/
    archive/

  prompts/
    intake-agent.md
    execution-agent.md
    resume-agent.md
```

If the actual tree evolves, treat this layout as the intended operating structure.

## The core operating idea

The harness operates on **current slices of work**, not on vague whole initiatives.

The default flow is:
1. normalize incoming work into a task slice,
2. classify the current slice with Layer A,
3. choose exactly one current Layer B mode,
4. apply Layer C only when needed,
5. record Layer D status and concrete next step,
6. execute or pause according to the current boundary,
7. reslice, reroute, review, hand off, or close as needed.

This is the central discipline of the harness.

## Start here

When using this harness for real work, start in this order:

1. Read this `README.md`.
2. Read `AGENTS.md` for the direct operating instructions given to the coding agent.
3. If the work is new or raw, use `workflows/intake-loop.md`.
4. If a task card already exists and is actionable, use `workflows/task-execution-loop.md`.
5. If the effort has multiple coherent slices and requires `feature_cell`, use `workflows/workstream-loop.md`.
6. If work is paused for review, use `workflows/checkpoint-review-loop.md`.
7. If work is being paused or transferred, use `workflows/handoff-resume-loop.md`.

## Minimum operational artifacts

The harness is designed to work with a very small artifact set.

### 1. Task card

This is the default operational artifact.

Use `templates/task-card.template.md` for every non-trivial task slice.

A task card is the authoritative record for:
- the current slice,
- Layer A snapshot,
- current Layer B mode,
- current Layer C container and control-profile context,
- current Layer D status,
- current next step,
- work log and closure context.

If you only adopt one artifact from this harness, adopt the task card.

### 2. Workstream card

Use `templates/workstream-card.template.md` only when task-only tracking is no longer adequate and the effort has been promoted into a `feature_cell`.

A workstream card coordinates:
- multiple child task slices,
- milestones or sequencing,
- cross-slice decisions,
- shared risks,
- workstream-scope Layer C container/control context and Layer D state.

### 3. Handoff note

Use `templates/handoff-note.template.md` whenever work is intentionally paused or transferred.

A handoff note is not authoritative. It is a resumability aid layered on top of an up-to-date task or workstream card.

## Live operating directories

### `active/inbox/`

Use this for raw incoming work that has not yet been normalized.

Nothing should stay here for long. Inbox items should be converted into task cards.

### `active/tasks/`

This is the main live operating area.

Each file should represent one current task slice.

### `active/workstreams/`

Use this only for efforts that genuinely require `feature_cell` treatment.

### `active/archive/`

Move completed or cancelled artifacts here when they are no longer active.

## The workflow set

The harness defines five core workflow loops.

### Intake loop

`workflows/intake-loop.md`

Use this when work is new, raw, or needs to be reshaped into a proper task slice.

Primary result:
- a usable task card with Layer A core, one current mode, and a concrete next step.

### Task execution loop

`workflows/task-execution-loop.md`

Use this when a task card already exists and the current Layer D state permits bounded progress.

Primary result:
- forward progress on the current slice with updated mode, state, next step, and work log as needed.

### Workstream loop

`workflows/workstream-loop.md`

Use this when the effort spans multiple coherent slices and task-only tracking is no longer enough.

Primary result:
- a coordinated `feature_cell` effort with maintained child tasks, milestones, shared decisions, workstream-level control context, and workstream-level Layer D state.

### Checkpoint / review loop

`workflows/checkpoint-review-loop.md`

Use this when progress intentionally pauses at a review or approval boundary.

Primary result:
- a review packet or approval-ready summary, recorded outcome, and correct post-boundary state transition.

### Handoff / resume loop

`workflows/handoff-resume-loop.md`

Use this when work is paused, transferred, or resumed.

Primary result:
- preserved control boundary, concise resumability context, and a concrete next step for the next executor.

## The minimum operating discipline

To use this harness correctly, the agent should follow a few rules consistently.

### Always work on a slice

Do not operate on vague broad initiatives when a bounded slice can be defined.

### Always choose one current mode

Layer B is a current posture, not a blended label.

Do not write:
- `research + implementation`
- `debug/refactor`
- `planning/execution`

If more than one mode seems equally necessary, the slice is usually too broad.

### Keep Layer C sparse

Add `feature_cell` only when continuity across slices or sessions is materially needed.

Add `control_profile` only when explicit control obligations differ from baseline.

### Treat Layer D as authoritative control status

Layer D answers whether work can continue, is blocked, is paused for review, is awaiting approval, is validating, or is done.

Do not turn Layer D into a custom workflow taxonomy.

### Always leave a concrete next step

Every non-terminal active artifact should expose a concrete next move.

## Default operating sequence for new work

When a new task arrives:

1. Put the raw request in `active/inbox/` if needed.
2. Run the intake loop.
3. Create a task card in `active/tasks/`.
4. Fill the Layer A core.
5. Choose exactly one current Layer B mode using `policies/routing-rules.md`.
6. Apply Layer C only if justified.
7. Set Layer D state, phase, and concrete `next_step`.
8. Continue with the task execution loop or stop at a review/handoff boundary if appropriate.

## When to create a workstream

Create a workstream only when the effort clearly needs long-running multi-slice coordination.

Typical signs:
- Layer A suggests long-horizon execution, such as `execution_horizon = multi_pr` or longer,
- Layer A suggests high resumability pressure, such as `handoff_need = high`,
- multiple child tasks are needed,
- milestones or sequencing matter,
- the work will likely change modes over time,
- or workstream-scope control context is required.

If those conditions are not present, stay at task level.

## Routing guidance

Use `policies/routing-rules.md` to map a task slice to one current Layer B mode.

The routing policy is intentionally small and should remain so; control-profile and workstream decisions should stay in Layer C rather than leaking into routing labels.

When routing or rerouting, ask:
- what is the dominant kind of work required now,
- what does the current `next_step` actually demand,
- does one mode clearly dominate,
- or is the slice malformed and in need of reslicing.

## Recommended reading path for humans

If you are maintaining or extending the harness itself, read in this order:

1. `README.md`
2. `concepts/operational-playbook.md`
3. the layer references in `concepts/`
4. the five workflow documents in `workflows/`
5. the templates in `templates/`
6. `policies/routing-rules.md`
7. `maintainining.md`

## Recommended reading path for agents

If an agent is entering the harness fresh, the minimum useful sequence is:

1. `README.md`
2. `AGENTS.md`
3. the workflow file relevant to the current operation
4. the template relevant to the artifact being created or updated
5. `policies/routing-rules.md` when a mode must be chosen or repaired

## Anti-patterns

Avoid these failure modes:

### Treating the harness as a giant process layer

The harness should clarify and stabilize work, not bury it under ceremony.

### Creating workstreams too early

Do not promote broad-sounding work into `feature_cell` unless real coordination pressure exists.

### Letting the task card go stale

The task card is the primary operational record. If it is stale, the harness stops being trustworthy.

### Letting handoff notes replace authoritative cards

Handoff notes are secondary aids, not the source of truth.

### Using custom states or blended modes

Do not introduce local state taxonomies or blended Layer B labels when the problem is really poor slicing.

### Forgetting closure

Completed or cancelled work should be explicitly closed or archived rather than silently abandoned.

## Practical rule of thumb

If you are unsure what to do next, ask these questions in order:

1. What is the current slice?
2. What is the current control state?
3. What is the one current mode?
4. Is a review, approval, or workstream-control boundary actually present?
5. What is the concrete next step?

If you can answer those five questions from the artifacts in this directory, the harness is functioning.

## Current status of this harness

This harness is intentionally minimal.

It currently focuses on:
- markdown-based operational artifacts,
- explicit workflow loops,
- light policy and control guidance,
- human-readable and agent-readable task/workstream records.

It does not yet require:
- machine-enforced schemas,
- automatic linting,
- dashboard generation,
- or complex orchestration.

Those can be added later if the operating model proves stable.

## Harness maintenance

If you are changing the harness itself rather than operating within it, use `docs/harness/maintainining.md`.

That guide owns:
- harness-wide change policy,
- compatibility and migration status,
- cross-file synchronization rules,
- validation checks,
- and deferred automation guidance.

The harness is healthy when it remains easy to enter, easy to resume, and hard to misunderstand.
