# Operational Harness

This directory contains the common operational harness for running long-lived agentic work in a way that stays classifiable, routable, control-legible, resumable, reviewable, and maintainable across sessions.

The harness is intentionally smaller than a full project-management system. It does not try to encode every workflow detail, every organizational policy, or every possible delivery methodology. Its purpose is narrower: provide a stable operating surface for taking in work, shaping it into bounded slices, routing it into the correct current posture, maintaining control status, and preserving resumable context over time.

This README is the **entry document** for the harness. It should help a human or agent understand:

- what the harness is for,
- how the layered model is used operationally,
- which artifacts are authoritative,
- which workflow to open next,
- and which constraints keep the harness coherent.

Detailed semantics live elsewhere:

- conceptual definitions in `concepts/`,
- direct agent operating instructions in `AGENTS.md`,
- stepwise execution loops in `workflows/`,
- default rules in `policies/`,
- and concrete schemas, templates, examples, and registries in their respective directories.

## Purpose

The harness exists to make ordinary and long-running agentic work operable without turning the repository into a vague pile of notes or an over-engineered workflow system.

A good harness should make it easy to answer five operational questions at any time:

1. What is the current work slice?
2. How should the agent work on it now?
3. Does any non-baseline Layer C context materially apply?
4. What is the current lifecycle control status?
5. What is the next executable step?

Those five questions are the backbone of the layered model in practice.

## What this harness is

At a high level, this harness provides:

- a shared conceptual model in `concepts/`,
- direct execution guidance in `AGENTS.md`,
- reusable workflow loops in `workflows/`,
- templates for stable operational artifacts in `templates/`,
- default rules and routing discipline in `policies/`,
- examples for reference in `examples/`,
- indexes for live visibility in `indexes/`,
- schemas and registries for structured consistency,
- and prompt documents for guided agent use in `prompts/`.

The harness is organized around four layers:

- **Layer A** — classification snapshot of the current work slice
- **Layer B** — current atomic operating mode
- **Layer C** — coordination structures and control profiles
- **Layer D** — lifecycle control plane

This README does not re-specify all four layers in full. It explains how they fit together operationally and how to enter the harness correctly.

## What this harness is not

This harness is not:

- a giant workflow engine,
- a universal state machine for every kind of work,
- a replacement for engineering judgment,
- a requirement that every effort become a workstream,
- a substitute for local technical standards,
- or a heavy project-management stack.

If a task is small and bounded, the harness should remain small and bounded too.

## Core operating idea

The harness operates on **current bounded slices of work**, not on vague whole initiatives.

The default operating loop is:

1. intake the request,
2. define the current slice,
3. classify it with Layer A,
4. choose exactly one current Layer B mode,
5. apply Layer C only if it materially changes organization or control,
6. set Layer D status and a concrete `next_step`,
7. execute the current slice,
8. update the authoritative artifacts at meaningful boundaries,
9. reclassify, reroute, promote, hand off, validate, or close when the shape changes.

This is the central discipline of the harness.

## The five operating questions

The harness is healthiest when its artifacts make the following answers obvious.

### 1. What is the current work slice?

This is primarily a Layer A question. The slice should be narrow enough that one dominant current posture is meaningful.

### 2. How should the agent work on it now?

This is the Layer B question. The harness requires one current atomic operating mode rather than blended labels.

### 3. Does any non-baseline Layer C context materially apply?

This is the Layer C question. Use Layer C only when `feature_cell` or `control_profile` context materially improves control, coordination, or resumability.

### 4. What is the current lifecycle control status?

This is the Layer D question. The control plane should say whether the work can proceed, is blocked, is paused at checkpoint, is awaiting approval, is validating, or is terminal.

### 5. What is the next executable step?

This is the mandatory operational discipline attached to every non-terminal item. The `next_step` must be concrete enough that a human or agent can resume cleanly.

## Start here

When using the harness for real work, enter it in this order:

1. Read this `README.md`.
2. Read `AGENTS.md` for the direct operating rules given to the agent.
3. Open the relevant workflow based on the current situation:
   new or raw work -> `workflows/intake-loop.md`
   existing actionable task -> `workflows/task-execution-loop.md`
   coordinated multi-slice effort -> `workflows/workstream-loop.md`
   review or approval boundary -> `workflows/checkpoint-review-loop.md`
   pause, transfer, or resume -> `workflows/handoff-resume-loop.md`
4. Use the relevant template in `templates/` if a new artifact must be created.
5. Use `policies/routing-rules.md` if mode selection, repair, or rerouting is needed.
6. Consult the concepts only when deeper semantics are required.

## Minimum operational artifacts

The harness should work with a deliberately small artifact set.

### Task card

The task card is the default operational artifact.

Use `templates/task-card.template.md` for every non-trivial task slice.

A task card is the authoritative record for:

- the current slice,
- the Layer A snapshot,
- the current Layer B mode,
- any applicable Layer C context,
- the Layer D control status,
- the concrete `next_step`,
- relevant references,
- work log and closure context.

If you adopt only one artifact from the harness, adopt the task card.

### Workstream card

Use `templates/workstream-card.template.md` only when task-only tracking is no longer sufficient and the effort genuinely requires a workstream container such as `feature_cell`.

A workstream card coordinates:

- multiple related task slices,
- workstream-level scope and goals,
- sequencing or milestones,
- shared decisions and risks,
- and workstream-level control state.

### Handoff note

Use `templates/handoff-note.template.md` when work is intentionally paused or transferred.

A handoff note is a resumability aid. It is not the primary source of truth. The authoritative task or workstream card must remain more current than the handoff note.

### Review, approval, and evidence artifacts

Introduce review packets, approval packets, evidence bundles, and decision-log entries when control, validation, or governance clarity requires them.

Do not introduce them merely for ceremony.

## Default operating sequence for new work

For a new incoming request, the recommended path is:

1. capture the request and place it in the inbox if it is still raw,
2. run the intake loop when the request has not yet been normalized,
3. define the current bounded slice,
4. create a task card,
5. fill the Layer A core,
6. choose one current Layer B mode,
7. apply Layer C only if justified,
8. set Layer D status,
9. record a concrete `next_step`,
10. continue via the appropriate execution, review, or handoff workflow.

The default assumption is **task-first, workstream-later**.

## When to create a workstream

Do not create a workstream merely because the effort sounds important or may grow later.

Promote into a workstream only when one or more are true:

- the effort clearly spans multiple coherent slices,
- multiple Layer B mode transitions are expected over time,
- multiple linked tasks must be coordinated,
- resumability and handoff pressure are high,
- milestone tracking materially improves control,
- workstream-level decisions and risks need a stable home,
- or long-horizon visibility genuinely matters.

Until that threshold is crossed, keep the work as a task.

## Routing guidance

Routing discipline is a core harness constraint.

### Use one current atomic mode

Every active task slice should have exactly one current Layer B mode.

Do not use blended labels such as:

- `research + implementation`
- `debug/refactor`
- `planning/execution`

If more than one mode seems equally necessary, the slice is probably too broad and should be resliced.

### Use routing rules rather than improvised labels

Mode choice should be repaired through `policies/routing-rules.md`, not through local naming inventions.

### Reclassify when the work changes

The current mode is not a permanent identity. It may change as the work moves from investigation to execution, from execution to evaluation, or from remediation to migration.

## Control and state guidance

### Layer C stays sparse

Layer C should only be used when `feature_cell` or `control_profile` context materially changes control obligations or organizational structure.

Canonical Layer C constructs in this harness are:

- `feature_cell`
- `control_profile`

Use them because they improve control and coordination clarity, not because they sound architecturally complete.

### Layer D is authoritative control status

Layer D answers whether work is:

- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

Do not invent local state names. Do not overload state with routing meaning or governance detail. Keep workflow semantics in the workflow, local fields, linked artifacts, and the actual `next_step`.

## Directory map

### `AGENTS.md`

Direct execution contract for an agent working under the harness.

### `concepts/`

Durable conceptual specifications for Layers A through D and the operational playbook.

Layer D now lives under `concepts/layer-d/`: use `concepts/layer-d/README.md` as the overview and `states.md`, `schema.md`, `scope-and-transitions.md`, and `examples.md` as the deeper split references.

### `examples/`

Reference examples that show what filled artifacts should look like.

### `indexes/`

Live visibility views for active tasks, active workstreams, blocked items, and pending approvals.

### `policies/`

Default rules for routing, evidence, review, governance, and closure.

### `prompts/`

Prompt documents for common operational entry points such as intake, execution, resume, and review.

### `registries/`

Structured catalogs for modes, control profiles, states, and validation configurations.

### `schemas/`

Machine-readable schemas for core harness artifacts.

### `templates/`

Canonical markdown templates for the small set of operational artifacts.

### `workflows/`

Reusable stepwise loops for intake, execution, coordination, review, and handoff.

## Reading path for humans

If you are maintaining or evolving the harness itself, read in this order:

1. `README.md`
2. `concepts/operational-playbook.md`
3. the layer references in `concepts/`, using `concepts/layer-d/README.md` as the Layer D entrypoint
4. the workflow documents in `workflows/`
5. the templates in `templates/`
6. `policies/routing-rules.md`
7. relevant examples, schemas, registries, and maintenance docs as needed

## Reading path for agents

If you are entering to perform work rather than maintain the harness, read in this order:

1. `README.md`
2. `AGENTS.md`
3. the relevant workflow in `workflows/`
4. the relevant template in `templates/`
5. `policies/routing-rules.md` when routing or rerouting is needed
6. deeper concept docs only when the immediate task requires them

This keeps the active context small while preserving the authoritative routing and control model.

## Anti-patterns

The following patterns usually indicate harness drift or misuse.

### Process theater

Creating artifacts that do not improve control, resumability, or review clarity.

### Premature workstreams

Promoting work into a workstream before there is real coordination pressure.

### Stale authoritative artifacts

Allowing task cards or workstream cards to fall behind chat history or handoff notes.

### Blended modes

Using multiple current Layer B modes instead of reslicing the work.

### Custom local states

Inventing new Layer D labels instead of using the shared control plane.

### Layer mixing

Encoding routing semantics inside state, or using Layer C as a vague status bucket.

### Vague next steps

Leaving `next_step` values such as `continue`, `work on it`, or `finish later`.

### Forgotten closure

Completing or cancelling work without updating the authoritative artifact and closure context.

## Practical rule of thumb

The harness is operationally healthy when a fresh human or agent can open the current artifacts and answer, without guesswork:

- what the current slice is,
- how the agent should work on it now,
- whether any non-baseline Layer C context materially applies,
- what the current lifecycle control status is,
- and what the next concrete step is.

If those answers are obvious, the harness is doing its job.

## Current status and maintenance guidance

This harness is intentionally minimal. Maintain it with the following constraints:

- prefer sharper slicing over more categories,
- prefer explicit routing rules over improvised labels,
- prefer a small artifact set over documentation sprawl,
- keep Layer C sparse,
- keep Layer D truthful and shared,
- and update this README when the live harness structure or entry logic changes.

The README should remain an **entry-and-routing document**. It should not absorb the full playbook, replace the concepts, or duplicate detailed workflow instructions. When in doubt, keep it clear, minimal, and operational.
