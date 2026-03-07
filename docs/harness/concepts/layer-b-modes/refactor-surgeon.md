# Refactor Surgeon

## Purpose

`refactor_surgeon` is the Layer B operating mode for behavior-preserving structural change performed under explicit control of regression risk.

Use this mode when the dominant work is not to invent new behavior and not to diagnose unexplained failure, but to change the internal structure of the system while keeping externally relevant behavior stable enough for the current boundary.

This mode is appropriate when structure must change, but the task’s success depends on disciplined preservation rather than feature expansion.

## Common next doc

If the task card already says `layer_b.current_mode: refactor_surgeon`, use this file for mode-specific guidance.

If mode fit is unclear, use `docs/harness/policies/routing-rules.md`.
If the mode is confirmed and `layer_d.state` permits forward work, continue with `docs/harness/workflows/task-execution-loop.md`.
If the current state is paused or terminal, use `docs/harness/operator-map.md` to jump to the correct boundary doc.

## Core question

When operating in `refactor_surgeon`, the central question is:

> How can this structure be changed safely while preserving the intended behavior boundary?

The target is not generic cleanup. The target is controlled restructuring with explicit attention to what must not change.

## When to use

Use `refactor_surgeon` when one or more of the following are true:

- the dominant work is internal restructuring, decomposition, extraction, reorganization, or type/model cleanup,
- the intended external behavior should remain stable for the current slice,
- the main risk is accidental regression introduced by structure change,
- the slice exists to improve maintainability, clarity, modularity, or internal shape without changing the contract materially,
- the task is about safely moving code, responsibilities, or abstractions rather than inventing new product behavior,
- existing behavior is sufficiently known that preservation can be evaluated.

This mode is often the right posture for internal code improvement, safe decomposition, and structural evolution that should not silently change what the system does.

## When not to use

Do not use `refactor_surgeon` when:

- the dominant work is direct delivery of new or changed behavior, in which case `routine_implementer` is usually better,
- the system is still being explored and the real work is uncertainty reduction, in which case `research_scout` is usually better,
- the task is really about defining an interface, schema, or acceptance boundary, in which case `contract_builder` is usually better,
- the main problem is unexplained failure or regression diagnosis, in which case `debug_investigator` is usually better,
- the dominant work is evidence generation or acceptance assessment, in which case `quality_evaluator` is usually better,
- the slice is mainly about staged transition, compatibility, rollback, or cutover, in which case `migration_operator` is usually better,
- the slice is mainly about measured improvement work rather than structural preservation, in which case `optimization_tuner` is usually better.

Do not use this mode as a euphemism for broad rewrites. Use it when behavior-preserving structural change is the actual current task.

## Typical Layer A signals

`refactor_surgeon` is often a good fit when Layer A looks something like this:

- `problem_uncertainty`: low or low-to-medium
- `specification_maturity`: medium-to-high or high enough that preserved behavior is known
- `dependency_complexity`: medium or high if the structure touches widely used paths
- `validation_burden`: medium or high because preservation must be checked
- `blast_radius`: often medium or high depending on how shared the structure is
- `execution_horizon`: short-to-medium for the current slice

Common signals include:
- desired behavior is mostly established,
- internal shape is the part under change,
- regression risk matters more than feature ambiguity,
- the slice should produce a safer or cleaner structure without changing intent.

## Primary working posture

When operating as `refactor_surgeon`, the agent should:

- define what behavior or boundary must remain stable,
- isolate the structural change into the smallest coherent slice,
- preserve externally relevant invariants while reshaping internals,
- make regression-sensitive areas explicit,
- prefer incremental safe movement over broad rewrite leaps,
- avoid opportunistic behavior changes hidden inside the refactor,
- keep the task card, rationale, and next step aligned with preservation rather than feature growth,
- stop and reroute if the task reveals that behavior itself is unclear or must change materially.

The posture is precise structural intervention, not general cleanup and not disguised feature work.

## Primary outputs

Typical outputs of `refactor_surgeon` include:

- extracted modules or functions,
- reorganized responsibilities,
- simplified control flow,
- safer type/model structure,
- reduced duplication where behavior is preserved,
- internal API cleanup under a stable external contract,
- preservation-focused test updates,
- narrower future implementation surfaces created by structural improvement.

A successful `refactor_surgeon` slice usually leaves the system cleaner or safer internally without creating uncertainty about intended behavior.

## Typical next-step patterns

Good `next_step` patterns in this mode include:

- `Extract the normalization-stage helpers into a separate module while preserving current parser output behavior.`
- `Split the evaluation orchestration logic from result formatting without changing external task behavior.`
- `Replace the duplicated block-shape mapping paths with one shared internal function and keep output equivalence checks in place.`
- `Reorganize the schema model definitions into explicit types while preserving serialized field behavior.`
- `Move migration compatibility checks behind a dedicated internal boundary without changing rollout semantics.`

Weak `next_step` patterns in this mode include:

- `clean up code`
- `refactor stuff`
- `improve architecture`
- `continue`

## Allowed autonomy pattern

`refactor_surgeon` can usually proceed autonomously while:

- performing bounded structural changes,
- improving internal decomposition,
- moving or extracting code under explicit preservation constraints,
- tightening local abstractions,
- updating local preservation checks and related notes,
- recording what behavior is intended to remain stable.

It should usually slow down or stop when:

- the refactor begins to change externally relevant behavior materially,
- the preserved boundary is not actually clear enough,
- the work reveals a concrete failure that requires diagnosis,
- the slice expands into a larger migration or compatibility problem,
- a review boundary, approval boundary, or other non-baseline control boundary should be crossed before proceeding further,
- the dominant work becomes evidence generation rather than structural change.

This mode should not absorb hidden redesign or delivery work just because the refactor touches those areas.

## Typical validation style

Validation in this mode is preservation-oriented.

Typical forms include:
- regression checks,
- equivalence checks,
- targeted tests around preserved behavior,
- contract-conformance checks,
- comparison of before/after outputs for representative scenarios,
- review focused on unintended behavior drift.

A `refactor_surgeon` slice is often considered good enough when:
- preserved behavior still holds for the relevant boundary,
- the structural change is cleanly contained,
- the system is internally simpler, safer, or easier to evolve,
- no hidden contract changes were introduced unintentionally.

If validation or comparison becomes the dominant work product rather than a bounded preservation step, rerouting to `quality_evaluator` may be more appropriate.

## Common reroute triggers

Reroute away from `refactor_surgeon` when the dominant work changes.

Common reroute triggers include:

### Reroute to `routine_implementer`

When:
- the slice has turned into intentional behavior change rather than preservation,
- the next useful work is delivering a new or changed capability.

### Reroute to `debug_investigator`

When:
- unexplained breakage appears and causal isolation becomes the dominant work,
- the preservation boundary has already been violated and diagnosis must come first.

### Reroute to `contract_builder`

When:
- the supposedly preserved behavior is not actually explicit enough,
- the task reveals that the contract or acceptance boundary must be clarified before structural change can be judged safely.

### Reroute to `quality_evaluator`

When:
- the refactor is complete and the dominant remaining work is evidence generation about preservation or readiness,
- comparison and assessment now dominate the slice.

### Reroute to `migration_operator`

When:
- the structural change is actually part of a staged transition with compatibility, coexistence, or rollback concerns that dominate the task.

## Common next modes

Typical next modes after `refactor_surgeon` are:
- `quality_evaluator`
- sometimes `routine_implementer`
- sometimes `debug_investigator`
- sometimes `contract_builder`
- sometimes `migration_operator`

A common pattern is:
- structure becomes painful -> `refactor_surgeon`
- preservation checked -> `complete` or `quality_evaluator`

## Typical risks / failure modes

Common failure modes in `refactor_surgeon` include:

### 1. Disguised rewrite

The task claims to preserve behavior but actually becomes a broad redesign.

### 2. Hidden behavior change

The refactor silently changes externally relevant behavior without updating the task framing.

### 3. Cleanup sprawl

The slice absorbs every nearby improvement opportunity and stops being bounded.

### 4. Weak preservation boundary

The team assumes behavior is known, but the relevant invariants were never stated clearly enough.

### 5. Under-validated structural change

The refactor is completed with insufficient regression checking for the touched boundary.

### 6. Stale mode after failure emerges

The task remains labeled as refactor work even though the dominant activity has become debugging or contract clarification.

## Good operating heuristics

Useful heuristics in this mode:

- state explicitly what behavior must remain stable,
- refactor in the smallest coherent slices that still improve structure,
- prefer reversible, inspectable changes over large structural jumps,
- separate "make it cleaner" from "make it different",
- if an intentional behavior change is needed, route it explicitly rather than hiding it inside the refactor,
- keep regression-sensitive checks close to the preserved boundary,
- ask whether another agent could understand what changed structurally and what was meant to stay the same.

## Relationship to Layer C and Layer D

### Relationship to Layer C

`refactor_surgeon` may run inside a `feature_cell` when the refactor is one bounded slice inside a broader multi-slice workstream.

It may also run under one or more `control_profile` records when structural change must satisfy explicit review, approval, evidence, traceability, or rollback obligations before wider adoption. Presets such as `reviewed`, `change_controlled`, or `high_assurance` may be relevant when the touched boundary is shared or high-consequence.

These Layer C constructs wrap or constrain the work. They do not define the current mode.

### Relationship to Layer D

A `refactor_surgeon` task is often:
- `active` while structural change is underway,
- sometimes `validating` when preservation evidence becomes dominant,
- sometimes `checkpoint` when the change should pause for review,
- sometimes `complete` when the bounded structural slice is finished and preservation is satisfied,
- sometimes `blocked` if dependencies or preservation criteria are missing.

The mode can remain `refactor_surgeon` while the Layer D lifecycle state changes.

## Example task shapes

Typical tasks that fit `refactor_surgeon` well:

- extract shared parser normalization helpers without changing output behavior,
- restructure evaluation orchestration into clearer internal modules while preserving external task flow,
- centralize duplicated schema-model mapping logic without changing serialized results,
- split a large internal service into smaller components while preserving existing interface behavior,
- simplify control flow in a critical path while keeping outputs and operational semantics stable.

## Practical checklist

Use this checklist to validate whether `refactor_surgeon` is the right mode:

- Is the main work structural change rather than new behavior delivery?
- Is the preserved behavior boundary explicit enough to check?
- Is regression risk the main concern rather than ambiguity about the desired outcome?
- Can the slice stay bounded while improving structure?
- Does exactly one preservation-oriented posture clearly dominate?

If yes, `refactor_surgeon` is probably the right mode.

## Short operational summary

Use `refactor_surgeon` when the current slice should improve internal structure while preserving the intended behavior boundary.

The hallmark of this mode is not generic cleanup. It is controlled structural change under explicit preservation discipline.
