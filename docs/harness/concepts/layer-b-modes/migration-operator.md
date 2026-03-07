# Migration Operator

## Purpose

`migration_operator` is the Layer B operating mode for executing or preparing staged transitions where sequencing, compatibility, rollback, and operational safety dominate the current slice.

Use this mode when the work is not ordinary bounded implementation and not just contract shaping, but controlled movement from one system state, interface, schema, or operating path to another. The defining property of this mode is that transition mechanics matter as much as, or more than, the raw code change itself.

This mode is appropriate when the system must cross a boundary safely rather than merely implement a local change.

## Core question

When operating in `migration_operator`, the central question is:

> How can this transition be staged safely so that compatibility, reversibility, and decision gates are handled explicitly?

The target is not generic delivery. The target is controlled transition.

## When to use

Use `migration_operator` when one or more of the following are true:

- the slice is part of a schema, protocol, storage, infrastructure, or interface migration,
- the work requires staged rollout, phased cutover, or temporary coexistence of old and new paths,
- compatibility constraints or consumer coordination are central,
- rollback planning or reversibility is important,
- the system must move through intermediate transition states safely,
- sequencing and gate criteria matter more than raw implementation speed,
- operational safety and readiness checks dominate the current slice.

This mode is often the right posture for risky transitions even when the local code changes look straightforward in isolation.

## When not to use

Do not use `migration_operator` when:

- the dominant work is still broad exploration of what should be done, in which case `research_scout` is usually better,
- the main need is defining the contract or compatibility rules before the transition can be staged, in which case `contract_builder` is usually better,
- the slice is just a normal bounded implementation step with no meaningful transition mechanics, in which case `routine_implementer` is usually better,
- the task is diagnosing unexplained breakage rather than staging a transition, in which case `debug_investigator` is usually better,
- the dominant work is evidence generation or readiness assessment after a migration step has already been executed, in which case `quality_evaluator` is usually better,
- the main task is performance or cost tuning rather than state transition, in which case `optimization_tuner` is usually better,
- the slice is mainly internal structural cleanup with preserved behavior rather than transition management, in which case `refactor_surgeon` is usually better.

Do not use this mode merely because legacy code is involved. Use it when transition mechanics dominate the current slice.

## Typical Layer A signals

`migration_operator` is often a good fit when Layer A looks something like this:

- `problem_uncertainty`: low-to-medium or medium
- `dependency_complexity`: medium-to-high or high, often cross-system or cross-team
- `specification_maturity`: medium-to-high or high enough that the migration path can be staged explicitly
- `validation_burden`: high because rehearsal, rollout checks, or production-like confirmation matter
- `reversibility`: low, mixed, or declining across stages, so rollback and cutover design matter
- `sensitivity`: often medium or high because data, compatibility, or operational continuity can be affected
- `blast_radius`: medium, high, or cross-service
- `execution_horizon`: medium or long for the broader effort, even if the current slice is bounded

Common signals include:
- a transition boundary already exists,
- rollback or compatibility matters materially,
- transition mechanics are more important than raw local implementation speed,
- staged execution, cutover planning, or temporary coexistence is required,
- a stage may be reversible now but less reversible later,
- the slice must preserve service continuity or data integrity while moving state.

## Primary working posture

When operating as `migration_operator`, the agent should:

- define the transition stage explicitly,
- identify compatibility assumptions and dependencies,
- make rollback, fallback, or recovery paths visible,
- separate irreversible from reversible actions,
- prefer staged movement over one-shot cutovers when risk is meaningful,
- make go/no-go conditions explicit,
- keep implementation steps tied to transition safety rather than opportunistic adjacent changes,
- stop and surface higher control boundaries when the stage is not safe to cross autonomously.

The posture is sequencing-first and control-aware, not code-first delivery.

## Primary outputs

Typical outputs of `migration_operator` include:

- migration stage definitions,
- rollout or cutover plans,
- compatibility notes,
- rollback or recovery notes,
- staged implementation tasks tied to the transition,
- gate criteria,
- readiness checklists,
- temporary coexistence plans,
- explicit move/observe/advance recommendations.

A successful `migration_operator` slice usually leaves the transition more controlled and legible than before.

## Typical next-step patterns

Good `next_step` patterns in this mode include:

- `Define the stage-1 adapter path that allows old and new schema readers to coexist during rollout.`
- `Prepare the cutover checklist and explicit rollback conditions for the next migration stage.`
- `Implement the compatibility shim for downstream consumers before enabling the new output path.`
- `Document the irreversible steps in the backfill sequence and require approval before execution.`
- `Rehearse the migration stage against a representative environment and record gate results.`

Weak `next_step` patterns in this mode include:

- `migrate system`
- `roll out change`
- `continue migration`
- `work on transition`

## Allowed autonomy pattern

`migration_operator` can usually proceed autonomously while:

- preparing stage definitions,
- implementing clearly bounded compatibility steps,
- drafting rollback-aware plans,
- assembling gate criteria,
- tightening operational sequencing notes,
- preparing rehearsal or readiness artifacts.

It should usually slow down or stop when:

- the next stage crosses a hard approval boundary or other non-baseline control boundary,
- the move contains meaningful irreversibility,
- compatibility assumptions are underdefined and require contract work,
- the dominant work becomes evidence review rather than transition mechanics,
- unexpected breakage appears and diagnosis becomes the real task,
- the workstream needs milestone-level interpretation before continuing.

This mode commonly operates inside explicit Layer C control-profile context, but that context is not the mode.

## Typical validation style

Validation in this mode is transition-oriented and stage-aware.

Typical forms include:
- rehearsal checks,
- compatibility verification,
- rollout gate criteria,
- rollback path inspection,
- before/after readiness comparison,
- partial activation checks,
- production-observation plans for post-cutover phases.

A `migration_operator` slice is often considered good enough when:
- the current transition stage is explicitly defined,
- required compatibility and rollback assumptions are visible,
- the next gate is clear,
- the system can move to the next stage without hidden transition ambiguity.

If evidence gathering or interpretation becomes the main deliverable rather than the transition plan or stage step, rerouting to `quality_evaluator` may be more appropriate.

## Common reroute triggers

Reroute away from `migration_operator` when the dominant work changes.

Common reroute triggers include:

### Reroute to `contract_builder`

When:
- compatibility rules or transition contracts are not actually explicit enough,
- the migration cannot proceed safely until boundary semantics are clarified.

### Reroute to `routine_implementer`

When:
- the current slice is now just a normal bounded implementation step inside a broader migration context,
- transition mechanics are no longer dominant in this particular slice.

### Reroute to `quality_evaluator`

When:
- the main remaining work is readiness evidence, rollout observation, or findings interpretation,
- transition execution is no longer the dominant activity.

### Reroute to `debug_investigator`

When:
- the migration step reveals unexplained breakage and causal isolation becomes dominant.

### Reroute to `research_scout`

When:
- the supposed migration is actually still too underframed and needs broader discovery before a safe path can be defined.

## Common next modes

Typical next modes after `migration_operator` are:
- `quality_evaluator`
- `routine_implementer`
- sometimes `contract_builder`
- sometimes `debug_investigator`

A common pattern is:
- migration staged -> `migration_operator`
- stage executed or prepared -> `quality_evaluator` or `awaiting_approval`
- findings clear -> next stage or closure

## Typical risks / failure modes

Common failure modes in `migration_operator` include:

### 1. Treating migration as ordinary implementation

The transition is modeled as a simple code change even though sequencing and rollback are the real risk.

### 2. Hidden irreversibility

The slice contains one-way moves, but those points are not made explicit.

### 3. Weak rollback thinking

Rollback exists only nominally, or depends on assumptions that were never checked.

### 4. Compatibility blind spots

The migration plan underestimates downstream consumers, coexistence windows, or format/version assumptions.

### 5. Collapsing multiple risky moves into one step

Too much operational change is packed into one stage without clear gates.

### 6. Stale mode after evidence dominates

The task stays in migration posture even after the real work has become readiness evaluation or findings interpretation.

## Good operating heuristics

Useful heuristics in this mode:

- name the current migration stage explicitly,
- separate preparation, cutover, and observation steps clearly,
- identify what must be true before the next stage may proceed,
- make rollback and recovery assumptions concrete rather than implied,
- prefer staged compatibility over flag-day transitions when risk is meaningful,
- treat irreversible moves as decision boundaries,
- if a slice becomes just normal bounded coding, route it out of migration mode rather than keeping everything under one label.

## Relationship to Layer C and Layer D

### Relationship to Layer C

`migration_operator` may run inside a `feature_cell` when the migration spans multiple coordinated slices over time.

It may also run under one or more `control_profile` records when the transition carries explicit review, approval, evidence, traceability, or rollback obligations. Presets such as `change_controlled` or `high_assurance` are common examples when cutover, compatibility, or data risk is material.

These Layer C constructs wrap or constrain the work. They do not define the current mode.

### Relationship to Layer D

A `migration_operator` task is often:
- `active` while preparing or executing a bounded migration stage,
- `checkpoint` when the plan or stage findings should pause for review,
- `awaiting_approval` before a hard cutover or irreversible move,
- `validating` during rollout observation or readiness evidence gathering,
- `complete` when the bounded transition slice is done,
- sometimes `blocked` if a prerequisite system or decision is missing.

The mode can remain `migration_operator` while the Layer D lifecycle state changes.

## Example task shapes

Typical tasks that fit `migration_operator` well:

- stage a parser schema transition with temporary compatibility support,
- prepare a backfill plan with rollback constraints,
- define the cutover and observation steps for moving downstream consumers to a new interface,
- execute one bounded migration stage inside a larger workstream,
- rehearse a transition path before approval for production movement.

## Practical checklist

Use this checklist to validate whether `migration_operator` is the right mode:

- Is the main work about moving safely from one state/path/interface to another?
- Are sequencing, compatibility, rollback, or cutover concerns central?
- Would treating this as ordinary implementation hide material risk?
- Is the current slice bounded as one migration stage or transition step?
- Does exactly one transition-oriented posture clearly dominate?

If yes, `migration_operator` is probably the right mode.

## Short operational summary

Use `migration_operator` when the current slice should manage a staged transition under explicit compatibility, rollback, and gate discipline.

The hallmark of this mode is not “change something in a legacy system.” It is controlled movement across a risky boundary where transition mechanics dominate the work.
