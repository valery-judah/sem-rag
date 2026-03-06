

# Quality Evaluator

## Purpose

`quality_evaluator` is the Layer B operating mode for generating, interpreting, or comparing evidence about correctness, quality, readiness, or acceptance when ordinary implementation alone is not enough.

Use this mode when the dominant work is not defining the contract and not directly implementing the change, but assessing whether the current result is good enough, correct enough, stable enough, or ready enough to justify the next move.

This mode is appropriate when evidence becomes the primary work product.

## Core question

When operating in `quality_evaluator`, the central question is:

> What evidence is needed, and what does that evidence justify, reject, or leave unresolved?

The target is not generic testing in the abstract. The target is a decision-useful quality judgment grounded in explicit evidence.

## When to use

Use `quality_evaluator` when one or more of the following are true:

- the current slice is primarily about validation, evaluation, readiness checking, or comparison,
- the next move depends on evidence rather than more design or more implementation,
- a candidate result exists and now needs assessment,
- the task requires benchmark-style comparison across variants, baselines, or scenarios,
- acceptance is non-trivial and must be supported by explicit findings,
- the slice should produce an evaluation summary, findings packet, or readiness recommendation,
- the main work is confirming whether a fix, feature, migration step, or contract is good enough to proceed.

This mode is often the right follow-on from `routine_implementer`, `migration_operator`, or a contract review that requests more evidence.

## When not to use

Do not use `quality_evaluator` when:

- the dominant work is still defining what should be built or accepted, in which case `contract_builder` is usually better,
- the dominant work is a bounded implementation change, in which case `routine_implementer` is usually better,
- the dominant work is diagnosis of a failure whose cause is not yet known, in which case `debug_investigator` is usually better,
- the dominant work is open-ended discovery or option mapping rather than evidence against an explicit question, in which case `research_scout` is usually better,
- the dominant work is measurable improvement work where the agent is still actively making tuning moves, in which case `optimization_tuner` is usually better,
- the slice is primarily about safe staged transition mechanics rather than assessing resulting evidence, in which case `migration_operator` is usually better.

Do not use this mode as a catch-all synonym for “tests exist.” Use it when evidence generation or interpretation is the dominant thing that should happen now.

## Typical Layer A signals

`quality_evaluator` is often a good fit when Layer A looks something like this:

- `validation_burden`: high
- `specification_maturity`: medium-to-high or high enough that evaluation questions can be framed explicitly
- `problem_uncertainty`: often lower about what should be checked, but still uncertain about whether the current result is sufficient
- `dependency_complexity`: variable, often medium or high if evidence must cover multiple interactions
- `blast_radius`: often medium or high when readiness judgment matters operationally
- `execution_horizon`: short-to-medium for the current evaluation slice

Common signals include:
- acceptance depends on evidence rather than assertion,
- the candidate result exists but is not yet trusted,
- comparison across scenarios or baselines matters,
- the output should be a findings-based recommendation rather than a code artifact.

## Primary working posture

When operating as `quality_evaluator`, the agent should:

- make the evaluation question explicit,
- define what evidence is relevant to the current slice,
- collect or interpret the smallest useful evidence set that supports a decision,
- compare actual outcomes to explicit expectations, baselines, or alternatives,
- record findings clearly enough that another agent or reviewer can act on them,
- avoid drifting into broad contract work or code-first execution unless the evidence clearly requires rerouting,
- keep the evaluation scoped to the current slice and stated acceptance basis.

The posture is evidence-oriented judgment, not general exploration and not delivery-first implementation.

## Primary outputs

Typical outputs of `quality_evaluator` include:

- evaluation summaries,
- findings packets,
- benchmark comparisons,
- readiness notes,
- acceptance recommendations,
- scenario-by-scenario observations,
- evidence bundles linked to a checkpoint or closure decision,
- explicit statement of whether the result is sufficient, insufficient, or inconclusive.

A successful `quality_evaluator` slice usually leaves the next move clearer than before: proceed, modify, investigate further, escalate, or stop.

## Typical next-step patterns

Good `next_step` patterns in this mode include:

- `Run the defined acceptance scenarios against baseline and candidate outputs, then summarize pass/fail and notable deltas.`
- `Compare the reviewed schema against three representative document cases and record any invariant violations.`
- `Assess whether the migration-readiness evidence supports crossing the next stage gate.`
- `Evaluate the regression fix against the stored failing fixture and adjacent non-regression cases.`
- `Prepare a findings packet stating whether the current segmentation output is good enough for phase-1 acceptance.`

Weak `next_step` patterns in this mode include:

- `test stuff`
- `check quality`
- `do validation`
- `continue`

## Allowed autonomy pattern

`quality_evaluator` can usually proceed autonomously while:

- running defined checks,
- gathering explicit evaluation evidence,
- comparing candidates to baselines,
- summarizing findings against acceptance conditions,
- determining whether the evidence is sufficient or incomplete,
- drafting findings packets or readiness notes.

It should usually slow down or stop when:

- the evaluation question is not yet explicit enough and the real problem is contract definition,
- the result clearly implies a new implementation or debugging slice should be created,
- a review or approval boundary is reached where findings must be interpreted by another actor,
- optimization work becomes the main activity instead of evaluation,
- the slice begins to sprawl into redesign rather than evidence-based judgment.

This mode often works closely with `review_gatekeeper`, but the overlay remains Layer C, not Layer B.

## Typical validation style

Validation in this mode is the primary content of the slice itself.

Typical forms include:
- acceptance scenario evaluation,
- before/after comparison,
- benchmark or metric comparison,
- readiness checking,
- conformance checking against explicit contract rules,
- findings synthesis across representative cases,
- recommendation based on gathered evidence.

A `quality_evaluator` slice is often considered good enough when:
- the relevant evidence has been gathered or interpreted,
- the findings clearly support a next action,
- important gaps or inconclusive areas are made explicit,
- another agent or reviewer could act without rerunning the whole evaluation blindly.

If the dominant work shifts from evaluation to making performance or quality improvements, rerouting to `optimization_tuner` may be more appropriate.

## Common reroute triggers

Reroute away from `quality_evaluator` when the dominant work changes.

Common reroute triggers include:

### Reroute to `routine_implementer`

When:
- the evidence clearly supports a bounded implementation change,
- the current evaluation slice has done enough and the next useful work is direct delivery.

### Reroute to `debug_investigator`

When:
- evaluation reveals unexplained failing behavior that now requires causal isolation,
- the main work becomes diagnosis rather than further evidence accumulation.

### Reroute to `contract_builder`

When:
- evaluation cannot proceed meaningfully because expected behavior or acceptance criteria are underdefined,
- the real next need is to clarify the contract before more evaluation occurs.

### Reroute to `optimization_tuner`

When:
- the evidence is sufficient and the dominant next activity becomes iterative improvement against a metric.

### Reroute to `migration_operator`

When:
- the evidence shows that the main next work is a staged rollout, rollback-aware move, or transition step rather than further evaluation.

## Common next modes

Typical next modes after `quality_evaluator` are:
- `routine_implementer`
- `debug_investigator`
- `contract_builder`
- `optimization_tuner`
- sometimes `migration_operator`

A common pattern is:
- implementation complete -> `quality_evaluator`
- evidence gathered -> `complete`, `checkpoint`, or reroute to the next corrective slice

## Typical risks / failure modes

Common failure modes in `quality_evaluator` include:

### 1. Testing without a question

Evidence is gathered, but the evaluation question is too vague to support a decision.

### 2. Metric theater

Many numbers are produced, but they do not map cleanly to the actual acceptance or readiness decision.

### 3. Hidden contract ambiguity

The task looks like evaluation, but the real blocker is undefined expected behavior.

### 4. Endless evidence gathering

The slice keeps accumulating more cases without improving the decision quality materially.

### 5. Premature readiness claims

The task concludes that something is “good” or “ready” without enough explicit evidence.

### 6. Stale mode after diagnosis becomes dominant

The task keeps the evaluation label even after the real work becomes debugging or contract clarification.

## Good operating heuristics

Useful heuristics in this mode:

- make the evaluation question explicit before collecting evidence,
- gather the smallest evidence set that can support the next decision,
- compare against something explicit: baseline, contract, expectation, scenario set, or threshold,
- state what the evidence does and does not justify,
- prefer representative cases over large unfocused dumps,
- record inconclusive areas explicitly instead of hiding them,
- if the findings imply a different dominant activity, reroute rather than stretching evaluation mode too far.

## Relationship to Layer C and Layer D

### Relationship to Layer C

`quality_evaluator` commonly interacts with:
- `review_gatekeeper` when findings should pause for interpretation or acceptance review,
- `feature_cell` when evaluation is one child slice in a larger workstream,
- sometimes `governance_escalation` when readiness evidence is part of a higher-risk decision boundary.

But these are overlays/containers, not modes.

### Relationship to Layer D

A `quality_evaluator` task is often:
- `validating` while evidence generation or interpretation is dominant,
- sometimes `checkpoint` when findings are ready for review,
- sometimes `active` if the task is evaluating but not formally marked as a validating state,
- sometimes `complete` when the evaluation slice has produced its full decision-ready output,
- sometimes `blocked` if required evidence inputs or scenarios are missing.

The mode can remain `quality_evaluator` while the lifecycle state changes.

## Example task shapes

Typical tasks that fit `quality_evaluator` well:

- compare candidate and baseline parser outputs against acceptance scenarios,
- assess whether a regression fix actually closes the issue without new breakage,
- prepare a readiness summary for the next migration stage,
- evaluate whether phase-1 segmentation results meet the reviewed contract,
- generate a findings packet for review after implementation is complete.

## Practical checklist

Use this checklist to validate whether `quality_evaluator` is the right mode:

- Is the main work evidence generation or interpretation?
- Is there an explicit evaluation or acceptance question?
- Does the next decision depend more on findings than on more design or code?
- Can the slice produce a decision-useful output such as a findings summary or readiness recommendation?
- Does exactly one evidence-oriented posture clearly dominate?

If yes, `quality_evaluator` is probably the right mode.

## Short operational summary

Use `quality_evaluator` when the current slice should determine whether a result is good enough, correct enough, or ready enough through explicit evidence.

The hallmark of this mode is not generic testing. It is production of decision-useful findings that justify continuation, correction, escalation, or closure.