

# Routine Implementer

## Purpose

`routine_implementer` is the Layer B operating mode for executing a clear, bounded change when the implementation path is already sufficiently defined.

Use this mode when the dominant work is no longer broad discovery, contract formation, or failure diagnosis. The slice already has a stable enough target, and the main question is how to deliver the change cleanly within the current boundary.

This mode is the default execution posture for ordinary implementation slices that do not require a more specialized mode.

## Core question

When operating in `routine_implementer`, the central question is:

> What bounded change should be executed now against an already clear enough target?

The target may be:
- a feature slice,
- a bug fix whose cause is already known,
- a contract-driven implementation step,
- a documentation or configuration update with explicit expectations,
- a small integration step whose boundary is already defined.

## When to use

Use `routine_implementer` when one or more of the following are true:

- the expected outcome is already clear enough to execute,
- the contract, schema, or interface is sufficiently explicit,
- the current work is mainly writing or modifying code or other concrete artifacts,
- the root cause of a defect is already known and the current slice is the bounded fix,
- the next useful step is direct delivery rather than more clarification,
- the slice has a narrow enough boundary that ordinary implementation discipline is sufficient,
- the task’s main risk is correct execution, not unresolved problem framing.

This mode is often the right follow-on from `contract_builder` or `debug_investigator` once ambiguity has dropped enough.

## When not to use

Do not use `routine_implementer` when:

- the dominant work is still discovery, option mapping, or general investigation, in which case `research_scout` is usually better,
- the main problem is still defining the contract, schema, boundary, or acceptance condition, in which case `contract_builder` is usually better,
- behavior is failing and the cause is not yet isolated, in which case `debug_investigator` is usually better,
- the task is primarily behavior-preserving structural surgery, in which case `refactor_surgeon` is usually better,
- staged transition mechanics, rollback, or migration coordination dominate the slice, in which case `migration_operator` is usually better,
- the dominant work is evidence generation, readiness assessment, or evaluation, in which case `quality_evaluator` is usually better,
- the dominant work is measured improvement or tuning rather than ordinary delivery, in which case `optimization_tuner` is usually better.

Do not use this mode just because code will eventually be written. Use it when direct bounded execution is the main thing that should happen now.

## Typical Layer A signals

`routine_implementer` is often a good fit when Layer A looks something like this:

- `problem_uncertainty`: low
- `specification_maturity`: high or sufficiently high
- `dependency_complexity`: low-to-medium or manageable
- `validation_burden`: low-to-medium, or high but already well-defined
- `artifact_type`: often code, config, docs, or another bounded implementation artifact
- `execution_horizon`: short and bounded for the current slice
- `blast_radius`: often low-to-medium, though it can be higher if the slice is still clear and controlled

Common signals include:
- the expected output is explicit,
- acceptance boundaries are already known,
- the current slice can be implemented without inventing new major rules,
- the work may include bounded non-code artifact execution when expectations are already explicit,
- the next step is concrete enough that another agent could simply execute it.

## Primary working posture

When operating as `routine_implementer`, the agent should:

- execute against the current contract or boundary,
- keep the slice narrow and delivery-focused,
- avoid reopening already-settled design questions unless execution reveals a real mismatch,
- implement the smallest coherent change that satisfies the current slice,
- keep the task card, state, and next step truthful as implementation progresses,
- use validation proportionate to the task rather than over-expanding into unrelated work,
- stop and reroute if execution reveals that the slice was not actually clear.

The posture is controlled delivery, not broad exploration and not speculative redesign.

## Primary outputs

Typical outputs of `routine_implementer` include:

- implemented code changes,
- tests added or updated as part of the slice,
- updated configuration or wiring,
- documentation changes tied to the implemented behavior,
- small integration steps against an already defined contract,
- completed bounded feature increments,
- bounded bug fixes after cause is known.

A successful `routine_implementer` slice usually leaves the system with one concrete delivered change and a clear closure or next bounded step.

## Typical next-step patterns

Good `next_step` patterns in this mode include:

- `Implement the schema-to-segmentation adapter using the reviewed phase-1 field set.`
- `Add the regression test for nested list normalization and apply the bounded fix in the normalization pass.`
- `Update the parser output mapping to emit the required parent/child fields defined by the contract.`
- `Implement the new configuration flag and wire it through the ingestion path.`
- `Apply the reviewed interface change and update the affected call sites.`

Weak `next_step` patterns in this mode include:

- `implement feature`
- `fix bug`
- `continue coding`
- `work on task`

## Allowed autonomy pattern

`routine_implementer` can usually proceed autonomously while:

- applying a clear bounded change,
- updating affected local tests,
- making local implementation decisions that stay within the accepted contract,
- performing small local refactors that are clearly in service of the implementation slice,
- updating the task card and work log as execution advances.

It should usually slow down or stop when:

- the implementation reveals that the contract is not actually sufficient,
- failure behavior appears and root cause is no longer clear,
- the slice expands beyond one coherent change,
- a review boundary, approval boundary, or other non-baseline control boundary is reached,
- migration mechanics or rollout risk become the dominant issue,
- validation/evidence generation becomes the dominant next activity.

This means `routine_implementer` often hands off to other modes rather than trying to absorb every new issue into one execution slice.

## Typical validation style

Validation in this mode is usually delivery-oriented and local to the slice.

Typical forms include:
- targeted tests,
- local regression checks,
- contract-conformance checks,
- narrow integration checks,
- quick verification against the defined acceptance criteria,
- brief review before closure when required by local policy.

A `routine_implementer` slice is often considered good enough when:
- the change satisfies the stated boundary,
- the expected acceptance checks pass,
- the task does not leave unresolved ambiguity hidden inside the implementation,
- the result does not require immediate reinterpretation of the contract.

If validation becomes the main work rather than a bounded closing step, rerouting to `quality_evaluator` may be more appropriate.

## Common reroute triggers

Reroute away from `routine_implementer` when the dominant work changes.

Common reroute triggers include:

### Reroute to `debug_investigator`

When:
- the implementation reveals unexplained failing behavior,
- the change cannot proceed until the real failure cause is isolated,
- reproduction and diagnosis become the dominant work.

### Reroute to `contract_builder`

When:
- the expected behavior or boundary turns out to be underspecified,
- implementation cannot proceed safely without clarifying acceptance, schema, or interface rules,
- the task is no longer primarily execution but agreement formation.

### Reroute to `refactor_surgeon`

When:
- the slice becomes mainly behavior-preserving structural rework,
- the delivery goal shifts from new behavior to safe internal restructuring.

### Reroute to `migration_operator`

When:
- staging, compatibility, cutover, rollback, or migration sequencing becomes dominant,
- the slice is no longer an ordinary bounded implementation step.

### Reroute to `quality_evaluator`

When:
- the implementation change is in place and the dominant remaining work is evidence generation, benchmark comparison, or acceptance assessment.

## Common next modes

Typical next modes after `routine_implementer` are:
- `quality_evaluator`
- sometimes `debug_investigator`
- sometimes `contract_builder`
- sometimes `migration_operator`

A common pattern is:
- contract clarified -> `routine_implementer`
- implementation delivered -> `quality_evaluator` or `complete`

## Typical risks / failure modes

Common failure modes in `routine_implementer` include:

### 1. Silent scope expansion

The slice absorbs nearby work because it feels convenient, and the task stops being bounded.

### 2. Executing past ambiguity

The agent keeps coding even though the contract is not actually clear enough.

### 3. Hidden mode drift

The work has turned into debugging, contract clarification, or validation, but the task is still labeled as routine implementation.

### 4. Local success, global mismatch

The implementation works locally but quietly violates the intended contract or downstream assumptions.

### 5. Under-recorded progress

The code changes advance, but the task card, current state, and next step are not updated, reducing resumability.

### 6. Premature closure

The task is marked complete before the bounded acceptance checks or review boundary are actually satisfied.

## Good operating heuristics

Useful heuristics in this mode:

- implement the smallest coherent change that closes the slice,
- keep the change aligned to the already-defined boundary,
- prefer finishing one bounded step over partially advancing several nearby ones,
- if a new ambiguity appears, decide explicitly whether to reroute rather than coding through it,
- keep tests and verification proportionate to the actual slice,
- update the task card whenever the implementation materially changes the current reality,
- ask whether another agent could take over immediately from the current artifact state.

## Relationship to Layer C and Layer D

### Relationship to Layer C

`routine_implementer` may run inside a `feature_cell` when the slice is one bounded step inside a longer multi-slice workstream.

It may also run under one or more `control_profile` records when the implementation must satisfy explicit review, approval, evidence, traceability, or rollback obligations. Presets such as `reviewed`, `change_controlled`, or `high_assurance` may clarify that control context.

These Layer C constructs wrap or constrain the work. They do not define the current mode.

### Relationship to Layer D

A `routine_implementer` task is often:
- `active` while execution is in progress,
- sometimes `validating` when acceptance checks become dominant,
- sometimes `checkpoint` if the change should pause for review,
- sometimes `awaiting_approval` if a hard gate must be crossed,
- `complete` when the bounded implementation slice is done and accepted.

The mode can remain `routine_implementer` while the Layer D lifecycle state changes.

## Example task shapes

Typical tasks that fit `routine_implementer` well:

- implement a reviewed schema adapter,
- apply a bounded bug fix after root cause has been isolated,
- add the required fields defined by an accepted contract,
- wire a new feature flag through an already-defined path,
- update a bounded integration point after interface review,
- implement a narrow documentation-backed behavior change.

## Practical checklist

Use this checklist to validate whether `routine_implementer` is the right mode:

- Is the expected outcome already clear enough to execute?
- Is the current slice mainly about delivery rather than discovery, contract formation, debugging, or evaluation?
- Could another agent implement the next step without inventing major missing rules?
- Is the slice bounded enough to stay narrow during execution?
- Does exactly one implementation-focused posture clearly dominate?

If yes, `routine_implementer` is probably the right mode.

## Short operational summary

Use `routine_implementer` when the current slice is ready for direct bounded execution against a sufficiently clear target.

The hallmark of this mode is not “coding” in the generic sense. It is controlled delivery of one coherent change without reopening higher-level uncertainty unless the work itself proves that the slice was not actually ready.
