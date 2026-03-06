

# Optimization Tuner

## Purpose

`optimization_tuner` is the Layer B operating mode for improving an existing system against explicit measurable technical objectives such as latency, throughput, cost, resource usage, relevance, or other tunable performance targets.

Use this mode when the system already works in a baseline sense and the dominant work is no longer basic implementation or broad diagnosis, but making and comparing improvement moves against a defined target metric or performance profile.

This mode is appropriate when the core task is not merely to measure quality, but to change the system in a disciplined way to improve a measurable outcome.

## Core question

When operating in `optimization_tuner`, the central question is:

> What change is most likely to improve the target metric without creating unacceptable tradeoffs elsewhere?

The target is not generic speedup or vague improvement. The target is controlled optimization against explicit criteria.

## When to use

Use `optimization_tuner` when one or more of the following are true:

- the system already has a functioning baseline,
- the dominant goal is to improve latency, throughput, memory, cost, token usage, ranking quality, retrieval efficiency, or another measurable technical property,
- the work depends on baseline comparison and measured deltas,
- there is at least one plausible improvement lever to test,
- the slice is about changing and comparing candidate implementations rather than only assessing them,
- tradeoffs between target and non-target metrics matter,
- the next useful output is an optimization move plus evidence of its effect.

This mode is often the right posture for tuning after a baseline implementation exists and the main question becomes whether a specific change is worth adopting.

## When not to use

Do not use `optimization_tuner` when:

- the dominant work is still broad discovery of the problem or solution space, in which case `research_scout` is usually better,
- the main need is defining the contract, target metric, acceptance threshold, or evaluation question, in which case `contract_builder` is usually better,
- the current slice is a normal bounded implementation step rather than a measured improvement loop, in which case `routine_implementer` is usually better,
- the system is failing in an unexplained way and the main need is diagnosis, in which case `debug_investigator` is usually better,
- the dominant work is only evidence gathering or comparison across candidates without an active tuning move, in which case `quality_evaluator` is usually better,
- the slice is mostly about staged transition or safe rollout rather than metric improvement, in which case `migration_operator` is usually better,
- the slice is mostly about behavior-preserving structural cleanup, in which case `refactor_surgeon` is usually better.

Do not use this mode as a label for any task involving benchmarks. Use it when optimization itself is the current dominant activity.

## Typical Layer A signals

`optimization_tuner` is often a good fit when Layer A looks something like this:

- `problem_uncertainty`: low-to-medium or medium, usually around which lever is best rather than what the system should do
- `specification_maturity`: medium-to-high or high enough that improvement targets are already meaningful
- `dependency_complexity`: medium or high depending on how many subsystems influence the target metric
- `validation_burden`: medium or high because comparison discipline is required
- `blast_radius`: variable, often medium if tuning affects shared paths
- `execution_horizon`: short-to-medium for the current experiment or tuning slice

Common signals include:
- there is a known baseline,
- a target metric or performance concern is explicit,
- one or more tuning levers are plausible,
- the current useful output is a changed candidate plus measured comparison.

## Primary working posture

When operating as `optimization_tuner`, the agent should:

- make the target metric and baseline explicit,
- identify the candidate optimization lever for the current slice,
- change one bounded part of the system at a time when practical,
- compare deltas against the baseline rather than reasoning from intuition alone,
- track non-target regressions that could invalidate the optimization,
- keep the slice narrow enough that the experiment outcome is interpretable,
- avoid overfitting to one benchmark without checking obvious collateral effects,
- stop and reroute if the work is no longer really about measured improvement.

The posture is experiment-and-improve, not generic implementation and not passive evaluation-only work.

## Primary outputs

Typical outputs of `optimization_tuner` include:

- baseline-versus-candidate comparisons,
- targeted performance or cost improvements,
- experiment notes,
- tuning change proposals,
- tradeoff summaries,
- recommendations about whether to adopt or reject a candidate optimization,
- explicit statement of measured gain, neutral result, or regression.

A successful `optimization_tuner` slice usually leaves the system with either a justified improvement or a justified rejection of a candidate change.

## Typical next-step patterns

Good `next_step` patterns in this mode include:

- `Implement the candidate batching strategy and compare end-to-end latency against the current baseline across the defined scenario set.`
- `Apply the retrieval cache change and record cost, latency, and hit-rate deltas relative to the baseline run.`
- `Tune the chunk-selection threshold and compare relevance and token-cost tradeoffs against the current configuration.`
- `Replace the current serialization path with the proposed fast path and measure throughput plus correctness-sensitive regressions.`
- `Test the smaller embedding configuration against the baseline and record whether cost savings preserve acceptable retrieval quality.`

Weak `next_step` patterns in this mode include:

- `optimize performance`
- `run benchmarks`
- `improve latency`
- `continue tuning`

## Allowed autonomy pattern

`optimization_tuner` can usually proceed autonomously while:

- defining a bounded tuning move,
- implementing the candidate change,
- running the agreed comparison against baseline,
- checking for obvious collateral regressions,
- summarizing whether the candidate is worth keeping,
- iterating when the next experiment remains within the same explicit objective.

It should usually slow down or stop when:

- the target metric or threshold is not actually explicit,
- the main work becomes evaluation design rather than tuning,
- the candidate result reveals unexplained failure that needs diagnosis,
- the work crosses into higher-risk rollout or migration territory,
- tradeoffs become policy-like rather than technical and require review,
- the slice starts changing too many variables at once to remain interpretable.

This mode benefits from discipline around one bounded change per evaluation loop where practical.

## Typical validation style

Validation in this mode is comparison-oriented and metric-driven.

Typical forms include:
- baseline-versus-candidate comparison,
- benchmark or load comparison,
- cost/performance tradeoff analysis,
- relevance or quality comparison when those are part of the optimization target,
- regression checks on adjacent non-target dimensions,
- threshold-based adoption criteria.

An `optimization_tuner` slice is often considered good enough when:
- the target metric delta is clear,
- important non-target regressions are visible,
- the adoption decision is evidence-based,
- another agent could understand whether the candidate should be kept, revised, or rejected.

If the slice becomes primarily about evaluating evidence rather than making optimization moves, rerouting to `quality_evaluator` may be more appropriate.

## Common reroute triggers

Reroute away from `optimization_tuner` when the dominant work changes.

Common reroute triggers include:

### Reroute to `quality_evaluator`

When:
- the current useful work is now interpreting results, comparing scenarios, or producing a findings packet rather than making the next tuning move,
- the optimization question has become a broader evidence or acceptance question.

### Reroute to `routine_implementer`

When:
- the best improvement path is now obvious and the remaining work is just bounded implementation rather than tuning experimentation,
- the chosen optimization has been accepted and needs straightforward integration.

### Reroute to `contract_builder`

When:
- the target metric, threshold, or optimization objective is underdefined,
- the system needs explicit acceptance or tradeoff rules before more tuning is meaningful.

### Reroute to `debug_investigator`

When:
- the tuning change reveals unexplained regressions or failures and diagnosis becomes dominant.

### Reroute to `migration_operator`

When:
- the optimization requires a staged rollout, compatibility management, or other transition mechanics that dominate the current slice.

## Common next modes

Typical next modes after `optimization_tuner` are:
- `quality_evaluator`
- `routine_implementer`
- sometimes `contract_builder`
- sometimes `debug_investigator`
- sometimes `migration_operator`

A common pattern is:
- baseline exists -> `optimization_tuner`
- candidate compared -> `quality_evaluator` or bounded adoption work
- accepted change integrated -> `routine_implementer` or `complete`

## Typical risks / failure modes

Common failure modes in `optimization_tuner` include:

### 1. Optimizing the wrong metric

The slice improves something measurable that does not actually matter to the real objective.

### 2. Unstable baseline

The comparison is performed against a noisy or shifting baseline, making conclusions weak.

### 3. Hidden collateral regression

The target metric improves, but correctness, reliability, relevance, or maintainability degrades materially.

### 4. Too many changed variables

The candidate differs in too many ways from baseline to attribute the result cleanly.

### 5. Metric overfitting

The optimization is tuned to one narrow benchmark while harming broader real-world performance.

### 6. Stale mode after evaluation dominates

The task remains labeled as tuning even after the work has become result interpretation or acceptance judgment.

## Good operating heuristics

Useful heuristics in this mode:

- make the target metric and baseline explicit before changing the system,
- prefer bounded tuning moves over broad multi-variable changes,
- record both gains and regressions, not just the target improvement,
- keep at least one non-target sanity check close to the slice,
- reject “improvements” that cannot be attributed cleanly,
- ask whether the current work is still optimizing or has become evaluation/reporting,
- if the latter, reroute rather than stretching tuning mode too far.

## Relationship to Layer C and Layer D

### Relationship to Layer C

`optimization_tuner` may interact with:
- `review_gatekeeper` when a tuning result should pause for review before adoption,
- `feature_cell` when the optimization program spans multiple coordinated slices,
- sometimes `governance_escalation` if the optimization affects a higher-risk production path.

But these are overlays/containers, not operating modes.

### Relationship to Layer D

An `optimization_tuner` task is often:
- `active` while the tuning change and comparison loop are underway,
- sometimes `validating` when benchmark execution or result checking becomes dominant,
- sometimes `checkpoint` when findings or tradeoffs should pause for review,
- sometimes `complete` when the bounded tuning slice has produced a clear adoption or rejection decision,
- sometimes `blocked` if benchmark infrastructure, representative inputs, or baseline data are missing.

The mode can remain `optimization_tuner` while the lifecycle state changes.

## Example task shapes

Typical tasks that fit `optimization_tuner` well:

- reduce query latency by testing a bounded batching or caching strategy,
- tune retrieval thresholds against explicit relevance and token-cost tradeoffs,
- compare candidate embedding or ranking configurations against a baseline,
- reduce parsing cost or memory footprint while checking for correctness-sensitive regressions,
- optimize a critical pipeline stage against throughput or latency targets.

## Practical checklist

Use this checklist to validate whether `optimization_tuner` is the right mode:

- Is there a working baseline already?
- Is the main work about improving a measurable technical property?
- Is there an explicit target metric or optimization objective?
- Will the slice change and compare a bounded candidate rather than only evaluate results?
- Does exactly one improvement-oriented posture clearly dominate?

If yes, `optimization_tuner` is probably the right mode.

## Short operational summary

Use `optimization_tuner` when the current slice should make and compare bounded improvement moves against an explicit measurable objective.

The hallmark of this mode is not generic benchmarking. It is disciplined tuning with baseline comparison, tradeoff awareness, and evidence-based adoption decisions.