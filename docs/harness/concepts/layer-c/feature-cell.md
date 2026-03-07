# Feature Cell

This document defines **`feature_cell`** as the canonical Layer C workstream wrapper.

A `feature_cell` is a lightweight wrapper for **long-horizon, multi-slice work** that needs continuity, visibility, and resumability across time. It does not define the current operating mode, and it is not a lifecycle state.

Use this file when you need to answer questions such as:

- Should this work remain independent slices, or be wrapped as a workstream?
- When is a `feature_cell` justified?
- What lightweight workstream package usually goes with it?
- How does a `feature_cell` relate to slices, `control_profile` records, and Layer D tracking?

## Purpose

`feature_cell` exists to give long-running work a stable workstream wrapper without turning Layer C into a heavyweight PM framework.

It is meant for work that would otherwise become brittle because context or control history gets lost across:

- multiple slices,
- multiple pull requests,
- multiple sessions,
- multiple handoffs,
- or multiple checkpoints over time.

A good `feature_cell` improves:

- continuity,
- resumability,
- workstream visibility,
- decision traceability,
- and coordination around one shared goal.

## Boundary

Keep these distinctions strict.

### Not Layer A

Layer A explains the shape of the current slice.

`feature_cell` is a downstream structuring decision, often justified by Layer A signals such as:

- long execution horizon,
- high handoff burden,
- cross-slice dependency,
- non-trivial coordination cost,
- evolving constraints over time.

Layer A explains why the work is shaped this way. `feature_cell` records that the work is being wrapped as a persistent workstream.

### Not Layer B

Layer B defines the current operating mode.

`feature_cell` does not answer:

> How should the agent work now?

It answers:

> Should these slices be managed as one coherent workstream across time?

A `feature_cell` may contain slices that move through several Layer B modes over time.

### Not Layer D

Layer D defines the current lifecycle or control status of a slice or workstream.

`feature_cell` is not a state.

Examples:

- a feature cell may currently be `active`, `checkpoint`, or `blocked` at workstream scope,
- an individual slice inside the cell may separately be `ready`, `in_progress`, `validating`, or `done`,
- but `feature_cell` itself is only the wrapper.

Do not treat feature-cell membership as a status.

## When a feature cell is justified

Use a `feature_cell` when work is better managed as a coherent workstream than as unrelated slices.

Typical indicators:

### 1. Multi-slice execution

The work cannot be completed cleanly in one slice without losing meaningful structure.

Examples:

- specification -> implementation -> validation,
- staged migration,
- feature build with multiple dependent PRs,
- rollout with follow-up evaluation.

### 2. High handoff burden

The work is likely to pass across multiple sessions, agents, or humans, and context loss would be costly.

### 3. Shared goal with dependent sub-work

Several slices contribute to one user-visible or system-level outcome and should remain grouped.

### 4. Need for workstream-level visibility

You need a stable place to see:

- current goal,
- major milestones,
- open decisions,
- key risks,
- current linked controls,
- and current next steps.

### 5. Need for resumability

A later agent or human should be able to resume the workstream without reconstructing context from scattered artifacts.

### 6. Need for workstream-level control coordination

The work needs workstream-level HITL points, approvals, checkpoints, or decision tracking across slices.

## When a feature cell is not justified

Do **not** create a `feature_cell` just because work matters or may take more than a few minutes.

A `feature_cell` is usually unnecessary when:

- the work is a single local slice,
- the work has low handoff risk,
- the work does not need workstream-level visibility,
- the work has little cross-slice coupling,
- or the work can be finished and evaluated cleanly without a persistent wrapper.

Avoid feature-cell inflation.

## Core design rules

### 1. One coherent workstream, not a bag of tasks

A `feature_cell` should represent one coherent workstream with one meaningful shared goal.

Bad examples:

- random backlog work
- misc fixes
- things to do this week

Good examples:

- parser migration to structured block schema
- hierarchical segmentation phase 1
- eval domain centralization rollout

### 2. Keep the workstream wrapper lightweight

A `feature_cell` should carry the minimum structure needed for continuity and control.

Do not turn it into heavyweight PM machinery by default.

### 3. Slices remain the execution unit

The `feature_cell` is the wrapper.

Actual execution still happens through slices that carry their own:

- Layer A classification,
- Layer B operating mode,
- Layer C slice-level `control_profile` if needed,
- Layer D lifecycle record.

### 4. Workstream state and slice state remain separate

A `feature_cell` may have workstream-level Layer D tracking.

Each child slice may also have its own Layer D record.

Do not collapse these into one undifferentiated status line.

### 5. Control semantics stay outside the workstream wrapper

Use linked `control_profile` records when control obligations matter.

Do not absorb review, approval, evidence, or rollback semantics into the `feature_cell` itself.

## Canonical object shape

When shown on its own, a `feature_cell` object should match the value of `layer_c.feature_cell`:

```yaml
scope: workstream
slug: <string>
title: <string>
goal: <string>
reason: <string>
entered_at: YYYY-MM-DD

status_ref: <string | null>
operating_package_ref: <string | null>

slices_ref:
  - <string>

milestones:
  - <string>

decision_log_ref: <string | null>
handoff_ref: <string | null>
evidence_refs:
  - <string>

control_profile_refs:
  - <string>

notes: <string | null>
```

## Field semantics

### `scope`

Always `workstream`.

### `slug`

Stable machine-friendly identifier for the workstream.

### `title`

Short human-readable label for the workstream.

### `goal`

The workstream outcome being pursued.

### `reason`

Why workstream wrapping is justified.

Good examples:

- multi-PR feature with high handoff risk
- staged migration with rollout-sensitive transitions
- design -> implementation -> evaluation arc needs continuity

### `entered_at`

When the feature cell was created.

### `status_ref`

Optional reference to the workstream-level Layer D record.

### `operating_package_ref`

Reference to the primary workstream artifact bundle.

This may point to:

- a workstream card,
- a dedicated directory,
- a tracker file,
- or another workstream index artifact.

### `slices_ref`

References to slices or task cards associated with the workstream.

This does not mean all slices are simultaneously active. It only means they belong to the same wrapper.

### `milestones`

Optional workstream checkpoints or delivery landmarks.

Keep these sparse and decision-relevant.

### `decision_log_ref`

Reference to workstream-level decision history.

### `handoff_ref`

Reference to the current handoff or resumability note.

### `evidence_refs`

Links to major evidence artifacts relevant at workstream scope.

### `control_profile_refs`

References to linked Layer C `control_profile` records.

These refs let the workstream wrapper compose with the control regime without absorbing those semantics.

### `notes`

Optional freeform clarification.

Use sparingly.

## Relationship to slices

A `feature_cell` wraps slices. It does not replace them.

A slice inside a `feature_cell` should still carry its own:

- Layer A classification,
- Layer B mode,
- Layer D record,
- and slice-level Layer C `control_profile` if required.

The `feature_cell` provides continuity above those slices.

## Relationship to control profiles

`feature_cell` and `control_profile` solve different problems:

- `feature_cell`: should this work be wrapped as a persistent workstream?
- `control_profile`: what explicit control obligations apply?

They often appear together, but neither implies the other.

Examples:

- a `feature_cell` with no extra control burden,
- a single slice with a reviewed `control_profile` but no `feature_cell`,
- a `feature_cell` with a workstream-level change-controlled profile,
- a `feature_cell` where only one child slice has a reviewed profile.

## Relationship to Layer D tracking

A repository may track Layer D at two levels when `feature_cell` is used:

1. workstream level
2. slice level

This split is often useful.

For example:

- the feature cell may be `active` overall,
- one child slice may be `in_progress`,
- another may be `ready`,
- another may be `blocked`,
- and a rollout slice may temporarily enter `awaiting_approval`.

## Recommended creation criteria

A repository may use a lightweight threshold such as:

Create a `feature_cell` when at least two of the following are true:

- expected multi-slice work,
- likely multi-session or multi-handoff execution,
- non-trivial cross-slice dependency,
- explicit workstream-level HITL or approval points,
- need for a decision log or handoff continuity,
- need for stable workstream-level visibility.

This is guidance, not a universal law.

## Recommended workstream package

Repositories using `feature_cell` will usually want a lightweight operating package.

Typical components:

- workstream card,
- goal statement,
- task or slice list,
- milestone list,
- decision log,
- active risks or constraints,
- evidence links,
- handoff note,
- next-step pointer,
- linked `control_profile` refs.

These are typical defaults, not the semantic definition of the workstream wrapper.

## Validation rules

At minimum, repositories using `feature_cell` should enforce:

1. `scope` must be `workstream`.
2. `slug`, `title`, `goal`, `reason`, and `entered_at` should be present.
3. `feature_cell` must not contain Layer B mode names as substitutes for slice structure.
4. `feature_cell` must not contain Layer D state names as its own semantics.
5. `feature_cell` must not embed `control_profile` semantics when refs are sufficient.
6. A `feature_cell` should represent one coherent workstream, not a loose task collection.

## Anti-patterns

### 1. Using a feature cell for every non-trivial task

This creates ceremony without adding continuity value.

### 2. Treating the feature cell as a mode

Bad:

- we are in feature-cell mode

### 3. Treating the feature cell as a state

Bad:

- the work is feature_cell and blocked

Use Layer D for status.

### 4. Replacing slices with a narrative blob

A `feature_cell` should not become a giant note that loses the slice structure.

### 5. Turning the feature cell into heavyweight PM

Bad signs:

- excessive mandatory fields,
- large status taxonomies,
- ceremony for low-risk work,
- artifacts nobody uses.

## Summary

Use `feature_cell` when work needs a lightweight but durable workstream wrapper.

Keep it:

- workstream-scoped,
- continuity-oriented,
- lightweight,
- separate from slices,
- separate from `control_profile` semantics,
- and separate from Layer D status.
