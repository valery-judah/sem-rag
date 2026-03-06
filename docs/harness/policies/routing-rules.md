

# Routing Rules

## Purpose

This document defines the default routing policy from Layer A problem shape to one current Layer B operating mode.

Its purpose is to help an agent choose the dominant current posture for a task slice after intake and during rerouting. It is not a universal workflow specification, not a replacement for judgment, and not a license to blend multiple modes into one label.

The routing policy should stay small, legible, and easy to apply repeatedly.

## Scope

These rules apply to **task slices**, not to workstreams as a whole.

Use this policy when:
- creating a new task card during intake,
- rerouting a task during execution,
- repairing a stale or ambiguous task card,
- checking whether the current mode still matches the actual work.

Do not use this document to:
- derive Layer D state,
- choose Layer C overlays directly,
- classify whole initiatives instead of the current slice,
- create blended modes like `research + implementation`.

## Core routing principle

Pick **exactly one** current Layer B mode: the one that best describes the dominant posture required **now** for the current slice.

The correct question is:

> What is the most important kind of work this slice currently requires?

Not:
- what the whole initiative is about,
- what the work might become later,
- what secondary activity is also present,
- what role the agent prefers.

## Allowed Layer B modes

Use only the following current modes:
- `research_scout`
- `contract_builder`
- `routine_implementer`
- `refactor_surgeon`
- `debug_investigator`
- `migration_operator`
- `optimization_tuner`
- `quality_evaluator`

## Inputs to routing

Routing should use the current task slice and at least the required Layer A core:
- `intent`
- `problem_uncertainty`
- `dependency_complexity`
- `knowledge_locality`
- `specification_maturity`
- `validation_burden`
- `blast_radius`
- `execution_horizon`

Routing may also consider:
- current request wording,
- current next step,
- current failure mode,
- whether evidence generation is now dominant,
- whether the work is behavior-preserving or behavior-changing,
- whether the slice is part of a staged transition.

## Default routing table

### Route to `research_scout`

Use `research_scout` when the dominant work is understanding the problem space, solution space, or surrounding landscape before a concrete contract or implementation path exists.

Typical signs:
- problem is still poorly understood,
- multiple plausible directions exist,
- constraints need discovery,
- relevant knowledge is scattered or incomplete,
- the main output is findings, mapping, options, or clarified understanding.

Common Layer A profile:
- higher `problem_uncertainty`,
- lower `specification_maturity`,
- non-trivial `knowledge_locality` challenges.

Typical outputs:
- findings summary,
- options list,
- discovery notes,
- problem framing,
- recommendation for the next slice.

Do not use when the real work is already contract definition, debugging, or evaluation.

### Route to `contract_builder`

Use `contract_builder` when the dominant work is defining scope, interface, behavior, acceptance conditions, schema, API shape, or other executable agreement.

Typical signs:
- the problem is sufficiently framed to define a contract,
- implementation should not proceed until the interface or acceptance basis is clearer,
- the main output is a specification, RFC section, schema, API contract, or acceptance definition,
- disagreements are mainly about what should be built or accepted, not how code is failing.

Common Layer A profile:
- moderate `problem_uncertainty`,
- rising `specification_maturity`,
- meaningful `validation_burden` because acceptance must be defined.

Typical outputs:
- contract draft,
- schema definition,
- acceptance criteria,
- RFC section,
- implementation boundary.

Do not use when the contract is already clear and the real work is straightforward implementation.

### Route to `routine_implementer`

Use `routine_implementer` when the implementation path is clear enough that the dominant work is executing a bounded change.

Typical signs:
- acceptance target is sufficiently understood,
- code or artifact change is the main activity,
- no major unexplained failure or design ambiguity dominates,
- the slice is a normal implementation step rather than a structural preservation refactor.

Common Layer A profile:
- lower `problem_uncertainty`,
- higher `specification_maturity`,
- manageable `dependency_complexity`,
- bounded `execution_horizon`.

Typical outputs:
- implemented code change,
- updated docs,
- tests added or updated as part of delivery,
- completed bounded feature slice.

Do not use when the main issue is unexplained failure, undefined contract, migration sequencing, or optimization diagnosis.

### Route to `refactor_surgeon`

Use `refactor_surgeon` when the dominant work is structural change with behavior preservation.

Typical signs:
- the goal is reorganization, cleanup, decomposition, or type/model restructuring,
- the task should preserve external behavior,
- risk comes from unintended regressions introduced by structure change rather than new intended behavior,
- the main question is how to transform the structure safely.

Common Layer A profile:
- lower `problem_uncertainty`,
- moderate `dependency_complexity`,
- meaningful `blast_radius` if structure is widely used,
- moderate `validation_burden` to ensure preservation.

Typical outputs:
- refactored module or interface shape,
- extracted abstractions,
- reorganized code structure,
- preservation-focused test updates.

Do not use when the task is actually debugging or behavior-changing feature work.

### Route to `debug_investigator`

Use `debug_investigator` when behavior is wrong or failing and the dominant work is finding the cause.

Typical signs:
- observed output is incorrect,
- regression or failure exists,
- root cause is not established,
- reproduction, isolation, and cause analysis are the main work,
- implementation should wait until the failure is understood.

Common Layer A profile:
- elevated `problem_uncertainty`,
- variable `specification_maturity` but unclear causal path,
- potentially high `blast_radius` if failure is broad.

Typical outputs:
- reproduction case,
- narrowed failure surface,
- root-cause hypothesis or confirmed cause,
- recommendation for fix slice.

Do not use when the issue is primarily that desired behavior was never clearly specified.

### Route to `migration_operator`

Use `migration_operator` when the slice belongs to a staged transition, replacement, cutover, backfill, or rollout-sensitive move from one system/state to another.

Typical signs:
- work involves old-to-new movement,
- sequencing, reversibility, rollout, coexistence, or compatibility matters,
- the slice is one step in a staged migration or system transition,
- risk comes from transition mechanics rather than only local code changes.

Common Layer A profile:
- higher `dependency_complexity`,
- meaningful `blast_radius`,
- longer `execution_horizon`,
- strong sensitivity to coordination and validation.

Typical outputs:
- migration plan slice,
- adapter or compatibility change,
- staged rollout step,
- cutover checklist,
- rollback-aware execution step.

Do not use for ordinary implementation just because the task touches legacy code.

### Route to `optimization_tuner`

Use `optimization_tuner` when the dominant work is improving an existing system against measurable objectives such as latency, cost, quality, throughput, relevance, or efficiency.

Typical signs:
- the system already works in a baseline sense,
- the main question is how to improve a measurable property,
- comparison against baseline matters,
- tradeoffs and instrumentation are important.

Common Layer A profile:
- lower `problem_uncertainty` about the system’s purpose,
- meaningful `validation_burden`,
- moderate or high `dependency_complexity` depending on the system.

Typical outputs:
- tuning change,
- benchmark comparison,
- parameter or architecture adjustment,
- recommendation based on measured deltas.

Do not use when the dominant work is simply evaluation without a concrete optimization move yet.

### Route to `quality_evaluator`

Use `quality_evaluator` when the dominant work is generating, interpreting, or comparing evidence about correctness, quality, readiness, or acceptance.

Typical signs:
- evaluation, validation, benchmarking, acceptance checking, or evidence review is the main activity,
- the task is not primarily defining the contract or implementing the fix,
- the next move depends on generated evidence,
- comparison across scenarios, baselines, or candidate outputs matters.

Common Layer A profile:
- higher `validation_burden`,
- specification may be stable enough to evaluate,
- uncertainty may be localized to whether the result is good enough.

Typical outputs:
- evaluation summary,
- findings packet,
- benchmark comparison,
- readiness assessment,
- acceptance recommendation.

Do not use when the main work is still exploring what should be measured or specified.

## Priority rules for ambiguous cases

When two modes both seem plausible, use these disambiguation rules.

### `research_scout` vs `contract_builder`

Use `research_scout` if the work is still mainly discovering the shape of the problem or option space.

Use `contract_builder` if the work has narrowed enough that the main value is defining an explicit contract, interface, or acceptance target.

### `contract_builder` vs `routine_implementer`

Use `contract_builder` if unclear behavior, boundary, or acceptance would make implementation premature.

Use `routine_implementer` if the contract is already good enough and the main work is to execute the change.

### `routine_implementer` vs `debug_investigator`

Use `debug_investigator` if something is failing and cause is not established.

Use `routine_implementer` if the failure cause is already known and the current slice is the bounded fix.

### `routine_implementer` vs `refactor_surgeon`

Use `refactor_surgeon` if the goal is structural change with intended behavior preservation.

Use `routine_implementer` if the goal is new or changed behavior, even if some cleanup is included.

### `migration_operator` vs `routine_implementer`

Use `migration_operator` if staging, compatibility, rollout sequencing, rollback, or cutover mechanics are central.

Use `routine_implementer` if the task is just a normal implementation step inside a larger migration context but transition mechanics are not dominant in this slice.

### `optimization_tuner` vs `quality_evaluator`

Use `quality_evaluator` when the main work is evidence generation or assessment.

Use `optimization_tuner` when the main work is making and comparing improvement moves against a metric.

## Rerouting rules

Reroute when the actual work has changed shape enough that the current mode no longer describes the dominant posture.

Common reroutes:
- `research_scout -> contract_builder` when discovery narrows into explicit contract formation,
- `contract_builder -> routine_implementer` when the contract is sufficiently defined,
- `routine_implementer -> debug_investigator` when unexplained failure becomes dominant,
- `debug_investigator -> contract_builder` when the real issue is undefined expected behavior,
- `migration_operator -> quality_evaluator` when readiness evidence becomes the main work,
- `quality_evaluator -> routine_implementer` when findings now support a bounded implementation fix,
- `optimization_tuner -> quality_evaluator` when a measurement cycle dominates before the next tuning move.

When rerouting:
- update `current_mode`,
- update the mode rationale,
- update `next_step` to match the new posture,
- update Layer A if the problem shape materially changed,
- record the reroute in the work log.

## What routing must not do

Routing must not:
- select multiple current modes,
- encode Layer D state,
- decide workstream promotion by itself,
- replace human judgment when a slice is badly formed,
- hide the need to reslice.

If the slice is too broad for one mode to make sense, the correct action is usually to **reslice the task**, not invent a blended route.

## Quick routing checklist

Use this checklist when choosing or validating a mode.

- What is the current slice trying to accomplish now?
- What is the dominant kind of work required now?
- Is the problem still mainly discovery, contract definition, implementation, debugging, migration, tuning, or evaluation?
- Does exactly one mode clearly dominate?
- If not, is the slice too broad and in need of reslicing?
- Does the current `next_step` match the chosen mode?
- Would another agent looking only at the task card find this routing choice plausible?

## Minimal examples

### Example 1: broad feature request at early stage

Observed:
- user asks for hierarchical segmentation,
- solution space is still open,
- constraints and retrieval implications need clarification.

Route:
- `research_scout`

Reason:
- discovery dominates before contract formation.

### Example 2: feature design narrows to interface definition

Observed:
- the broad feature is now framed,
- the next task is defining the intermediate schema and acceptance boundaries.

Route:
- `contract_builder`

Reason:
- explicit contract formation dominates now.

### Example 3: clear bug with unknown cause

Observed:
- parser output is broken after a refactor,
- reproduction exists,
- the cause is not known yet.

Route:
- `debug_investigator`

Reason:
- causal isolation dominates before the fix.

### Example 4: known bug with bounded fix

Observed:
- failure cause is already established,
- the current slice is implementing the specific correction and test.

Route:
- `routine_implementer`

Reason:
- debugging has ended; bounded implementation now dominates.

### Example 5: evaluation packet requested

Observed:
- candidate and baseline outputs need to be compared,
- the next move depends on findings.

Route:
- `quality_evaluator`

Reason:
- evidence generation and interpretation dominate the current slice.

## Maintenance rules

- Keep this routing policy small and explicit.
- Prefer improving slice quality over adding new modes.
- Add a new universal routing rule only when repeated real cases cannot be expressed with the existing set.
- Do not turn routing into a giant taxonomy.
- When in doubt, choose the mode that best matches the immediate `next_step`, or reslice if no single mode fits.