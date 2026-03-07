

# Contract Builder

## Purpose

`contract_builder` is the Layer B operating mode for turning a partly known problem into an explicit executable agreement.

Use this mode when the dominant work is defining what downstream work should build against, validate against, or treat as accepted. The output is not primarily code or evaluation findings. The output is a clearer contract: boundary, schema, interface, behavior definition, acceptance condition, or implementation-ready scope.

This mode is especially useful when implementation would be premature without sharper agreement on expected behavior.

## Common next doc

If the task card already says `layer_b.current_mode: contract_builder`, use this file for mode-specific guidance.

If mode fit is unclear, use `docs/harness/policies/routing-rules.md`.
If the mode is confirmed and `layer_d.state` permits forward work, continue with `docs/harness/workflows/task-execution-loop.md`.
If the current state is paused or terminal, use `docs/harness/operator-map.md` to jump to the correct boundary doc.

## Core question

When operating in `contract_builder`, the central question is:

> What must be made explicit so that later work can proceed against a stable enough boundary?

That boundary may be:
- an API contract,
- a schema,
- an RFC section,
- a behavior definition,
- an acceptance rule,
- a task or slice boundary,
- a migration contract between old and new paths,
- or another explicit agreement surface.

## When to use

Use `contract_builder` when one or more of the following are true:

- the problem is framed enough to define an agreement, but not yet defined enough to implement safely,
- downstream implementation is likely to drift without clearer boundaries,
- acceptance conditions need to be made explicit,
- the main uncertainty is about what the output, interface, or boundary should be,
- a broad initiative needs to be narrowed into an executable slice,
- a schema or intermediate representation must be defined before multiple later slices can proceed,
- behavior is disputed or underspecified even though the general direction is known,
- a reviewable design or contract artifact is the correct next deliverable.

This mode is often the right bridge between early exploration and bounded implementation.

## When not to use

Do not use `contract_builder` when:

- the dominant work is still open-ended discovery and problem-space mapping rather than agreement formation, in which case `research_scout` is usually better,
- the contract is already sufficiently clear and the real work is a bounded change, in which case `routine_implementer` is usually better,
- the main problem is failing behavior with unknown cause, in which case `debug_investigator` is usually better,
- the dominant work is evidence generation, benchmarking, or acceptance checking rather than contract definition, in which case `quality_evaluator` is usually better,
- the slice is a behavior-preserving structural change rather than a contract-definition problem, in which case `refactor_surgeon` is usually better.

Do not use this mode as a vague synonym for “planning.” It should produce a concrete contract artifact or contract-shaping outcome.

## Typical Layer A signals

`contract_builder` is often a good fit when Layer A looks something like this:

- `problem_uncertainty`: low-to-medium or medium
- `specification_maturity`: medium and rising, but not yet high enough for safe execution
- `validation_burden`: medium or high because acceptance must be explicit
- `interpretation_burden`: often medium or high because tradeoffs, exclusions, or acceptance shape require judgment
- `dependency_complexity`: often medium or higher if multiple later slices depend on the same boundary
- `artifact_type`: often schema, RFC, interface, acceptance criteria, or another contract artifact
- `execution_horizon`: short or medium for the current slice, even if the broader effort is larger

Common signals include:
- a bounded scope exists, but the contract inside it is still loose,
- implementation risks rework because expected behavior is underspecified,
- multiple later consumers depend on a shared explicit interface or schema,
- the specification is mature enough to define the boundary but not yet mature enough to execute safely,
- human judgment is needed to make acceptance, invariants, or exclusions explicit,
- the current useful output is a draft that can be reviewed and then executed against.

## Primary working posture

When operating as `contract_builder`, the agent should:

- narrow broad intent into explicit boundaries,
- convert vague expectations into concrete acceptance language,
- identify what must be stable now versus what can remain deferred,
- make interfaces, invariants, exclusions, and assumptions visible,
- produce a contract artifact that other slices can reference,
- avoid premature implementation detail unless it is needed to sharpen the contract,
- keep the contract minimal enough for the current phase rather than over-designing the future.

The posture is disciplined clarification, not open-ended ideation and not direct code-first delivery.

## Primary outputs

Typical outputs of `contract_builder` include:

- schema drafts,
- interface definitions,
- RFC sections,
- acceptance criteria,
- scope boundary notes,
- invariants and exclusions,
- task or slice definitions,
- migration boundary contracts,
- review packets for contract approval,
- explicit decision-ready proposals about what the next implementation slice should assume.

A successful `contract_builder` slice usually leaves the system more executable by making expectations more explicit.

## Typical next-step patterns

Good `next_step` patterns in this mode include:

- `Draft the required and optional fields for the intermediate schema and define phase-1 exclusions.`
- `Write explicit acceptance criteria for parser block-shape preservation.`
- `Define the API boundary between the segmentation stage and downstream retrieval assembly.`
- `Clarify the parent/child invariants for nested block handling and record deferred edge cases.`
- `Prepare the contract review packet with proposed boundary, tradeoffs, and open questions.`

Weak `next_step` patterns in this mode include:

- `work on schema`
- `plan implementation`
- `think more about design`
- `continue`

## Allowed autonomy pattern

`contract_builder` can usually proceed autonomously while:

- drafting a contract,
- sharpening scope,
- specifying fields or invariants,
- making exclusions explicit,
- turning broad requests into reviewable proposals,
- splitting a vague problem into bounded future slices.

It should usually slow down or stop when:

- a real choice among materially different directions requires review,
- a milestone contract must be accepted before downstream execution,
- a non-baseline control boundary or explicit approval boundary must be crossed before locking the boundary,
- evidence is needed to validate the contract assumptions.

This means `contract_builder` often operates inside explicit Layer C control-profile context, but that context remains separate from the mode itself.

## Typical validation style

Validation in this mode is usually not “tests pass” in the ordinary sense.

More typical validation forms are:
- reviewability,
- clarity of acceptance conditions,
- consistency of fields/invariants,
- sufficiency for downstream slices,
- absence of hidden contradictions,
- agreement that the defined boundary is explicit enough to proceed.

In practical terms, a contract is often considered good enough when:
- another agent could implement against it without inventing major missing rules,
- the acceptance basis is explicit,
- phase boundaries and exclusions are clearly stated,
- the next slice becomes narrower rather than more ambiguous.

## Common reroute triggers

Reroute away from `contract_builder` when the dominant work changes.

Common reroute triggers include:

### Reroute to `routine_implementer`

When:
- the contract is now sufficiently explicit,
- the next useful work is a bounded implementation change,
- ambiguity no longer dominates the slice.

### Reroute to `research_scout`

When:
- the supposed contract problem is actually still a discovery problem,
- the option space is not yet understood enough to define a useful contract,
- more mapping or evidence is needed before agreement formation.

### Reroute to `debug_investigator`

When:
- the task appears to be a contract problem but actually depends on identifying why current behavior fails,
- reproduction and root-cause isolation become the dominant work.

### Reroute to `quality_evaluator`

When:
- the contract exists but now must be assessed against evidence, benchmarks, or acceptance scenarios,
- the main work becomes validation of readiness rather than contract formation.

## Common next modes

Typical next modes after `contract_builder` are:
- `routine_implementer`
- `quality_evaluator`
- sometimes `research_scout`
- sometimes `migration_operator` if the contract was for a staged transition boundary

The most common progression is:
- exploration narrows -> `contract_builder`
- contract becomes executable -> `routine_implementer`

## Typical risks / failure modes

Common failure modes in `contract_builder` include:

### 1. Over-design

The contract grows to cover future phases that do not need to be locked now.

### 2. Faux clarity

The artifact looks formal, but key acceptance conditions or invariants are still ambiguous.

### 3. Premature execution leakage

The task drifts into implementation before the contract is stable enough, causing downstream rework.

### 4. Endless specification churn

The contract keeps expanding because the slice boundary was never made explicit.

### 5. Hidden review boundary

The draft is effectively waiting for review or acceptance, but the task remains `active` without a real checkpoint transition.

### 6. Confusing contract work with research

The agent keeps exploring generally instead of forcing the agreement surface into explicit shape.

## Good operating heuristics

Useful heuristics in this mode:

- define what must be stable now and what is explicitly deferred,
- make exclusions visible, not just inclusions,
- state acceptance in executable language where possible,
- prefer a minimal sufficient contract over a comprehensive speculative one,
- write so another agent can act against the result,
- when the contract is “almost done,” ask whether a reviewer could make a real decision from it,
- if no decision could be made yet, the contract is probably still too vague.

## Relationship to Layer C and Layer D

### Relationship to Layer C

`contract_builder` may run inside a `feature_cell` when the contract slice belongs to a broader multi-slice workstream.

It may also run under one or more `control_profile` records when the contract must satisfy explicit review, approval, evidence, traceability, or rollback obligations before downstream execution. Presets such as `reviewed`, `change_controlled`, or `high_assurance` are common examples of that control context.

These Layer C constructs wrap or constrain the work. They do not define the current mode.

### Relationship to Layer D

A `contract_builder` task is often:
- `active` while drafting and refining,
- `checkpoint` when the contract is ready for review,
- sometimes `awaiting_approval` if the contract requires signoff,
- sometimes `complete` if the current slice was only to define and deliver the contract.

The mode can stay `contract_builder` while the Layer D lifecycle state changes.

## Example task shapes

Typical tasks that fit `contract_builder` well:

- define the intermediate schema between parsing and segmentation,
- write acceptance rules for a regression-sensitive behavior boundary,
- define the API boundary between two pipeline components,
- draft an RFC section that downstream implementation depends on,
- turn a broad feature ask into a bounded execution slice with explicit exclusions,
- clarify migration compatibility rules before rollout steps begin.

## Practical checklist

Use this checklist to validate whether `contract_builder` is the right mode:

- Is the main work defining a boundary, contract, schema, or acceptance target?
- Would direct implementation likely drift or rework without clearer agreement?
- Is the slice more about explicit agreement than about discovery, debugging, or evaluation?
- Can the output of this slice make later work narrower and safer?
- Is exactly one contract-shaping posture clearly dominant?

If yes, `contract_builder` is probably the right mode.

## Short operational summary

Use `contract_builder` when the current slice should turn a partly known problem into a stable enough agreement that later work can proceed against it.

The hallmark of this mode is not “planning” in the abstract. It is production of an explicit contract that reduces ambiguity for downstream execution, review, or validation.
