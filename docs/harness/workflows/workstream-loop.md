

# Workstream Loop

## Purpose

The workstream loop governs how an agent operates when a long-running effort has been promoted into a `feature_cell` container.

Its job is not to replace task execution. Its job is to:
- maintain the workstream as a coherent multi-slice effort,
- keep task-level work aligned to the workstream goal and current milestones,
- decide when to create, update, pause, or close child task slices,
- track workstream-level decisions, risks, and handoff points,
- apply workstream-scope control context when review or approval obligations must operate above individual tasks,
- keep the effort resumable across sessions, agents, and delivery stages.

This loop is the default operating loop for any effort that can no longer be managed cleanly as a single task card.

## Outcome

A successful workstream cycle produces one or more of the following:
- a current and coherent workstream card,
- one or more created, updated, or closed child task cards,
- refreshed milestones, priorities, or execution sequencing,
- workstream-scope Layer C control context when needed,
- a workstream-scope Layer D status that matches the current control condition,
- linked decisions, evidence, and handoff notes,
- a clear next step either for the workstream itself or for a specific child task.

## When to use this loop

Use the workstream loop when:
- a task has been promoted to `feature_cell`,
- the effort spans multiple meaningful slices,
- multiple child tasks exist or are clearly needed,
- the effort is expected to continue across sessions or agents,
- milestones, sequencing, or workstream-level review now matter.

Do not use this loop for:
- a single bounded task that still fits cleanly in one task card,
- raw incoming work that has not gone through intake,
- detailed execution within one child task,
- pure checkpoint handling for one paused task.

## Inputs

The workstream loop expects:
- an existing workstream card,
- linked child task cards or a decision to create them,
- the workstream goal and current scope boundary,
- any current milestones or sequencing notes,
- current workstream-scope Layer C and Layer D records,
- relevant decision, evidence, and handoff references.

The workstream card is the control surface for the effort at workstream scope.

Current workstream cards still use legacy `container` / `overlays` frontmatter as shorthand. Interpret those fields through the v2 Layer C model and use `docs/harness/maintainining.md` for the full compatibility mapping and migration status.

## Core principles

### 1. The workstream is a coordination layer, not a giant task

A workstream card should coordinate child slices. It should not absorb all detailed execution into one monolithic record.

### 2. Task-level execution still happens in task cards

The workstream loop decides what slices exist and how they relate. Individual implementation, investigation, or evaluation still belongs in task execution.

### 3. Promote only when task-only tracking is inadequate

`feature_cell` exists for long-running, multi-slice, resumable work. Do not use it for every important task.

### 4. Keep scope and sequencing explicit

A workstream should make it easy to answer:
- what this effort is trying to achieve,
- what slice is active now,
- what child tasks exist,
- what milestone or boundary is next,
- what decision or review point is pending.

### 5. Separate workstream status from child task status

Workstream-level Layer D should describe the control status of the workstream itself. It should not be mechanically derived from child task states.

## Workstream procedure

### Step 1. Read the workstream card and linked child tasks

Start by reading the workstream card.

Confirm:
- the workstream goal is still valid,
- the scope boundary is still coherent,
- the listed child tasks still represent the effort accurately,
- current milestones or phases still make sense,
- Layer C control context at workstream scope is still justified,
- Layer D at workstream scope matches the current control situation.

Then inspect any active or recently changed child tasks relevant to the current cycle.

### Step 2. Decide whether the effort still requires workstream treatment

A workstream should exist only while task-only tracking is inadequate.

Keep workstream treatment when one or more of these remain true:
- multiple child slices are active or planned,
- sequencing across slices matters,
- milestones or staged delivery matter,
- resumability across sessions or agents matters,
- workstream-scope review or approval/control boundaries are required.

If those conditions no longer apply, consider retiring the workstream after closing or unlinking remaining child tasks and recording the decision.

### Step 3. Reconfirm the workstream goal and boundary

A workstream card should clearly state:
- the goal of the larger effort,
- the current scope boundary,
- what is intentionally excluded for now,
- what completion would mean at workstream scope.

If the workstream has drifted, update it.

Signs the workstream boundary is wrong:
- it has absorbed multiple unrelated initiatives,
- the goal has become too vague to guide slice creation,
- workstream milestones no longer match actual execution,
- child tasks do not clearly contribute to the same outcome.

If necessary, split the workstream or narrow its scope.

### Step 4. Decide what child slices are needed now

The workstream loop should decide whether to:
- continue an existing child task,
- create a new child task,
- close a finished child task,
- cancel an obsolete child task,
- reslice a child task that has become too broad,
- sequence the next child task after a completed boundary.

Create a new child task when:
- the next useful step is a new coherent slice,
- a new dominant Layer B mode is required,
- a prior child task has reached a natural boundary,
- a separate acceptance or review boundary is needed.

Do not keep one child task alive forever if it has already changed shape multiple times.

### Step 5. Maintain workstream milestones and sequencing

The workstream card should expose current sequencing clearly.

You do not need a heavy project plan, but you should record enough structure to answer:
- what milestone or stage is current,
- which child task is expected to move next,
- what dependency or decision gates exist,
- what boundary would trigger the next transition.

Milestones may be simple, for example:
- discovery complete,
- contract approved,
- implementation slice complete,
- validation complete,
- rollout decision pending.

If milestone language becomes noisy, simplify it rather than multiplying labels.

### Step 6. Reassess workstream-scope Layer C

At workstream scope, Layer C usually matters more than at single-task scope.

Evaluate in this order:
1. whether `feature_cell` still applies
2. whether a workstream-scope non-baseline `control_profile` applies

`feature_cell` is already the workstream-wrapper assumption for this loop.

#### Apply or retain a reviewed-style workstream control profile when:
- a cross-slice design or architecture decision is pending,
- a milestone requires human interpretation before new child tasks should proceed,
- the workstream should pause after producing a packet or milestone artifact,
- workstream direction depends on review of findings across multiple tasks.

#### Apply or retain a change-controlled or high-assurance workstream control profile when:
- the workstream has high blast radius overall,
- staged release or migration governance is required,
- explicit signoff is needed before crossing a milestone,
- risk management must operate at effort scope rather than within one task.

Do not automatically mirror task-scope control context at workstream scope. Apply it only when the boundary is genuinely workstream-wide.

### Step 7. Reassess workstream-scope Layer D

Layer D at workstream scope should answer control-plane questions about the larger effort.

Common workstream states:
- `active` when the effort is in progress and at least one meaningful next move exists,
- `checkpoint` when the workstream should pause at a milestone review boundary,
- `awaiting_approval` when a hard workstream-level gate exists,
- `blocked` when a workstream-level blocker prevents meaningful continuation,
- `validating` when the dominant effort is cross-slice validation or readiness checking,
- `complete` when the workstream goal has been achieved,
- `cancelled` when the effort is intentionally terminated.

Examples of workstream-level blockers:
- unresolved architecture decision,
- missing external dependency that blocks all remaining slices,
- pending approval to proceed with the next stage,
- invalidated workstream goal.

Do not mark the workstream `blocked` just because one child task is blocked if the overall effort can still progress elsewhere.

### Step 8. Record decisions, evidence, and risks at the right scope

The workstream loop should maintain shared context that would be awkward to duplicate in each child task.

Record at workstream scope when the item affects the larger effort, for example:
- architecture decisions affecting multiple tasks,
- milestone approvals,
- shared risk notes,
- readiness findings,
- cross-slice evidence bundles,
- handoff notes for future agents.

Keep task-local details in task cards. Keep workstream-wide decisions in the workstream card or linked decision files.

### Step 9. Keep child tasks aligned

For each active child task, ensure:
- it still contributes to the workstream goal,
- its title describes a coherent slice,
- it has one current Layer B mode,
- its Layer D state matches reality,
- its next step is current,
- any workstream dependencies or milestones are reflected.

If a child task has drifted away from the workstream, either:
- detach it,
- close it,
- or move it into a different workstream.

### Step 10. Refresh next steps at both scopes

At the end of the workstream cycle, the harness should make it clear:
- what the next workstream-level action is, and/or
- which child task should move next.

A good workstream-level `next_step` might be:
- `Create child task for intermediate schema definition and link it to milestone: contract formation`
- `Pause at checkpoint and prepare workstream review packet comparing the three architecture paths`
- `Request approval for migration stage 2 using linked readiness findings`

If the next work belongs entirely within an existing child task, the workstream card may point to that task rather than restating all detail.

## When to create a child task

Create a child task when the next useful unit of work has:
- a coherent slice boundary,
- one dominant operating mode,
- a meaningful next step,
- its own acceptance or review boundary.

Examples:
- define intermediate output schema,
- investigate parser regression cause,
- draft evaluation harness outline,
- implement stage-1 adapter,
- compare baseline and candidate outputs.

## When to close or cancel a child task

Close a child task when its slice is done and the acceptance basis is clear.

Cancel a child task when:
- the slice is no longer needed,
- the workstream direction changed,
- the child task was superseded by a better slice,
- the task should be replaced rather than kept open indefinitely.

Record the relationship if a replacement task was created.

## Workstream completion rule

A workstream can be marked `complete` when:
- the stated workstream goal has been met,
- no required child slices remain open,
- any required validation, approval, or readiness boundary has been satisfied,
- closure evidence or decision context is linked.

A workstream can be marked `cancelled` when:
- the larger effort is intentionally terminated,
- or the workstream is superseded by a different effort structure.

Do not leave abandoned workstreams indefinitely in `active` state.

## Output quality bar

A workstream cycle is acceptable only if:
- the workstream goal and boundary are still clear,
- child tasks reflect real current slices,
- workstream Layer C and Layer D match real control conditions,
- milestones or sequencing are current enough to guide action,
- shared decisions, risks, and evidence are recorded at the right scope,
- another agent could understand how the effort is organized and what should happen next.

## Anti-patterns

### Treating the workstream as a mega-task

Do not turn the workstream card into one huge execution log containing all implementation details.

### Creating workstreams too early

Do not promote every broad-sounding task into a `feature_cell` before real multi-slice coordination exists.

### Mirroring child state blindly

Do not derive the workstream state mechanically from the states of child tasks.

### Stale child task lists

Do not leave finished, drifted, or superseded child tasks unexamined in the workstream card.

### Missing workstream next step

Do not leave the workstream card without a clear next coordination action or an indicated next child task.

### Unbounded workstream scope

Do not let one workstream silently absorb every adjacent idea related to the same general theme.

## Workstream checklist

Use this checklist during or at the end of each workstream cycle.

- The workstream card was read before changing coordination state.
- The workstream still justifies `feature_cell` treatment.
- The workstream goal and scope boundary are current.
- Child tasks still represent coherent slices.
- Milestones or sequencing notes still match reality.
- Workstream-scope Layer C was reassessed where relevant.
- Workstream-scope Layer D matches the current control condition.
- Shared decisions, risks, evidence, and handoff notes were updated where relevant.
- The next workstream action or next child task is explicit.

## Minimal examples

### Example 1: broad feature becomes multi-slice effort

Observed:
- one task on hierarchical segmentation has split into schema design, segmentation logic, and evaluation planning.

Good workstream result:
- a workstream card is created,
- the original task is treated as one child slice,
- new child tasks are created for the additional coherent slices,
- milestones are recorded at a lightweight level,
- the workstream `next_step` points to the next child task to activate.

### Example 2: workstream reaches milestone review

Observed:
- several child tasks produced architecture findings,
- the next stage should not proceed until a direction is reviewed.

Good workstream result:
- a reviewed-style non-baseline control boundary is recorded at workstream scope,
- a review packet is linked,
- the workstream Layer D moves to `checkpoint`,
- child tasks are not allowed to continue into the next stage autonomously.

### Example 3: one child blocked, workstream still active

Observed:
- implementation child task is blocked on an external dependency,
- evaluation and documentation child tasks can still proceed.

Good workstream result:
- the blocked child task records its own blocker,
- the workstream remains `active`,
- the workstream next step points to another viable child slice,
- no false workstream-wide blockage is declared.

## Relationship to other loops

- Use the intake loop to normalize new requests into task slices before workstream promotion.
- Use the task execution loop for detailed work inside each child task.
- Use the workstream loop to coordinate a `feature_cell` effort across slices.
- Use the checkpoint/review loop when the workstream or a child task has paused for review.
- Use the handoff/resume loop whenever the effort is being transferred across agents or sessions.

## Agent instruction shorthand

When operating as a workstream agent:
1. read the workstream card and relevant child tasks,
2. confirm that the effort still requires `feature_cell` treatment,
3. keep the workstream goal, boundary, and milestones current,
4. create, close, or reslice child tasks as needed,
5. apply workstream-scope Layer C only when a true cross-slice boundary exists,
6. update workstream-scope Layer D to match reality,
7. record shared decisions, risks, evidence, and handoff notes at the right scope,
8. leave a clear next coordination step or next child task.
