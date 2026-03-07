

# Task Execution Loop

## Purpose

The task execution loop governs how an agent continues work on an existing task slice after intake is complete.

Its job is not to redesign the whole initiative. Its job is to:
- read the current task card as the authoritative control surface,
- verify that execution is allowed by the current Layer D state,
- perform the current bounded step,
- update the task record as the work changes shape,
- reroute or reslice when the current operating posture is no longer correct,
- leave the task in a resumable state after every meaningful boundary.

This loop is the default operating loop for active task-level work.

## Outcome

A successful execution cycle produces one or more of the following:
- progress on the current `next_step`,
- a refined task summary or scope boundary,
- updated Layer A classification if the slice has materially changed,
- an updated Layer B current mode if the operating posture has changed,
- a Layer C change if a review or governance boundary has become necessary,
- a Layer D transition such as `active -> validating`, `active -> checkpoint`, `active -> blocked`, or `validating -> complete`,
- new evidence, references, or decision links,
- a fresh concrete `next_step` for the next execution cycle.

## When to use this loop

Use the task execution loop when:
- a task card already exists,
- the task has passed intake,
- the task is currently actionable or ready for bounded continuation,
- the goal is to make progress on the current slice rather than normalize a new request.

Do not use this loop for:
- raw incoming work that has not yet been converted into a task card,
- workstream-level coordination across multiple child tasks,
- checkpoint review handling after a pause for interpretation,
- pure handoff or resume actions with no execution.

## Inputs

The execution loop expects an existing task card containing at least:
- task identity and summary,
- current Layer A snapshot,
- one current `layer_b.current_mode`,
- any active `layer_c.control_profiles` and any `layer_c.feature_cell_ref`,
- current `layer_d` status,
- current `layer_d.next_step`,
- relevant references and work log context.

The task card is the primary source of truth for execution.

## Core principles

### 1. Execute from the card, not from memory

Before doing work, read the current task card.

Do not rely on remembered intent, earlier chat context, or stale assumptions if they conflict with the recorded task state.

### 2. Respect Layer D as the control gate

Execution is permitted only when the current state allows it.

The loop should not silently work through a blocker, checkpoint, or approval boundary.

### 3. Keep the current slice small and explicit

Execution should work on the current bounded slice, not absorb all adjacent work opportunistically.

### 4. Reclassify early when the slice changes shape

If the task stops matching its current Layer A or Layer B framing, update it rather than forcing progress under the wrong posture.

### 5. Always leave resumable trace

Every meaningful execution step should end with an updated task record and a concrete next step or terminal state.

## Execution procedure

### Step 1. Read the current task card

Start by reading the full current task card.

Confirm:
- the task summary still reflects the current slice,
- the Layer A snapshot is still plausible,
- the Layer B mode still matches the dominant posture,
- Layer C control context or workstream links are understood,
- the Layer D state permits the kind of work being attempted,
- the `next_step` is concrete enough to execute.

If the task card is missing critical fields, repair the card first before continuing.

### Step 2. Check whether execution is allowed by Layer D

Use Layer D as the operational gate.

#### Allowed execution states

Execution usually proceeds when the state is:
- `active`,
- `validating` when validation work itself is the current execution,
- `draft` only if the explicit purpose of this cycle is to finish shaping the task into an actionable state.

#### Non-execution states

Do not continue normal execution when the state is:
- `blocked`,
- `checkpoint`,
- `awaiting_approval`,
- `complete`,
- `cancelled`.

Instead:
- use the review loop for `checkpoint`,
- wait for or record the required decision for `awaiting_approval`,
- resolve blockers before proceeding from `blocked`,
- do not reopen `complete` or `cancelled` casually; create a new task or decision trail if resumed.

### Step 3. Execute the current bounded step

Work only on the current `next_step` or on the smallest bounded set of actions required to complete it.

Examples:
- inspect a code path,
- draft a contract section,
- implement a clearly scoped change,
- run a validation command,
- compare expected and actual outputs,
- prepare a checkpoint packet.

Avoid silent scope expansion.

If adjacent issues are discovered, record them and decide explicitly whether they belong in:
- the same current slice,
- a resliced follow-up task,
- the parent workstream,
- or a separate unrelated task.

### Step 4. Update the work log immediately after a meaningful step

After each meaningful boundary, write a short work log entry.

Record:
- what was done,
- what was observed,
- what changed in understanding,
- what evidence was produced,
- whether the task remains in the same mode/state,
- what should happen next.

The work log should make later resumption possible without replaying the full investigation.

### Step 5. Decide whether the task still matches its current slice

During execution, reassess whether the current task card still represents a coherent slice.

Signs the task should be resliced:
- the scope has grown beyond one dominant operating posture,
- a new substantial subproblem has appeared,
- the next useful step now depends on a different acceptance contract,
- the current task has mixed multiple unrelated outcomes,
- the original title no longer describes the current work.

If reslicing is required:
- update the current task to reflect what it actually covered,
- create a new task for the next coherent slice,
- link the relationship in the task summaries or references,
- avoid turning one task card into an unbounded work log for everything.

### Step 6. Reassess Layer A when the problem shape changes

Layer A should not be rewritten for minor noise, but it should be updated when the slice materially changes.

Reassess the Layer A core when execution reveals changes in:
- uncertainty,
- dependency complexity,
- specification maturity,
- validation burden,
- blast radius,
- execution horizon.

Examples:
- a seemingly routine implementation turns out to require cross-system dependency coordination,
- a bug investigation reveals that the real issue is unclear contract definition,
- a documentation task becomes an evaluation-heavy acceptance problem.

When Layer A changes, note why in the work log.

### Step 7. Reassess Layer B when the dominant posture changes

Choose one current mode at all times.

Typical reroutes:
- `routine_implementer -> debug_investigator` when implementation reveals unexplained failing behavior,
- `debug_investigator -> contract_builder` when the real problem is an undefined interface or acceptance contract,
- `research_scout -> contract_builder` when exploration has narrowed to a concrete design contract,
- `contract_builder -> routine_implementer` when the contract is sufficiently defined for execution,
- `migration_operator -> quality_evaluator` when the dominant work becomes evidence generation and comparison.

If the mode changes:
- update `layer_b.current_mode`,
- update `layer_b.reason`,
- update `layer_b.reroute_triggers` if they changed,
- ensure `layer_d.next_step` matches the new posture.

Do not keep an obsolete mode for convenience.

### Step 8. Reassess Layer C only when execution crosses a real boundary

Layer C should remain sparse during execution.

Evaluate whether execution has revealed the need for:

#### a non-baseline `control_profile`

Add or adjust one when continued autonomous work should stop at a review boundary or when the task now requires stronger-than-baseline control.

Examples:
- multiple architecture options now need selection,
- an RFC draft is ready for review before implementation,
- evaluation findings need interpretation,
- the next move would commit to a direction that should be reviewed first,
- unexpectedly high blast radius,
- irreversible migration step,
- production-sensitive rollout,
- explicit signoff requirement discovered during work.

#### `feature_cell`

Promote to workstream container only when task-level tracking is no longer adequate.

Examples:
- multiple linked child slices are now required,
- the effort now clearly spans multiple sessions and delivery stages,
- cross-slice milestones or handoffs have become necessary.

When Layer C changes, update the task card immediately and add any required linked artifact such as a workstream card or review packet.

Task cards now use canonical Layer C fields directly. If a linked workstream card also needs an update, use its canonical `layer_c.feature_cell`, `layer_c.control_profiles`, `layer_d`, and `layer_d_companion` fields directly.

### Step 9. Transition Layer D when the control status changes

Layer D should reflect the current control condition, not hidden workflow semantics.

Common transitions:
- `draft -> active` when the task becomes executable,
- `active -> blocked` when a real blocker prevents continued work,
- `active -> checkpoint` when a review packet is ready and progress should pause,
- `active -> awaiting_approval` when a hard approval boundary is reached,
- `active -> validating` when validation becomes the dominant activity,
- `validating -> complete` when acceptance is satisfied,
- `active -> complete` when the slice is done and no separate validation phase is needed,
- `active -> cancelled` when the task is intentionally terminated.

For every non-trivial transition, update the relevant companion fields:
- `layer_d_companion.blocking_reason`
- `layer_d_companion.unblock_condition`
- `layer_d_companion.checkpoint_reason`
- `layer_d_companion.approval_ref`
- `layer_d_companion.evidence_refs`
- `layer_d_companion.decision_ref`

Never change state without updating the task narrative enough to explain why.

### Step 10. Refresh `next_step` or close the task

At the end of the execution cycle, do one of two things:
- set a fresh concrete `next_step`, or
- move the task into a terminal or paused state with the required boundary context.

A good `next_step` is:
- specific,
- local to the current slice,
- executable by another agent without rereading everything.

Weak examples:
- `keep going`
- `finish task`
- `do validation`

Strong examples:
- `Write failing regression test for nested list normalization using the reproduced sample input`
- `Draft section comparing current parser output schema against desired intermediate schema`
- `Prepare checkpoint packet with three migration options and explicit rollback considerations`

## State-specific guidance

### When `state = active`

Normal execution is allowed.

The main responsibility is to make bounded progress and keep the task card current.

### When `state = validating`

The dominant work is evidence generation, verification, comparison, or acceptance checking.

Record:
- commands run,
- scenarios covered,
- outputs observed,
- evaluation findings,
- whether acceptance conditions were met.

### When `state = blocked`

Do not continue normal execution.

Record the blocker precisely. Good blockers are concrete:
- missing repository access,
- missing input file,
- unresolved decision dependency,
- failing prerequisite migration,
- absent acceptance criteria.

Also record the best known `unblock_condition`.

### When `state = checkpoint`

Do not continue autonomous forward execution past the declared review boundary.

Prepare or link the relevant review packet, findings summary, or decision request.

### When `state = awaiting_approval`

Do not proceed across the hard gate until the approval event is recorded.

Attach or reference the approval packet if applicable.

### When `state = complete`

The slice is done.

Record the acceptance basis:
- implemented and reviewed,
- validated by tests,
- evaluated against required outputs,
- explicitly accepted,
- or another concrete closure basis.

### When `state = cancelled`

Record why the task was intentionally terminated and whether follow-up work replaced it.

## Output quality bar

An execution cycle is acceptable only if:
- the task card remains the authoritative current description of the slice,
- the Layer D state at the end matches reality,
- the task has one current Layer B mode,
- any Layer A or Layer C change is explicitly justified,
- evidence or decisions are linked when relevant,
- the task ends with either a concrete `next_step` or a valid paused/terminal state.

## Anti-patterns

### Executing through a boundary

Do not continue working through `checkpoint`, `awaiting_approval`, or `blocked` as if they were advisory labels.

### Silent rerouting

Do not let the real work become debugging, contract design, or evaluation while leaving the task card in an obsolete mode.

### Scope accretion

Do not keep absorbing adjacent work into the same task because it is nearby.

### Stale next step

Do not leave the old `next_step` in place after it has already been completed or invalidated.

### State flips without evidence

Do not mark a task `complete`, `checkpoint`, or `awaiting_approval` without enough narrative, evidence, or references to make the boundary intelligible.

### Using the task card as a diary instead of a control surface

The work log can be detailed, but the task card must still clearly expose:
- what this slice is,
- what `layer_b.current_mode` it is in,
- what `layer_d.state` it is in,
- what `layer_d.next_step` is.

## Execution checklist

Use this checklist during or at the end of each execution cycle.

- The task card was read before continuing work.
- The current Layer D state permits the attempted work.
- The current `next_step` was either executed or deliberately replaced.
- The work log captures what changed.
- Layer A was reassessed if the slice materially changed.
- Layer B still reflects the dominant posture.
- Layer C was updated only if a real boundary emerged.
- Layer D matches the real control condition.
- Evidence, decision, blocker, or approval references were linked if relevant.
- The task now has a fresh `next_step` or a well-formed paused/terminal state.

## Minimal examples

### Example 1: implementation reveals a bug investigation

Starting state:
- mode: `routine_implementer`
- state: `active`
- next step: implement parser normalization adjustment

Observed during execution:
- current behavior fails in an unexpected earlier stage,
- cause is not established.

Good execution result:
- work log updated with reproduction findings,
- Layer B rerouted to `debug_investigator`,
- Layer A uncertainty may increase,
- Layer D remains `active`,
- next step becomes reproduction isolation rather than continued implementation.

### Example 2: draft reaches review boundary

Starting state:
- mode: `contract_builder`
- state: `active`
- next step: finish RFC acceptance section

Observed during execution:
- draft is complete enough for human review,
- further progress should pause until the direction is confirmed.

Good execution result:
- a review-oriented slice `control_profile` recorded or confirmed,
- review packet linked,
- Layer D transitions to `checkpoint`,
- `checkpoint_reason` recorded,
- no further autonomous implementation is attempted.

### Example 3: validation completes the slice

Starting state:
- mode: `quality_evaluator`
- state: `validating`
- next step: run evaluation cases and compare outputs

Observed during execution:
- required cases passed,
- evidence bundle created,
- acceptance condition satisfied.

Good execution result:
- evidence refs linked,
- acceptance basis recorded,
- Layer D transitions to `complete`.

## Relationship to other loops

- Use the intake loop to create or reshape a task before execution.
- Use the task execution loop for bounded task-level progress.
- Use the workstream loop when coordinating multiple child slices.
- Use the checkpoint/review loop when the task has paused for review or interpretation.
- Use the handoff/resume loop when the task is being transferred or paused between agents.

## Agent instruction shorthand

When operating as an execution agent:
1. read the current task card,
2. verify that Layer D allows the intended work,
3. execute the current bounded step,
4. update the work log and references,
5. reclassify Layer A or reroute Layer B if the slice changed shape,
6. apply Layer C only if a real control boundary emerged,
7. update Layer D to match reality,
8. leave a concrete next step or a well-formed paused/terminal state.
