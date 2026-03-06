# Operational Playbook for Layered Agentic Work
## Status

Draft v1.0

## Purpose

This document defines a **minimal operational playbook** for handling incoming tasks and maintaining workflow in the layered agentic work model.

It is designed to work **with** the existing layered architecture rather than replacing it:

- **Layer A** classifies the current work slice.
- **Layer B** selects the current atomic operating mode.
- **Layer C** applies overlays and containers.
- **Layer D** records lifecycle control status.

The playbook answers a narrower question:

> How should work be taken in, routed, executed, maintained, handed off, and closed in a way that stays faithful to Layers A-D?

The main design constraint is deliberate: this playbook must remain a **thin operational loop**, not a second taxonomy and not a hidden universal workflow state machine.

## Why this playbook exists

The layered model gives a clean architecture, but teams still need a practical way to operate day to day.

Without an operational playbook, several failure modes appear quickly:

- incoming work is executed before it is properly classified,
- tasks are mislabeled with operating modes as if they were permanent identity,
- long-running work is tracked as one oversized task instead of as a workstream,
- review and approval behavior is improvised rather than modeled,
- lifecycle state becomes overloaded with routing meaning,
- handoff quality degrades because the "next step" and decision context are not maintained.

This playbook exists to prevent those failures while keeping process overhead low.

## Design goals
### 1. Stay aligned with the layer boundaries

The playbook must preserve the separation between:

- classification,
- operating posture,
- overlays / containers,
- and lifecycle state.

### 2. Remain minimal

The playbook should define the smallest set of mandatory artifacts, checks, and update rules that still support reliable execution and resumability.

### 3. Be usable on ordinary incoming tasks

The default path should work for small tasks, not only for large programs.

### 4. Scale to long-running work

The same playbook should support promotion into a workstream container when needed.

### 5. Optimize for resumability and handoff

At any point, another human or agent should be able to answer:

- what this task is,
- how it should be worked now,
- what extra control regime applies,
- whether it can proceed,
- and what the next concrete action is.

## Non-goals

This playbook does **not** attempt to define:

- a universal domain-specific delivery methodology,
- a program-level planning framework,
- a replacement for local engineering standards,
- a detailed approval policy for every organization,
- a comprehensive artifact taxonomy for all teams,
- or a large canonical state machine.

Workflow-specific detail should continue to live in:

- local `phase`,
- linked artifacts,
- local policy/profile documents,
- and the current task or workstream context.

## Core operational principle

For every incoming item, the system should be able to answer five questions:

1. **What is this current work slice?**
2. **How should the agent work on it now?**
3. **Does it require extra governance or a long-horizon wrapper?**
4. **What is its current lifecycle control status?**
5. **What is the next executable step?**

These five questions map directly to Layers A-D plus one explicit operational discipline:

- Layer A answers question 1.
- Layer B answers question 2.
- Layer C answers question 3.
- Layer D answers question 4.
- `next_step` answers question 5.

## The minimal operating loop

The playbook is built around one repeatable loop:

1. **Intake** the request.
2. **Create or update** a task card.
3. **Classify** the current slice with Layer A.
4. **Route** to one current Layer B mode.
5. **Apply** any needed Layer C constructs.
6. **Set** Layer D control status, local `phase`, and `next_step`.
7. **Execute** the current slice.
8. **Update** the record at every meaningful boundary.
9. **Reclassify or promote** when the shape changes.
10. **Close, cancel, or hand off** with explicit evidence or decision context.

This loop should be lightweight enough to use on ordinary tasks and structured enough to support larger workstreams.

## Operational entities
### 1. Task slice

The default operational unit.

A task slice represents the **current bounded unit of work** being handled now. It should be small enough that one current Layer B mode is meaningful.

A task slice is the default entry point for all incoming work.

### 2. Workstream

A longer-running coordinated unit containing multiple task slices across time.

A workstream should usually be represented through a **Layer C `feature_cell` container** when:

- the work spans multiple slices,
- multiple mode changes are expected,
- milestone tracking matters,
- resumability and handoff pressure are high,
- or workstream-level visibility is needed.

### 3. Review boundary

A point at which continuation depends on reviewer interpretation or disposition.

This is usually expressed through a Layer C `review_gatekeeper` overlay and a Layer D state such as `checkpoint` or, in stronger cases, `awaiting_approval`.

### 4. Approval boundary

A stronger control point where continuation requires explicit signoff.

This is often associated with Layer C `governance_escalation` and Layer D `awaiting_approval`.

## Canonical minimal artifact set

The playbook should keep the artifact set deliberately small.

### Mandatory for all work
#### 1. Task card

Every incoming request should be represented by a task card.

This is the primary operational record.

### Required only when applicable
#### 2. Workstream card

Required when the work is promoted into a `feature_cell` or equivalent long-horizon wrapper.

#### 3. Decision log

Required when meaningful checkpoints, approvals, cancellations, reroutes, or scope decisions occur.

#### 4. Evidence bundle or evidence references

Required when review, validation, approval, or completion depends on evidence beyond the task narrative.

### Optional but often useful

- milestone list,
- handoff notes,
- risk summary,
- rollback or recovery notes,
- acceptance summary,
- evaluation summary.

The important rule is that artifacts should be introduced because they improve control, resumability, or validation clarity, not because the process wants ceremony.

## Default policy: task-first, workstream-later

Every incoming request should begin as a **task slice**, not as a workstream.

Promotion to a workstream should happen only when the work clearly exceeds the task-only model.

This prevents premature operational overhead and keeps small tasks cheap to handle.

### Promote to a workstream when one or more are true

- `execution_horizon` is clearly multi-PR or long-running,
- multiple Layer B mode transitions are expected,
- sparse but explicit HITL points are needed over time,
- multiple linked tasks must be coordinated,
- workstream-level lifecycle tracking is useful,
- resumability or handoff pressure is high,
- milestone tracking materially improves control.

### Do not promote merely because

- the task feels important,
- there are many notes,
- the work might grow later,
- or someone wants to "keep options open."

Default to the simpler structure until there is operational evidence that the task-only model is insufficient.

## Intake procedure

Every incoming request should follow the same minimal intake path.

### Step 1. Capture the request

Create a task card in `draft` unless the work is already clearly actionable.

Record at minimum:

- title,
- request summary,
- references or links,
- expected output or artifact,
- owner or current executor,
- timestamps,
- and any immediately visible missing context.

### Step 2. Bound the current slice

Before classification, decide what the **current slice** actually is.

The slice should be narrow enough that one dominant operating mode makes sense.

Good examples:

- compare parser options for first-stage ingestion,
- write the task card and classify the migration slice,
- implement the bounded schema refactor,
- reproduce and isolate the failing regression,
- assemble evidence for benchmark review.

Bad examples:

- build the entire feature end to end,
- fix the whole platform,
- migrate the full system eventually,
- redesign everything related to retrieval quality.

If the request is too large, create a smaller initial slice first.

### Step 3. Fill the required Layer A core

Before active execution, fill the minimum Layer A subset:

- `intent`
- `problem_uncertainty`
- `dependency_complexity`
- `knowledge_locality`
- `specification_maturity`
- `validation_burden`
- `blast_radius`
- `execution_horizon`

This is the minimum classification required to make reliable downstream decisions.

### Step 4. Choose the current Layer B mode

Select exactly one current operating mode.

Do not create blended labels.

Use the dominant question:

- do we need to discover,
- bound the contract,
- execute directly,
- diagnose,
- stage a risky transition,
- optimize against a measurable target,
- or produce quality evidence?

### Step 5. Apply Layer C in fixed order

Evaluate Layer C in this order:

1. Does the work need a `feature_cell` container?
2. Does it need a `review_gatekeeper` overlay?
3. Does it need a `governance_escalation` overlay?

This order keeps orchestration concerns separate from review and governance concerns.

### Step 6. Set Layer D

Set:

- `state`,
- `phase`,
- `next_step`,
- and any needed companion fields.

If the task can proceed, set it to `active` with a concrete next step.

If it is waiting on context, keep it in `draft` or mark it `blocked`, depending on whether work had already become actionable and then lost a dependency.

### Step 7. Begin execution

Only after the above is in place should the task move into normal execution.

## Classification discipline for Layer A in operations

The playbook does not redefine Layer A, but it does impose an operational discipline around it.

### Rule 1. Classify the current slice, not the entire future

Do not try to classify the whole program if only one bounded slice is being worked now.

### Rule 2. Use the required core for all non-trivial tasks

Optional fields remain optional unless local practice proves they repeatedly change routing or governance.

### Rule 3. Reclassify when the shape changes materially

Layer A is not permanent identity. Reclassification is expected when:

- uncertainty decreases,
- specification matures,
- validation burden increases,
- blast radius becomes clearer,
- the execution horizon expands,
- or the current slice changes altogether.

### Rule 4. Do not encode mode, state, or overlays in Layer A

Layer A should not contain:

- current operating mode,
- lifecycle state,
- overlay identity,
- or workstream container identity.

## Routing discipline for Layer B in operations

Layer B answers only one question:

> How should the agent work now on the current slice?

### Routing guide

Use the following practical mapping.

| Dominant condition now | Typical route |
|---|---|
| Solution space still being discovered | `research_scout` |
| Objective known but contract still forming | `contract_builder` |
| Clear bounded implementation slice | `routine_implementer` |
| Structural cleanup under invariants | `refactor_surgeon` |
| Failing behavior with unknown cause | `debug_investigator` |
| Compatibility, sequencing, rollback, or cutover dominates | `migration_operator` |
| Measurable technical tuning dominates | `optimization_tuner` |
| Quality evidence or evaluation dominates | `quality_evaluator` |

### Routing rules
#### Rule A. Specification maturity overrides raw intent

If the request says "implement" but the contract is still immature, route to `contract_builder` first.

#### Rule B. Diagnosis overrides direct fixing

If a bug is known but root cause is not, route to `debug_investigator` rather than direct implementation.

#### Rule C. Heavy evaluation burden can dominate execution

When ordinary tests are not sufficient, `quality_evaluator` may be the correct current mode even if implementation recently finished.

#### Rule D. Governance does not redefine mode

High-risk work may keep the same Layer B mode while adding Layer C overlays and stronger Layer D gates.

#### Rule E. Horizon affects containment, not atomic mode

Long-running work may require `feature_cell`, but the active slice should still have one current atomic mode.

### Reroute triggers

The task card should explicitly record reroute triggers when useful, such as:

- hidden ambiguity discovered,
- contract frozen,
- root cause isolated,
- benchmark requirement surfaced,
- approval requirement surfaced,
- work expanded into multi-slice coordination.

## Layer C application rules in operations

Layer C modifies or wraps work. It is not a status model.

### Evaluation order

Always evaluate Layer C in this order:

1. container need,
2. review need,
3. governance need.

### 1. `feature_cell`

Apply when the work should no longer be treated as a one-shot task.

#### Typical triggers

- multi-slice or multi-PR horizon,
- high handoff pressure,
- multiple mode transitions expected,
- workstream-level visibility needed,
- milestone tracking matters,
- explicit long-horizon coordination is required.

#### Operational implications

- create or maintain a workstream card,
- link slices to the workstream,
- maintain sparse milestones,
- keep decision history visible,
- preserve resumability and handoff clarity,
- optionally track workstream-scope Layer D alongside task-scope Layer D.

### 2. `review_gatekeeper`

Apply when reviewer interpretation or critique is a real continuation condition.

#### Typical triggers

- findings need interpretation,
- a design trade-off needs review,
- conformance or acceptance depends on judgment,
- architecture or policy review is required,
- evidence exists but must be reviewed before continuation.

#### Operational implications

- prepare review-ready summary or packet,
- keep evidence references current,
- route to `checkpoint` or `awaiting_approval` when the control boundary is active,
- capture review outcome in decision references or notes.

### 3. `governance_escalation`

Apply when the work proceeds under stricter-than-baseline control obligations.

#### Typical triggers

- large blast radius,
- hard or irreversible reversibility profile,
- security, privacy, integrity, or public-contract sensitivity,
- explicit approval requirement,
- rollout-sensitive or migration-sensitive transition.

#### Operational implications

- strengthen evidence discipline,
- record readiness and risk more explicitly,
- attach rollback or recovery context when relevant,
- use approval references and decision records,
- expect stronger Layer D boundaries such as `checkpoint`, `awaiting_approval`, or `validating`.

### Scope rules
#### Slice scope

Use when the construct applies only to the current task slice.

#### Workstream scope

Use when the construct applies across the longer-running workstream.

#### Inheritance

Workstream-level overlays may influence child tasks, but inheritance should be explicit rather than assumed.

Record inheritance when local practice needs it, for example:

- `inherits_to_children: true`
- `inherits_to_children: false`

### Composition rules

- At most one container per scope.
- Overlays may stack.
- The stricter obligation wins when obligations conflict.

## Layer D operating rules

Layer D is the shared control plane. Operational discipline matters here because status drift is the fastest way to lose workflow clarity.

### Canonical state meanings
#### `draft`

The work item exists but is not yet fully actionable.

Use when:

- the task has been captured but not fully framed,
- classification is incomplete,
- essential context is still missing,
- or the first actionable slice has not yet been established.

#### `active`

The task may proceed now.

Use when:

- no blocking dependency prevents work,
- no required checkpoint is active,
- no explicit approval gate is currently holding continuation,
- and the next step is executable.

#### `blocked`

The task cannot proceed because a dependency or condition prevents continuation.

Use when:

- required context is missing after the task had become actionable,
- an external dependency is unavailable,
- a prerequisite deliverable has not landed,
- a technical blocker prevents continuation.

Always record `blocking_reason`, and preferably `unblock_condition`.

#### `checkpoint`

Work is paused at a review or control boundary before continuation.

Use when:

- a review packet is ready,
- design trade-offs need interpretation,
- findings must be dispositioned,
- a required checkpoint review is active.

Always record a meaningful `checkpoint_reason`.

#### `awaiting_approval`

Work is waiting on explicit signoff.

Use when:

- the control regime requires formal approval,
- the go/no-go boundary has been reached,
- continuation is not permitted without signoff.

Store the approval or decision reference when available.

#### `validating`

Execution is largely done, and validation or observation is now the dominant activity.

Use when:

- test execution dominates,
- offline evaluation dominates,
- rollout observation dominates,
- acceptance evidence collection dominates.

Validation is not merely "some tests exist"; it is the dominant current posture of the slice.

#### `complete`

The scoped work is done.

Use when:

- the slice objective has been satisfied,
- required evidence has passed,
- required acceptance has occurred,
- and no further execution remains inside the current scope.

#### `cancelled`

The work was intentionally stopped and will not continue in this scope.

Use when:

- the task is explicitly dropped,
- superseded by another slice,
- or closed by decision rather than completion.

### Layer D schema in the playbook
#### Core

```yaml
layer_d:
  state: draft | active | blocked | checkpoint | awaiting_approval | validating | complete | cancelled
  phase: <workflow-local phase or null>
  next_step: <explicit next action or null>
  entered_at: <timestamp or null>
  updated_at: <timestamp or null>
```

#### Companion fields

```yaml
layer_d_companion:
  blocking_reason: <string or null>
  unblock_condition: <string or null>
  checkpoint_reason: <string or null>
  approval_ref: <artifact or decision ref or null>
  evidence_refs: []
  decision_ref: <string or null>
  lifecycle_scope: task | workstream
```

### State discipline rules
#### Rule 1. Every non-terminal item should have `next_step`

If a task is active, blocked, at checkpoint, awaiting approval, or validating, the next action should be clear.

#### Rule 2. `blocked` requires an explicit reason

Do not use `blocked` as a vague status.

#### Rule 3. Do not confuse review with approval

Use `checkpoint` for review or interpretation boundaries.

Use `awaiting_approval` for explicit signoff boundaries.

#### Rule 4. Do not encode overlays into state

`review_gatekeeper` and `governance_escalation` remain Layer C constructs even when they make `checkpoint` or `awaiting_approval` more likely.

#### Rule 5. Workstream and task scopes may both exist

When `feature_cell` is present, it can be useful to track Layer D at both:

- task scope,
- workstream scope.

But the state values themselves remain the same.

## Task card template

```yaml
task:
  id: T-...
  title: ...
  summary: ...
  refs: []
  output_expectation: ...
  owner: ...
  created_at: ...
  updated_at: ...

  layer_a:
    intent: implement | refactor | debug | research | review | migrate | optimize
    problem_uncertainty: known_pattern | local_ambiguity | design_heavy | research_exploration | open_ended_investigation
    dependency_complexity: self_contained | few_local_dependencies | cross_module | cross_service | external_or_multi_party
    knowledge_locality: fully_local | mostly_local | scattered_internal | external_research_required | tacit_human_required
    specification_maturity: vague_idea | scoped_problem | draft_contract | frozen_contract | implementation_ready
    validation_burden: trivial_local_check | tests_strong_confidence | partial_signals_only | offline_eval_required | production_confirmation_required
    blast_radius: local | subsystem | cross_service | platform
    execution_horizon: atomic | multi_step | multi_pr | long_running_program | ongoing_lane
    handoff_need: low | medium | high

  layer_b:
    current_mode: research_scout | contract_builder | routine_implementer | refactor_surgeon | debug_investigator | migration_operator | optimization_tuner | quality_evaluator
    reason: ...
    reroute_triggers: []

  layer_c:
    container: null
    overlays: []

  layer_d:
    state: draft | active | blocked | checkpoint | awaiting_approval | validating | complete | cancelled
    phase: ...
    next_step: ...
    entered_at: ...
    updated_at: ...

  layer_d_companion:
    blocking_reason: null
    unblock_condition: null
    checkpoint_reason: null
    approval_ref: null
    evidence_refs: []
    decision_ref: null
    lifecycle_scope: task
```

### Notes

- Only fill what is necessary for the current slice.
- Use linked artifacts rather than bloating the card body.
- Keep `reason` and `next_step` concrete.

## Workstream card template

Use only when a `feature_cell` is present.

```yaml
workstream:
  id: W-...
  title: ...
  goal: ...
  owner: ...
  task_ids: []
  milestone_ids: []
  created_at: ...
  updated_at: ...

  layer_c:
    container:
      name: feature_cell
      scope: workstream
      reason: ...
    overlays: []

  layer_d:
    state: draft | active | blocked | checkpoint | awaiting_approval | validating | complete | cancelled
    phase: ...
    next_step: ...
    entered_at: ...
    updated_at: ...

  layer_d_companion:
    blocking_reason: null
    unblock_condition: null
    checkpoint_reason: null
    approval_ref: null
    evidence_refs: []
    decision_ref: null
    lifecycle_scope: workstream
```

### Minimal workstream operating package

A workstream commonly maintains:

- workstream card,
- linked task cards,
- sparse milestone list,
- decision log,
- handoff notes,
- declared HITL points,
- evidence references.

Not every workstream needs a heavy packet set. The package should stay as small as the control needs allow.

## Execution rules
### Rule 1. Execute from the current gate only

Do not proceed as if the task were active when the current state is actually:

- `blocked`,
- `checkpoint`,
- or `awaiting_approval`.

### Rule 2. Update at meaningful boundaries

Update the task or workstream record when one of the following happens:

- the current slice changes,
- the mode changes,
- a review packet is produced,
- a blocker appears or clears,
- a decision is made,
- validation becomes dominant,
- the work closes or is cancelled.

### Rule 3. Re-slice when one mode is no longer enough

If the current item no longer has one dominant mode, the task is usually too large.

Create a new child slice or successor slice rather than forcing one card to represent multiple active problem shapes.

### Rule 4. Close with evidence or decision context

Do not move items to `complete` or `cancelled` as naked status flips.

Record:

- evidence references,
- acceptance summary,
- or decision reference,

as appropriate.

## Review and approval handling
### Review handling

When `review_gatekeeper` applies:

1. keep the active work moving until the review boundary is actually reached,
2. prepare the relevant review-ready packet,
3. move to `checkpoint` when continuation depends on review,
4. record review outcome,
5. either return to `active`, move to `awaiting_approval`, or close the slice.

### Approval handling

When `governance_escalation` implies explicit signoff:

1. assemble readiness evidence,
2. record rollback or recovery context when relevant,
3. move to `awaiting_approval` when the signoff boundary is active,
4. attach `approval_ref` or equivalent decision record,
5. continue only after the approval condition is satisfied.

### Important distinction

A task may have a review overlay without currently being at a checkpoint.

A task may have a governance overlay without currently awaiting approval.

Layer C indicates the **regime**. Layer D indicates the **current gate**.

## Validation handling

Validation should be handled as a first-class operational phase rather than an afterthought.

### Move to `validating` when validation becomes dominant

Examples:

- running and interpreting benchmarks,
- running offline evaluation,
- rollout observation,
- acceptance evidence collection,
- production confirmation.

### Keep evidence references current

When in `validating`, the record should point to:

- test results,
- evaluation artifacts,
- dashboards,
- rollout observations,
- acceptance summaries,
- or linked reports.

### Exit criteria

Validation should resolve into one of:

- `complete`,
- `active` again if findings require additional work,
- `checkpoint` if interpretation is needed,
- `awaiting_approval` if signoff is the next boundary,
- or `cancelled` if the slice is intentionally terminated.

## Handoff and resumability rules

The playbook should support interruption and resumption without relying on memory.

### Minimum handoff quality bar

At handoff time, another operator should be able to answer:

- what the task is,
- why the current mode was chosen,
- what overlays or container apply,
- what the current state is,
- what the next step is,
- what decisions have already been made,
- and what evidence or artifacts matter.

### Handoff package

For ordinary tasks, the task card is usually enough if it is maintained well.

For workstreams, handoff usually requires:

- workstream card,
- linked current tasks,
- milestone view,
- decision log,
- handoff notes,
- current evidence links.

### Resume procedure

When resuming work:

1. read Layer A, Layer B, Layer C, and Layer D,
2. confirm that the current slice is still the right slice,
3. confirm that the current mode is still the right mode,
4. check whether overlays or workstream conditions changed,
5. execute from `next_step` or reclassify if reality has changed.

## Maintenance cadence

The playbook should define a lightweight maintenance discipline.

### Continuous maintenance rules
#### Rule 1. Every active item should remain actionable

If `state = active`, the next action should not be ambiguous.

#### Rule 2. Every blocked item should expose the block clearly

The blocker must be named, not implied.

#### Rule 3. Review and approval items should point to artifacts

When an item is at `checkpoint` or `awaiting_approval`, the supporting packet or evidence should be discoverable.

#### Rule 4. Completion should be evidenced

Completed work should point to proof, not just a status change.

### Suggested review rhythm

A minimal operational review can use the following questions:

1. Which items are still in `draft` and should be clarified or dropped?
2. Which active items do not have a concrete next step?
3. Which blocked items lack a clear unblock condition?
4. Which checkpoint or approval items lack a review or approval packet?
5. Which workstreams need promotion, decomposition, or closure?

This can be done informally. The value comes from the questions, not from process theater.

## Anti-patterns

The following practices should be explicitly avoided.

### 1. Encoding everything into lifecycle state

Do not create giant custom states such as:

- `design_review_pending_implementation`,
- `feature_cell_active_review`,
- `migration_cutover_validation_gate`,
- or similar composite labels.

Use:

- Layer B for operating posture,
- Layer C for overlays and containers,
- Layer D for control status,
- and local `phase` for detail.

### 2. Treating Layer B as permanent identity

A task is not "a debug task forever" merely because one slice required `debug_investigator`.

### 3. Treating `feature_cell` as a mode

It is a container, not an operating posture.

### 4. Treating `review_gatekeeper` as a state

It is an overlay, not a current gate.

### 5. Treating `governance_escalation` as synonymous with approval

It is a regime, not the current status.

### 6. Keeping oversized tasks that should be re-sliced

If one card needs several simultaneous modes, it is probably too large.

### 7. Leaving `next_step` vague

"Continue work" is not an operational next step.

### 8. Promoting workstreams too early

Do not create long-horizon wrappers until coordination pressure actually exists.

## Worked examples
### Example 1. Ambiguous implementation request
#### Incoming request

"Build the first version of the segmentation pipeline."

#### Operational handling

- Create task card in `draft`.
- Bound the first slice as: define the scoped contract and success criteria for the first implementation slice.
- Fill Layer A core:
  - `intent = implement`
  - `problem_uncertainty = design_heavy`
  - `specification_maturity = scoped_problem`
  - `validation_burden = partial_signals_only`
  - `execution_horizon = multi_pr`
- Route to Layer B `contract_builder`.
- Apply Layer C `feature_cell` at workstream scope if the work clearly spans several slices and PRs.
- Possibly apply `review_gatekeeper` if architecture review is needed.
- Set Layer D:
  - `state = active`
  - `phase = contract_drafting`
  - `next_step = produce initial contract with boundaries, assumptions, and acceptance criteria`

### Example 2. Regression with unknown cause
#### Incoming request

"Fix the failing parser output for tables in the PDF ingestion pipeline."

#### Operational handling

- Create task card.
- Bound the first slice as repro and root-cause isolation.
- Layer A core suggests `intent = debug`, unknown cause, moderate dependency complexity.
- Route to `debug_investigator`.
- Keep Layer C empty unless review or governance demands surface.
- Set Layer D:
  - `state = active`
  - `phase = reproduction_and_isolation`
  - `next_step = reproduce failure on saved fixture and isolate stage causing malformed table output`
- After root cause is found, reroute to `routine_implementer` or `refactor_surgeon` as appropriate.

### Example 3. Rollout-sensitive migration
#### Incoming request

"Move the schema and cut traffic to the new contract without downtime."

#### Operational handling

- Create task card or workstream if clearly multi-slice.
- Layer A indicates migration intent, elevated blast radius, hard reversibility concerns, and production confirmation burden.
- Route to `migration_operator`.
- Apply `governance_escalation`.
- Apply `feature_cell` at workstream scope if the work spans several cutover slices.
- Use `checkpoint` for readiness review.
- Use `awaiting_approval` at explicit go/no-go boundary.
- Use `validating` during rollout observation.
- Close only when acceptance evidence and required approval conditions are satisfied.

## Suggested v1 adoption policy

To keep rollout simple, start with a narrow mandatory baseline.

### Mandatory in v1

- every incoming task gets a task card,
- Layer A required core is filled for non-trivial work,
- exactly one Layer B current mode is selected,
- Layer C is explicitly evaluated in the standard order,
- Layer D contains `state`, `phase`, and `next_step`,
- `blocked` always has `blocking_reason`,
- non-terminal states should have a real `next_step`.

### Recommended but optional in v1

- reroute trigger tracking,
- workstream-level lifecycle alongside task lifecycle,
- inheritance flags for workstream overlays,
- milestone list,
- handoff notes,
- evidence bundles beyond linked references.

### Add later only if operationally justified

- broader required Layer A fields,
- richer policy/profile references,
- standardized review packet templates,
- standardized approval packet templates,
- automation on top of the schema,
- dashboards derived from Layer D plus selected Layer A fields.

## Compressed operator checklist
### Intake checklist

- Create task card.
- Bound the current slice.
- Fill Layer A required core.
- Pick one Layer B mode.
- Evaluate `feature_cell`.
- Evaluate `review_gatekeeper`.
- Evaluate `governance_escalation`.
- Set Layer D `state`, `phase`, `next_step`.
- Begin execution only from the current gate.

### Update checklist

- Did the current slice change?
- Is the current mode still right?
- Did a new overlay or workstream need appear?
- Is the current state still accurate?
- Does `next_step` still reflect reality?
- Do new evidence or decision references need to be attached?

### Closure checklist

- Is the slice actually complete in its current scope?
- Has required validation been satisfied?
- Has required review or approval been satisfied?
- Are evidence or decision references recorded?
- Should this item be completed, cancelled, or succeeded by a new slice?

## Final operating rule

This playbook should be interpreted conservatively:

- keep the shared model small,
- keep the task slice current,
- keep the operating mode singular,
- keep overlays and containers explicit,
- keep lifecycle state clean,
- and keep `next_step` concrete.

If the system does that consistently, it will support both simple tasks and long-running work without collapsing the architecture back into one overloaded workflow model.
