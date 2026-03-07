

# Intake Loop

## Purpose

The intake loop converts an incoming request into an operationally usable task slice.

Its job is not to solve the work immediately. Its job is to:
- normalize the request,
- define the current work slice,
- capture the minimum Layer A classification,
- choose the current Layer B operating mode,
- apply Layer C only if needed,
- initialize Layer D control status,
- create a resumable task card.

This loop is the default entrypoint for all non-trivial incoming work in the harness.

## Outcome

A successful intake produces:
- one task card in `docs/harness/active/tasks/`,
- a filled Layer A core snapshot,
- exactly one current Layer B mode,
- any required Layer C control-profile or workstream-wrapper decision,
- an initialized Layer D record with `state`, `phase`, and `next_step`,
- links to the relevant inputs and references,
- a short work log entry describing the intake decision.

If the work clearly requires long-running coordination, intake may also create a workstream card in `docs/harness/active/workstreams/`.

## When to use this loop

Use the intake loop when:
- a new task arrives through chat, issue, ticket, note, or manual request,
- an inbox item has not yet been turned into a task card,
- an existing request is too raw to execute safely,
- a prior task needs to be resliced because the current unit of work was not well-formed.

Do not use the intake loop for routine continuation of a well-formed active task. In that case, use the execution loop.

## Inputs

Typical inputs:
- a raw request,
- links to repository files, docs, issues, PRs, or notes,
- user constraints,
- expected output artifact,
- any stated urgency, review requirement, or delivery boundary.

Input quality may be poor. Intake is allowed to produce a bounded draft task even when the request is incomplete.

## Core principles

### 1. Classify the current slice, not the whole universe

The unit of intake is the current executable or investigable slice.

Do not over-model the larger initiative unless the request clearly demands workstream treatment.

### 2. Prefer a small correct task over a large vague task

If a request is broad, define a smaller first slice with a concrete next step.

### 3. Choose one current operating mode

Layer B is current posture, not identity, not workflow type, and not long-term ownership.

### 4. Keep Layer C sparse

Apply control profiles and workstream wrappers only when they materially change how the work must be governed or organized.

### 5. Never leave a task without a next step

A task created by intake is incomplete unless its immediate next step is explicit.

## Intake procedure

### Step 1. Read and normalize the incoming request

Create a compact normalized summary:
- what is being asked,
- what artifact or outcome is expected,
- what references are available,
- what is still unclear,
- what appears in-scope for the first slice,
- what is explicitly out of scope for now.

If the request is extremely raw, write the summary directly into the new task card.

### Step 2. Decide whether this is a task slice or a workstream candidate

Default to a task slice.

Promote to workstream consideration only if one or more of the following are already clear:
- the work will span multiple meaningful slices,
- the work will likely require multiple PRs or staged delivery,
- the work will require durable handoffs or resumability across sessions,
- the work will likely change Layer B modes over time,
- the work needs workstream-level milestones or oversight.

If those conditions are not yet clear, create only a task card.

### Step 3. Create the task card

Create a new task file in `docs/harness/active/tasks/` using `task-card.template.md`.

Task cards store the operational Layer A-D record in structured frontmatter. Treat that frontmatter as authoritative.

Minimum required fields at creation time:
- `id`
- `title`
- `created_at`
- `updated_at`
- `layer_a` core fields
- `layer_b.current_mode`
- `layer_b.reason`
- `layer_c.feature_cell_ref`
- `layer_c.control_profiles`
- `layer_d.state`
- `layer_d.next_step`
- `layer_d.entered_at`
- `layer_d.updated_at`
- `layer_d_companion.lifecycle_scope`

The title should describe the current slice, not the entire possible future effort.

Good:
- `Investigate parser regression in block normalization`
- `Draft RFC structure for hierarchical segmentation`
- `Define acceptance contract for hybrid parser output`

Avoid overly broad titles such as:
- `Build parser system`
- `Fix RAG`
- `Improve architecture`

### Step 4. Fill the Layer A core classification

At intake, fill the required Layer A core only.

Required Layer A fields:
- `intent`
- `problem_uncertainty`
- `dependency_complexity`
- `knowledge_locality`
- `specification_maturity`
- `validation_burden`
- `blast_radius`
- `execution_horizon`

This is enough to support routing without overloading intake.

If some values are ambiguous, choose the best grounded current value and record the uncertainty in the task summary or open questions section.

Preferred starter values for commonly improvised fields:
- `intent`: `implement`, `refactor`, `debug`, `research`, `review`, `migrate`, `optimize`
- `dependency_complexity`: `self_contained`, `few_local_dependencies`, `cross_module`, `cross_service`, `external_or_multi_party`
- `knowledge_locality`: `fully_local`, `mostly_local`, `scattered_internal`, `external_research_required`, `tacit_human_required`

Use `research` for contract-definition or uncertainty-reduction slices when the dominant work is making the boundary explicit. Use `review` when critique, assessment, approval, or interpretation is the main requested outcome. If none is perfect, choose the closest canonical value and explain the nuance in notes rather than inventing a new value.

### Step 5. Choose exactly one Layer B current mode

Choose the dominant operating posture for the current slice.

Use the following routing defaults:
- use `research_scout` when the main work is understanding the problem or solution space,
- use `contract_builder` when the main work is defining scope, interface, contract, or acceptance conditions,
- use `routine_implementer` when the implementation path is clear and bounded,
- use `refactor_surgeon` when the goal is structural change with behavior preservation,
- use `debug_investigator` when behavior is failing and cause is not yet established,
- use `migration_operator` when the slice is part of a staged transition or replacement,
- use `optimization_tuner` when the slice is about measurable improvement of an existing path,
- use `quality_evaluator` when the dominant work is evaluation, diagnosis, or quality evidence generation.

Do not assign multiple modes during intake. If the task later changes shape, reroute it during execution.

### Step 6. Decide whether Layer C applies

Evaluate Layer C in this order:

1. `feature_cell`
2. non-baseline `control_profile`

#### Apply `feature_cell` only if the task already needs workstream treatment

If yes:
- create a workstream card,
- link the task card to that workstream,
- treat the current task as the first child slice.

#### Apply a reviewed-style `control_profile` only if continued progress should pause at an interpretation or review boundary

Typical examples:
- architecture options need human selection,
- RFC or contract must be reviewed before implementation,
- evaluation findings must be interpreted before the next move,
- the task should stop after producing a review packet.

Keep baseline control while drafting or shaping the contract itself. Add `reviewed` only when the slice has reached a real review boundary and should stop there before implementation-aligned continuation.

#### Apply a change-controlled or high-assurance `control_profile` only if stronger-than-baseline control is required

Typical examples:
- high blast radius,
- hard-to-reverse changes,
- sensitive migrations,
- explicit approval gate,
- rollout-sensitive operational change.

If none apply, leave Layer C empty.

Task cards now use canonical Layer C fields directly:
- `layer_c.feature_cell_ref`
- `layer_c.control_profiles`

If a linked workstream card is created, use its canonical `layer_c.feature_cell`, `layer_c.control_profiles`, `layer_d`, and `layer_d_companion` fields directly.

### Step 7. Initialize Layer D

Set the initial lifecycle control state.

Use these defaults:
- `draft` if the task exists but is not yet actionable,
- `active` if the next step is immediately executable,
- `checkpoint` if intake is complete but work should pause for review,
- `awaiting_approval` only if a real approval boundary already exists at intake,
- `blocked` only if a concrete blocker is already known.

Also set:
- `layer_d.phase`
- `layer_d.next_step`
- `layer_d.entered_at`
- `layer_d.updated_at`
- `layer_d_companion.blocking_reason` if blocked
- `layer_d_companion.checkpoint_reason` if checkpoint
- `layer_d_companion.lifecycle_scope: task`

The `next_step` must be concrete enough that another agent can resume without reinterpretation.

Weak examples:
- `continue`
- `work on it`
- `investigate more`

Strong examples:
- `Read parser normalization code path and isolate the first failing transformation step`
- `Draft RFC section outline with explicit inputs, outputs, and acceptance questions`
- `Compare current schema fields against required evaluation outputs and list gaps`

### Step 8. Add references and initial work log

Record:
- source links,
- relevant files,
- related issues or PRs,
- any assumptions made during intake.

Then add a short work log entry describing:
- why the slice was defined as it was,
- which Layer B mode was chosen,
- whether Layer C was applied,
- what the next step is.

### Step 9. Move or archive the raw inbox item

If the task was created from `docs/harness/active/inbox/`, either:
- remove the inbox item after its contents are captured elsewhere, or
- replace it with a pointer to the created task card.

Do not keep both a live inbox item and an unlinked task card as independent sources of truth.

## Output quality bar

An intake result is acceptable only if:
- the task slice is narrow enough that one current mode makes sense,
- the Layer A core is filled,
- the task has exactly one current Layer B mode,
- Layer C is either empty or explicitly justified,
- Layer D has a valid non-terminal state and a concrete `next_step`,
- another agent could resume the task without redoing intake from scratch.

## Promotion rule for workstreams

Create a workstream card only when task-only tracking becomes inadequate.

Use a workstream when:
- the effort will clearly outlive a single slice,
- multiple child tasks will exist in parallel or sequence,
- resumability and handoff quality matter across sessions,
- milestones or cross-slice decisions need durable tracking.

Do not create a workstream for every task. Task-only is the default.

## Anti-patterns

### Over-broad task cards

Do not turn a broad initiative into one task card with a vague title and no executable boundary.

### Blended modes

Do not write things like:
- `research + implementation`
- `debug/refactor`
- `planning/execution`

Pick one current mode.

### Premature Layer C usage

Do not apply `feature_cell` or a non-baseline `control_profile` just because the work feels important.

### Empty next step

Do not create a task in `active` state without a concrete next step.

### Using Layer D as workflow semantics

Do not encode detailed workflow meaning in state names or invent custom status variants during intake.

## Intake checklist

Use this checklist before considering intake complete.

- The request has been normalized into a short summary.
- A task card exists in `docs/harness/active/tasks/`.
- The task title describes the current slice.
- The Layer A core fields are filled.
- Exactly one Layer B mode is selected.
- Layer C has been evaluated in the correct order.
- Layer D has `state`, `phase`, and `next_step`.
- Any blocker, checkpoint reason, or approval boundary is recorded.
- References and assumptions are linked.
- A short work log entry exists.

## Minimal examples

### Example 1: raw bug report

Incoming request:

> Parser output is breaking list blocks after last refactor. Please investigate and fix.

Good intake result:
- task card created,
- current slice defined as investigation of regression cause,
- Layer B mode set to `debug_investigator`,
- Layer D state set to `active`,
- next step set to inspect the failing normalization stage,
- no non-baseline Layer C context yet.

### Example 2: broad feature request

Incoming request:

> We need hierarchical segmentation for the pipeline.

Good intake result:
- task card created for first bounded slice such as RFC structuring or contract definition,
- current mode set to `contract_builder` or `research_scout`,
- possible promotion to `feature_cell` only if the effort is clearly long-running,
- Layer D next step focused on producing the first bounded artifact.

### Example 3: review-first task

Incoming request:

> Draft the migration plan, but stop for review before any implementation.

Good intake result:
- task card created for migration plan drafting,
- current mode set to `migration_operator` or `contract_builder` depending on slice shape,
- reviewed-style `control_profile` selected if the drafted plan must stop for review,
- initial Layer D state may still be `active` if drafting can proceed now,
- later transition to `checkpoint` when the review packet is ready.

## Relationship to other loops

- Use the intake loop to create or reshape a task.
- Use the execution loop to continue active work.
- Use the workstream loop when `feature_cell` exists.
- Use the checkpoint/review loop when a review boundary has been reached.
- Use the handoff/resume loop whenever the task is being paused or transferred.

## Agent instruction shorthand

When operating as an intake agent:
1. normalize the request,
2. define the smallest useful current slice,
3. create the task card,
4. fill the Layer A core,
5. choose one current Layer B mode,
6. apply Layer C only if justified,
7. initialize Layer D with a concrete next step,
8. leave enough trace that another agent can continue without repeating intake.
