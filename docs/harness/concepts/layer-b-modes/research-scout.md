

# Research Scout

## Purpose

`research_scout` is the Layer B operating mode for reducing uncertainty through targeted discovery, mapping, and evidence gathering when the current slice is still exploratory.

Use this mode when the dominant work is not yet to implement, not yet to define the final contract, and not yet to diagnose a concrete failure, but to understand the relevant landscape well enough to make the next slice narrower and more actionable.

This mode is appropriate when the system needs orientation before stronger commitment.

## Core question

When operating in `research_scout`, the central question is:

> What do we need to learn now so the next slice can stop being broad exploration and become a narrower executable task?

The target is not endless research. The target is uncertainty reduction that improves routing.

## When to use

Use `research_scout` when one or more of the following are true:

- the problem or solution space is still not framed tightly enough for contract definition or implementation,
- multiple plausible directions exist and the task must compare or map them,
- key constraints, dependencies, or assumptions are still unclear,
- relevant knowledge is scattered and the current useful work is to gather and structure it,
- the slice should produce findings, options, framing, or recommendations rather than code,
- the effort needs an initial problem decomposition before more committed work begins,
- the current question is exploratory but still bounded enough to avoid generic brainstorming.

This mode is often the right first response to broad new requests, partially specified initiatives, and early-stage design uncertainty.

## When not to use

Do not use `research_scout` when:

- the dominant work is already defining a concrete contract, schema, or acceptance boundary, in which case `contract_builder` is usually better,
- the expected outcome is already sufficiently clear and the current slice should be implemented directly, in which case `routine_implementer` is usually better,
- the task is diagnosing a concrete failure with a reproducible symptom, in which case `debug_investigator` is usually better,
- the main work is gathering evaluation evidence against an already explicit question, in which case `quality_evaluator` is usually better,
- the slice is primarily about a staged transition, rollout, or migration boundary, in which case `migration_operator` is usually better,
- the task is mainly behavior-preserving structural work, in which case `refactor_surgeon` is usually better.

Do not let this mode become a polite label for indecision. It should produce bounded findings that improve the next route.

## Typical Layer A signals

`research_scout` is often a good fit when Layer A looks something like this:

- `problem_uncertainty`: high
- `specification_maturity`: low or low-to-medium
- `knowledge_locality`: dispersed, mixed, or not yet well understood
- `dependency_complexity`: variable, often unclear at the start
- `validation_burden`: still secondary to framing, though it may become important later
- `execution_horizon`: short for the current exploration slice, even if the broader effort is larger

Common signals include:
- the user request is broad or underconstrained,
- the next step depends on understanding options or constraints,
- the task needs mapping before narrowing,
- there is not yet one stable agreement surface to define.

## Primary working posture

When operating as `research_scout`, the agent should:

- narrow the exploratory question enough to keep the slice bounded,
- gather only the information needed to improve the next decision,
- identify constraints, options, dependencies, and open questions,
- distinguish established facts from plausible assumptions,
- organize findings into a form that supports rerouting,
- avoid drifting into contract drafting, implementation, or debugging unless the evidence clearly justifies rerouting,
- stop once the next slice becomes meaningfully narrower.

The posture is disciplined exploration, not open-ended ideation and not premature commitment.

## Primary outputs

Typical outputs of `research_scout` include:

- findings summaries,
- option maps,
- constraint lists,
- dependency maps,
- problem framing notes,
- comparative notes across plausible directions,
- explicit unanswered questions,
- recommendations for the next slice,
- proposal for whether the next mode should be `contract_builder`, `routine_implementer`, or something else.

A successful `research_scout` slice usually leaves the task easier to classify than before.

## Typical next-step patterns

Good `next_step` patterns in this mode include:

- `Map the main constraints and unknowns for phase-1 hierarchical segmentation before defining the contract slice.`
- `Compare the plausible parser-first and schema-first approaches and note which assumptions block direct implementation.`
- `Identify the minimum set of upstream and downstream dependencies that shape the current feature boundary.`
- `Collect the existing docs, code paths, and prior notes relevant to the requested migration and summarize open decision points.`
- `Reduce the broad feature request into two or three plausible next slices and recommend which should become the first contract task.`

Weak `next_step` patterns in this mode include:

- `research more`
- `think about the problem`
- `explore ideas`
- `continue`

## Allowed autonomy pattern

`research_scout` can usually proceed autonomously while:

- gathering and structuring relevant context,
- comparing plausible directions,
- clarifying dependencies and assumptions,
- narrowing a broad request into better-shaped slices,
- producing a bounded findings summary or recommendation.

It should usually slow down or stop when:

- the findings already support a specific contract or implementation slice,
- the exploration is no longer reducing uncertainty materially,
- a real design or review choice should be surfaced explicitly,
- the work begins to sprawl into speculative future architecture rather than current slice framing,
- evidence generation against an explicit acceptance question becomes the dominant work.

This mode should hand off cleanly once exploration has done its job.

## Typical validation style

Validation in this mode is usually about usefulness of framing rather than pass/fail behavior.

Typical forms include:
- whether the findings reduced uncertainty materially,
- whether the main options and constraints are explicit,
- whether assumptions and unknowns are separated clearly,
- whether the output makes the next slice narrower,
- whether another agent could now route the task more confidently.

A `research_scout` slice is often considered good enough when:
- the exploratory question is answered well enough for rerouting,
- the next mode is clearer than before,
- the remaining uncertainty is explicit rather than hidden.

## Common reroute triggers

Reroute away from `research_scout` when the dominant work changes.

Common reroute triggers include:

### Reroute to `contract_builder`

When:
- the landscape is now understood well enough to define a boundary, schema, interface, or acceptance contract,
- the next useful work is explicit agreement formation rather than more exploration.

### Reroute to `routine_implementer`

When:
- exploration shows that the path is already clear enough for direct bounded execution,
- the task no longer needs substantial contract shaping first.

### Reroute to `debug_investigator`

When:
- the broad question collapses into diagnosis of a concrete failing behavior,
- reproduction and causal isolation become dominant.

### Reroute to `quality_evaluator`

When:
- the current useful work is no longer mapping options but generating evidence against an explicit evaluation question.

### Reroute to `migration_operator`

When:
- the exploration clarifies that the dominant challenge is staged transition mechanics rather than general discovery.

## Common next modes

Typical next modes after `research_scout` are:
- `contract_builder`
- `routine_implementer`
- sometimes `debug_investigator`
- sometimes `migration_operator`
- sometimes `quality_evaluator`

The most common progression is:
- broad request arrives -> `research_scout`
- uncertainty narrows -> `contract_builder`
- contract becomes executable -> `routine_implementer`

## Typical risks / failure modes

Common failure modes in `research_scout` include:

### 1. Endless exploration

The task remains exploratory after the next slice is already obvious.

### 2. Scope sprawl

The agent starts mapping the whole domain instead of the bounded question relevant to the current slice.

### 3. Premature architecture invention

The research output jumps too quickly into a large solution design without enough grounding.

### 4. Weak findings

The output contains many observations but does not improve routing or next-step quality.

### 5. Hidden contract work

The task has already become explicit agreement formation, but the mode is left stale as exploration.

### 6. Confusing uncertainty with lack of progress

The agent keeps gathering more context instead of deciding that the current uncertainty is already low enough to reroute.

## Good operating heuristics

Useful heuristics in this mode:

- phrase the research question narrowly before gathering context,
- collect only context that can change the next route,
- separate facts, assumptions, and open questions explicitly,
- prefer option narrowing over option proliferation,
- stop once the next task can be stated more concretely than before,
- ask whether the output would let another agent choose a better mode with less hesitation,
- if yes, the exploration slice may be complete.

## Relationship to Layer C and Layer D

### Relationship to Layer C

`research_scout` may run inside a `feature_cell` when the exploratory slice is part of a broader multi-slice workstream.

It may also run under one or more `control_profile` records when findings must cross an explicit review boundary, approval boundary, or other non-baseline control boundary before the next slice is chosen. In that context, presets such as `reviewed`, `change_controlled`, or `high_assurance` may be relevant.

These Layer C constructs wrap or constrain the work. They do not define the current mode.

### Relationship to Layer D

A `research_scout` task is often:
- `active` while bounded exploration is underway,
- sometimes `checkpoint` when findings are ready for review,
- sometimes `blocked` if required sources or context are unavailable,
- sometimes `complete` when the current exploratory question has been answered and the next route is clear.

The mode can remain `research_scout` while the Layer D lifecycle state changes.

## Example task shapes

Typical tasks that fit `research_scout` well:

- narrow a broad feature request into an initial contract slice,
- compare possible starting points for a new capability before contract formation,
- identify the main constraints and open questions around a proposed migration,
- collect the code, docs, and decisions relevant to a still-vague initiative and summarize the actual decision surface,
- determine whether a request is really a contract problem, implementation problem, or debugging problem.

## Practical checklist

Use this checklist to validate whether `research_scout` is the right mode:

- Is the main work still reducing uncertainty rather than executing or defining a final agreement?
- Is the current question exploratory but still bounded?
- Would better findings materially improve the next route?
- Is the slice likely to end by narrowing the next task, not by delivering the final artifact itself?
- Does exactly one exploration-focused posture clearly dominate?

If yes, `research_scout` is probably the right mode.

## Short operational summary

Use `research_scout` when the current slice should reduce uncertainty enough to produce a narrower, better-routed next task.

The hallmark of this mode is not generic research. It is bounded exploration that improves the next operating decision.
