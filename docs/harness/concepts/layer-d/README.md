# Layer D: Lifecycle Control Plane

## Purpose

Layer D defines the **minimal shared lifecycle control plane** for agentic work.

Its job is to record the **current execution-control status** of a tracked item so that humans and agents can tell whether work may proceed, is paused, is blocked, is awaiting review or approval, is validating, or is finished.

Layer D is intentionally small. It is not a full workflow engine, not a domain delivery methodology, and not a replacement for workflow-local phase logic.

## What Layer D owns

Layer D owns the following concerns:

- the **current lifecycle/control status** of a tracked item,
- the **universal state vocabulary** used across the harness,
- the **minimal schema** for lifecycle records,
- task-scope and workstream-scope lifecycle tracking,
- and the basic transition principles for moving between lifecycle states.

This is the shared control-plane layer for answering questions such as:

- can this task proceed now?
- is this item blocked?
- is a review boundary currently active?
- is explicit approval currently required?
- is validation now the dominant current activity?
- is this tracked scope complete or intentionally cancelled?

## What Layer D does not own

Layer D does **not** own:

- Layer A classification of the work,
- Layer B operating mode selection,
- Layer C `feature_cell` or `control_profile` semantics,
- reviewer or approver role policy,
- rollback policy,
- evidence policy,
- traceability policy,
- rich workflow semantics beyond local `phase`,
- or arbitrary domain-specific state machines.

Layer D should stay small. When more detail is needed, put that detail into:

- `phase`,
- companion fields,
- linked artifacts,
- local policy references,
- or other layers.

## Relationship to Layers A, B, and C

The boundary between layers must stay explicit.

- **Layer A** describes the current work slice.
- **Layer B** describes how the agent should work now.
- **Layer C** defines the control regime and workstream wrapper.
- **Layer D** records the current lifecycle gate/status inside that context.

A useful shorthand:

- **Layer C owns the regime**
- **Layer D owns the current gate**

This means:

- a `reviewed` control profile is not the same thing as `checkpoint`,
- a `change_controlled` profile is not the same thing as `awaiting_approval`,
- a `feature_cell` is not a state,
- and a Layer B mode such as `quality_evaluator` is not a Layer D lifecycle value.

## Canonical state set

Layer D uses one intentionally small universal state set:

- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

This set is intended to be sufficient across repositories and workflows.

Workflow-local nuance should go into:

- `phase`,
- `next_step`,
- reason fields,
- evidence references,
- decision references,
- and linked artifacts,

rather than into a growing list of universal states.

## Core design rules

The following rules define the intended shape of Layer D.

### 1. One record, one canonical state

A Layer D record has exactly one current canonical `state`.

Do not create composite lifecycle labels that try to combine:

- operating mode,
- control regime,
- review semantics,
- approval semantics,
- and workflow detail

into one giant state string.

### 2. Non-terminal items should usually remain actionable

For non-terminal items, the record should usually make the next move visible.

That means:

- `active` should have a concrete `next_step`,
- `blocked` should have a real `blocking_reason`,
- `checkpoint` should usually explain the active review/control boundary,
- `awaiting_approval` should usually show what approval is missing,
- `validating` should usually indicate what evidence is being gathered or interpreted.

### 3. Keep review distinct from approval

Use:

- `checkpoint` for review, interpretation, or disposition boundaries,
- `awaiting_approval` for hard signoff boundaries.

Do not collapse them.

### 4. `validating` is a real lifecycle state

Use `validating` when validation or observation becomes the dominant current work.

Do not leave an item in `active` merely because implementation technically finished if the real current posture is now evidence generation or verification.

### 5. Layer D must not encode other layers

Layer D must not be used as a hidden substitute for:

- Layer B mode identity,
- Layer C control-profile identity,
- or Layer A classification.

### 6. Workstream state is not mechanically derived

When both workstream-scope and task-scope lifecycle records exist, do not infer the workstream state automatically from child task states.

The workstream is its own tracked object.

## Scope model

Layer D may be tracked at two scopes:

- **task scope**
- **workstream scope**

### Task scope

Task scope is the default.

Use task-scope Layer D when you are controlling the current bounded work slice.

### Workstream scope

Workstream-scope Layer D becomes relevant when a Layer C `feature_cell` exists and the workstream itself has meaningful lifecycle status.

Examples:

- overall workstream is still `active`,
- overall workstream is at a checkpoint,
- release approval is pending at workstream scope,
- rollout observation is active at workstream scope,
- the workstream is complete or cancelled overall.

### Coexistence

Task-scope and workstream-scope Layer D may coexist.

That is often the clearest model for long-running work.

## How to use this directory

Recommended reading order:

1. Read this `README.md` for the Layer D boundary and map.
2. Read `states.md` for the canonical meanings of the eight states.
3. Read `schema.md` for the normative field contract and invariants.
4. Read `scope-and-transitions.md` for task/workstream interaction and transition logic.
5. Read `examples.md` for concrete worked cases.

Use this directory when you need to answer:

- what state should this record be in?
- what fields should accompany that state?
- should lifecycle be tracked at task scope, workstream scope, or both?
- is this a review pause, approval gate, validation phase, or dependency block?
- how should Layer D remain separate from Layer C and Layer B?

## File map

- `README.md` — umbrella spec and boundary for Layer D
- `states.md` — canonical meanings of the eight universal states
- `schema.md` — normative data contract for Layer D records
- `scope-and-transitions.md` — scope rules, transition patterns, and Layer C interaction
- `examples.md` — worked examples showing correct Layer D usage

## Minimal examples of interpretation

A few quick examples:

- A captured task that is not yet actionable → `draft`
- A slice that may proceed now with a concrete next step → `active`
- A task waiting on an upstream dependency → `blocked`
- A design packet waiting for interpretation → `checkpoint`
- A rollout packet waiting on explicit go/no-go signoff → `awaiting_approval`
- A benchmark run or rollout observation now dominates → `validating`
- A bounded tracked scope is done → `complete`
- A tracked scope is intentionally terminated → `cancelled`

A workstream may be `active` while one child task is `blocked`.

A workstream may be `awaiting_approval` even when no single child task is currently in that exact state.

## Usage notes

Keep Layer D small and durable.

Prefer:

- improving record quality,
- keeping `next_step` concrete,
- recording reasons and evidence clearly,
- and using local `phase` for detail

over extending the universal state ontology.

Do not add new universal states casually.

When the model seems too small, the right move is often to improve:

- `phase`,
- companion fields,
- linked packets,
- decision refs,
- or scope handling

rather than to grow the shared state set.

## Summary

Layer D is the shared lifecycle control plane for the harness.

It should remain:

- small,
- explicit,
- separate from Layer A, Layer B, and Layer C,
- usable at task scope and workstream scope,
- and strong enough to make the current control status legible at any moment.
