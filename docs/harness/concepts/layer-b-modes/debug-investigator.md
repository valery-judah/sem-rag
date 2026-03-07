# Debug Investigator

## Purpose

`debug_investigator` is the Layer B operating mode for diagnosing failing, incorrect, or unexpected behavior when the root cause is not yet established.

Use this mode when the dominant work is not implementing the fix yet, but isolating the problem: reproducing the issue, narrowing the failure surface, identifying the first broken boundary, and forming or confirming a causal explanation.

This mode is appropriate when execution would be premature because the system does not yet know what is actually wrong.

## Common next doc

If the task card already says `layer_b.current_mode: debug_investigator`, use this file for mode-specific guidance.

If mode fit is unclear, use `docs/harness/policies/routing-rules.md`.
If the mode is confirmed and `layer_d.state` permits forward work, continue with `docs/harness/workflows/task-execution-loop.md`.
If the current state is paused or terminal, use `docs/harness/operator-map.md` to jump to the correct boundary doc.

## Core question

When operating in `debug_investigator`, the central question is:

> What is failing, where does it first fail, and what causal explanation is strong enough to justify the next slice?

The target is not general exploration. The target is causal isolation.

## When to use

Use `debug_investigator` when one or more of the following are true:

- observed behavior is wrong, failing, regressed, or inconsistent with the expected result,
- the system can reproduce or partially reproduce the issue,
- the cause is not yet isolated,
- the current useful work is narrowing the failure surface rather than implementing a fix,
- several plausible causes exist and the next step is diagnosis,
- the task needs to identify the first failing transformation, boundary, or assumption,
- the main output should be a root-cause hypothesis, confirmed cause, or clear handoff to a bounded fix.

This mode is often the right first response to regressions, unexplained breakage, and surprising output mismatches.

## When not to use

Do not use `debug_investigator` when:

- the dominant work is still broad problem-space discovery rather than diagnosis of a concrete failure, in which case `research_scout` is usually better,
- the failure cause is already known and the current slice is just applying the bounded fix, in which case `routine_implementer` is usually better,
- the real problem is not unexplained behavior but an undefined or disputed contract, in which case `contract_builder` is usually better,
- the dominant work is evidence generation or acceptance assessment after a fix or candidate change, in which case `quality_evaluator` is usually better,
- the task is mainly behavior-preserving structural work rather than fault isolation, in which case `refactor_surgeon` is usually better,
- transition mechanics, rollback, or staged migration behavior dominate the slice, in which case `migration_operator` is usually better.

Do not keep a task in `debug_investigator` after diagnosis is already good enough and the real work has become implementation or contract clarification.

## Typical Layer A signals

`debug_investigator` is often a good fit when Layer A looks something like this:

- `problem_uncertainty`: medium or high
- `specification_maturity`: often medium-to-high if expected behavior is known, but causal understanding is low
- `dependency_complexity`: low-to-high depending on how many interacting parts could be responsible
- `validation_burden`: medium because reproduction and confirmation matter
- `blast_radius`: often medium or high if the failure may affect shared behavior
- `execution_horizon`: usually short for the diagnostic slice, even if the larger effort is broader

Common signals include:
- a regression is visible,
- tests or outputs disagree with expectation,
- failure can be observed but not yet explained,
- the next useful work is to reproduce, isolate, and narrow rather than patch.

## Primary working posture

When operating as `debug_investigator`, the agent should:

- reproduce the issue as directly as possible,
- identify the expected behavior boundary,
- isolate the first place where actual behavior diverges,
- reduce noise and irrelevant variation,
- compare candidate causes against observed evidence,
- avoid speculative fixing before the failure surface is understood,
- keep the task tightly focused on diagnosis rather than adjacent cleanup,
- record findings in a way that makes rerouting to the next slice straightforward.

The posture is disciplined fault isolation, not broad experimentation and not code-first fixing.

## Primary outputs

Typical outputs of `debug_investigator` include:

- a reproducible failing case,
- a narrowed failure surface,
- the first failing stage, boundary, or transformation,
- a root-cause hypothesis with supporting evidence,
- a confirmed cause,
- a recommended bounded fix slice,
- a recommendation to reroute into `contract_builder` if expected behavior is unclear,
- a decision that the issue belongs elsewhere in the system than initially assumed.

A successful `debug_investigator` slice usually leaves the next task much narrower than the original failure report.

## Typical next-step patterns

Good `next_step` patterns in this mode include:

- `Reproduce the regression using the stored fixture and isolate the first normalization stage where structure is lost.`
- `Compare baseline and failing outputs to identify the earliest divergent field.`
- `Instrument the transformation pipeline and capture the first step where parent/child relationships collapse.`
- `Reduce the failing input to the smallest reproducible nested-list case.`
- `Check whether the observed failure comes from contract ambiguity or from a local implementation regression.`

Weak `next_step` patterns in this mode include:

- `fix bug`
- `keep debugging`
- `work on parser`
- `continue`

## Allowed autonomy pattern

`debug_investigator` can usually proceed autonomously while:

- reproducing the failure,
- isolating the failure surface,
- comparing expected and actual outputs,
- instrumenting or inspecting the relevant path,
- testing local causal hypotheses,
- tightening the task boundary as evidence accumulates.

It should usually slow down or stop when:

- the cause is already sufficiently clear and the real work is now implementation,
- expected behavior itself turns out to be underdefined,
- the issue crosses into a review boundary, approval boundary, or other non-baseline control boundary,
- broader migration or rollout concerns become dominant,
- the main remaining work is evidence generation after a change rather than diagnosis.

This mode should not try to absorb the fix, the contract rewrite, and the evaluation pass into the same slice unless the boundaries remain genuinely narrow.

## Typical validation style

Validation in this mode is diagnosis-oriented.

Typical forms include:
- reliable reproduction,
- comparison of expected versus actual output,
- minimal failing cases,
- confirmation that the suspected cause explains the observed failure,
- confirmation that unrelated candidate causes have been ruled out,
- evidence that the issue has been localized enough to support the next slice.

A `debug_investigator` slice is often considered good enough when:
- the first failing point is identified,
- the likely cause is strong enough to justify a bounded fix or contract clarification,
- the next task no longer needs open-ended diagnosis.

If the work shifts from diagnosis to acceptance or readiness evidence, rerouting to `quality_evaluator` may be more appropriate.

## Common reroute triggers

Reroute away from `debug_investigator` when the dominant work changes.

Common reroute triggers include:

### Reroute to `routine_implementer`

When:
- the root cause is sufficiently isolated,
- the corrective change is bounded,
- the next useful step is to implement the fix.

### Reroute to `contract_builder`

When:
- the investigation shows that expected behavior or acceptance is underspecified,
- the apparent bug is really a missing or ambiguous contract,
- downstream work needs clarified rules before any fix can be called correct.

### Reroute to `quality_evaluator`

When:
- the fix or candidate change exists,
- the dominant next activity is evaluation, comparison, or acceptance assessment.

### Reroute to `research_scout`

When:
- the supposed debugging task is actually an open landscape problem with no stable failure boundary,
- the system needs broader discovery before diagnosis can even be meaningful.

### Reroute to `migration_operator`

When:
- the issue is primarily caused by staged transition behavior, compatibility boundaries, or rollout mechanics rather than ordinary local failure.

## Common next modes

Typical next modes after `debug_investigator` are:
- `routine_implementer`
- `contract_builder`
- sometimes `quality_evaluator`
- sometimes `migration_operator`

A common pattern is:
- failure reported -> `debug_investigator`
- cause isolated -> `routine_implementer`
- fix delivered -> `quality_evaluator` or `complete`

## Typical risks / failure modes

Common failure modes in `debug_investigator` include:

### 1. Premature fixing

The agent starts applying changes before the failure surface is understood.

### 2. Endless diagnosis

The task stays in investigation mode even after the problem is narrow enough for the next slice.

### 3. Scope drift into cleanup

The debugging task expands into general cleanup, refactor, or redesign unrelated to the diagnosed cause.

### 4. Mistaking ambiguity for defect

The observed issue looks like a bug, but the real problem is that expected behavior was never made explicit.

### 5. Weak reproduction

The investigation relies on vague symptoms rather than a reproducible failure boundary.

### 6. Hidden state drift

The task has really become `contract_builder` or `routine_implementer`, but the mode is left stale as `debug_investigator`.

## Good operating heuristics

Useful heuristics in this mode:

- prefer the smallest reliable reproduction over a large noisy scenario,
- identify the first failing boundary, not just the last visible symptom,
- compare actual behavior to explicit expected behavior whenever possible,
- distinguish "cause unknown" from "behavior undefined",
- record why the current hypothesis is plausible and what evidence rules alternatives out,
- stop diagnosing once the next slice becomes clear,
- keep the task card updated so another agent can continue without replaying the entire investigation.

## Relationship to Layer C and Layer D

### Relationship to Layer C

`debug_investigator` may run inside a `feature_cell` when the diagnostic slice is one bounded step inside a larger workstream.

It may also run under one or more `control_profile` records when diagnostic findings must cross an explicit review boundary, approval boundary, or other non-baseline control boundary before a risky fix proceeds. Presets such as `reviewed`, `change_controlled`, or `high_assurance` may be relevant when the failure touches a higher-risk boundary.

These Layer C constructs wrap or constrain the work. They do not define the current mode.

### Relationship to Layer D

A `debug_investigator` task is often:
- `active` while diagnosis is in progress,
- sometimes `checkpoint` when findings should be reviewed before a fix,
- sometimes `blocked` if reproduction or access prerequisites are missing,
- sometimes `complete` if the slice was only to isolate and document the cause.

The mode can remain `debug_investigator` while the Layer D lifecycle state changes.

## Example task shapes

Typical tasks that fit `debug_investigator` well:

- investigate a parser regression introduced by a refactor,
- isolate why a pipeline stage drops required fields,
- determine why outputs diverge from a previously passing baseline,
- narrow a failing nested-structure transformation to the first broken pass,
- confirm whether a broken behavior is local or caused upstream.

## Practical checklist

Use this checklist to validate whether `debug_investigator` is the right mode:

- Is there a concrete failing or incorrect behavior to diagnose?
- Is the cause not yet sufficiently established?
- Is the main work reproduction and isolation rather than implementation?
- Would a bounded fix be premature right now?
- Does exactly one diagnosis-focused posture clearly dominate?

If yes, `debug_investigator` is probably the right mode.

## Short operational summary

Use `debug_investigator` when the current slice should isolate the cause of a concrete failure before any bounded fix or contract rewrite proceeds.

The hallmark of this mode is not generic troubleshooting. It is disciplined narrowing of the failure surface until the next slice becomes an implementable fix, a clarified contract, or another explicitly justified mode.
