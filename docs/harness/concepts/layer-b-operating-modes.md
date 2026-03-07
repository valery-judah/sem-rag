# Layer B: Atomic Operating Modes for Agentic Work

## Status

Draft v1.1

## Purpose

This document defines **Layer B** in the agentic work model: the set of **atomic operating modes** used to answer the question:

> How should the agent work **now** on the current work slice?

Layer B is intentionally downstream from Layer A. It does **not** classify the work itself. Instead, it takes a **Layer A classification snapshot** and selects the current working posture that best fits the slice at the present moment.

Layer B exists to prevent several common modeling errors:

- treating a temporary operating posture as the permanent identity of a task,
- treating governance constructs such as review gates as if they were delivery modes,
- treating long-horizon orchestration structures such as feature workstreams as if they were atomic modes,
- and mixing control-plane lifecycle state into work-mode selection.

A task or workstream may pass through several Layer B modes over time. Mode selection is therefore **current-state routing**, not destiny.

## Position in the overall stack

The intended stack is:

### Layer A -- Classification snapshot

Orthogonal descriptors of the current work slice.

Examples:

- intent,
- uncertainty,
- dependency complexity,
- knowledge locality,
- specification maturity,
- validation burden,
- blast radius,
- execution horizon.

### Layer B -- Atomic operating mode

The current answer to:

> How should the agent behave now?

Canonical modes:

- Research Scout
- Contract Builder
- Routine Implementer
- Refactor Surgeon
- Debug Investigator
- Migration Operator
- Optimization Tuner
- Quality Evaluator

### Layer C -- Workstream wrapper and control regime

Structures that wrap work across time or impose explicit control obligations without changing the current problem-solving posture.

Examples:

- `feature_cell` as the long-horizon workstream wrapper,
- `control_profile` as the canonical control object,
- preset aliases such as `reviewed`, `change_controlled`, or `high_assurance` as ergonomic summaries of common non-baseline control contexts.

### Layer D -- Lifecycle control plane

Small shared state model plus workflow-local `phase`.

Examples:

- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

## Why Layer B exists

Layer A can describe the shape of a work slice with good precision. For example, a slice may be:

- `intent = implement`,
- `uncertainty = design_heavy`,
- `dependency_complexity = cross_module`,
- `knowledge_locality = scattered_internal`,
- `specification_maturity = scoped_problem`,
- `validation_burden = partial_signals_only`,
- `execution_horizon = multi_pr`.

That snapshot is valuable, but it still does not tell the agent how to operate.

The agent may need to:

- gather evidence,
- draft a contract,
- implement directly,
- debug through diagnosis loops,
- structure a migration,
- run benchmarks,
- or produce evaluation evidence.

Layer B converts classification into a small catalog of **working postures** that can be routed consistently.

This keeps the model clean in four ways:

1. **Classification remains descriptive.**
   Layer A describes the slice without prematurely assigning a mode.
2. **Mode remains operational.**
   Layer B says how to work, not what the work permanently is.
3. **Containers stay separate.**
   Long-running workstream structure belongs in Layer C.
4. **Control state stays separate.**
   Whether the work can continue, needs a checkpoint, or is waiting on approval belongs in Layer D.

## Design principles

### 1. Modes are routing outputs

Layer B modes are selected **from** Layer A. They are not Layer A fields.

For example:

- `specification_maturity = scoped_problem` does not itself mean `Contract Builder`,
- `execution_horizon = multi_pr` does not itself mean `feature_cell`,
- `validation_burden = offline_eval_required` does not itself mean `Quality Evaluator` in every case.

Those are downstream routing conclusions.

### 2. Modes are current, not permanent

A task may start in uncertainty-reduction mode and later become implementation-ready. A long-running workstream may pass through several modes across time. Layer B therefore records the **current dominant operating posture**, not the eternal identity of the task.

### 3. Modes should be atomic

A Layer B mode should capture one dominant way of working now. It should not encode an entire multi-stage delivery topology.

### 4. Keep Layer C constructs out of Layer B

The following are **not** Layer B peers:

- `control_profile`,
- preset summaries such as `reviewed` or `change_controlled`,
- `feature_cell`.

These are Layer C constructs. They can constrain or wrap Layer B work, but they do not replace the current atomic mode.

### 5. Keep lifecycle state out of Layer B

States such as `checkpoint`, `awaiting_approval`, and `validating` are not operating modes. They are control-plane states from Layer D.

A mode may appear in multiple lifecycle states. For example:

- Contract Builder may be `active` while drafting,
- Contract Builder may be `checkpoint` when trade-offs need review,
- Migration Operator may be `awaiting_approval` before cutover,
- Quality Evaluator may be `validating` while evidence is being gathered.

### 6. Prefer reclassification over premature execution

If a task initially looks executable but core ambiguity remains, the system should reroute into an earlier mode rather than forcing implementation.

### 7. Keep the mode set small and stable

A new mode should be introduced only when repeated real tasks cannot be described well by the existing modes and when the distinction materially changes how the agent should behave.

## Scope and non-scope

### In scope

Layer B defines:

- the canonical set of atomic operating modes,
- the role of Layer B in the layered model,
- the system-level routing semantics for selecting a current mode,
- the transition logic and reroute principles between modes,
- the relationship between Layer B and Layers A, C, and D,
- and the minimal schema for recording current mode and mode history.

### Out of scope

Layer B does **not** define:

- Layer A classification axes,
- Layer C control profiles and workstream wrappers,
- Layer D lifecycle state,
- detailed playbook procedures,
- agent configuration internals such as tool authority or instruction regime,
- full workflow microstates,
- or organization-specific approval policy.

Mode-specific operational depth is also kept out of this umbrella document and lives in the dedicated mode files under `docs/harness/concepts/layer-b-modes/`.

## Canonical atomic operating modes

Layer B standardizes on the following eight atomic operating modes:

1. **Research Scout**
2. **Contract Builder**
3. **Routine Implementer**
4. **Refactor Surgeon**
5. **Debug Investigator**
6. **Migration Operator**
7. **Optimization Tuner**
8. **Quality Evaluator**

These are the canonical routing outputs for the current work slice.

## Canonical mode index

The detailed operational references for each mode live in `docs/harness/concepts/layer-b-modes/`.

| Mode | One-line purpose | Detailed file |
|---|---|---|
| Research Scout | Reduce uncertainty through bounded discovery, mapping, and findings synthesis. | `layer-b-modes/research-scout.md` |
| Contract Builder | Turn a partly known problem into an explicit contract, boundary, or acceptance target. | `layer-b-modes/contract-builder.md` |
| Routine Implementer | Execute a clear bounded change against a sufficiently explicit target. | `layer-b-modes/routine-implementer.md` |
| Refactor Surgeon | Perform behavior-preserving structural change under explicit regression control. | `layer-b-modes/refactor-surgeon.md` |
| Debug Investigator | Diagnose failing or incorrect behavior when the cause is not yet isolated. | `layer-b-modes/debug-investigator.md` |
| Migration Operator | Handle staged transitions where sequencing, compatibility, and rollback matter. | `layer-b-modes/migration-operator.md` |
| Optimization Tuner | Improve measurable technical behavior against explicit targets and baselines. | `layer-b-modes/optimization-tuner.md` |
| Quality Evaluator | Produce or interpret evidence about quality, correctness, readiness, or acceptance. | `layer-b-modes/quality-evaluator.md` |

## How to use this document versus the per-mode files

Use this document when you need to understand:

- what Layer B is,
- why it is separate from Layers A, C, and D,
- how routing should work in principle,
- how rerouting should work over time,
- what fields should be recorded for current mode and mode history.

Use the per-mode files when you need to know:

- when a specific mode does or does not apply,
- what outputs to expect from that mode,
- how the agent should behave inside that mode,
- common reroute triggers for that mode,
- mode-specific risks and failure patterns.

In normal operation, the recommended sequence is:

1. classify the current slice with Layer A,
2. route into one Layer B mode,
3. open the detailed file for that mode,
4. then continue with Layer C and Layer D constraints kept separate.

## Standard mode template

The detailed mode files should stay structurally consistent, but the shared authoring contract for maintaining that structure now lives in `docs/harness-maintain/main.md`.

Use this umbrella Layer B document for semantics and routing boundaries. Use the maintainer guide when changing the canonical mode set or the shared mode-file structure.

## Routing guidance from Layer A to Layer B

This section provides routing guidance, not a rigid deterministic state machine.

### Core routing logic

#### 1. Start from the dominant question

Ask which of these is most true **now**:

- Do we need to **discover**?
- Do we need to **bound the contract**?
- Do we need to **execute directly**?
- Do we need to **diagnose**?
- Do we need to **stage a risky transition**?
- Do we need to **optimize against a measurable technical target**?
- Do we need to **produce quality evidence**?

That question usually determines the initial Layer B mode.

#### 2. Use Layer A signals as routing constraints

Layer A fields should constrain the choice.

Typical patterns:

- high uncertainty + weak knowledge locality -> **Research Scout**,
- known objective + under-mature contract -> **Contract Builder**,
- implementation-ready + low ambiguity + strong tests -> **Routine Implementer**,
- behavior-preserving structural change -> **Refactor Surgeon**,
- known defect + unknown cause -> **Debug Investigator**,
- migration-shaped risk + sequencing/compatibility concerns -> **Migration Operator**,
- performance/cost/latency target + benchmark discipline -> **Optimization Tuner**,
- heavy evaluation burden or weak ordinary correctness signal -> **Quality Evaluator**.

#### 3. Prefer the dominant mode, not a blended label

Do not invent composite labels such as:

- `research-plus-implementation`,
- `debug-plus-review`,
- `migration-plus-feature`.

Pick the dominant current mode, then represent other concerns through:

- reroute triggers,
- Layer C control profiles,
- the Layer C `feature_cell` wrapper,
- and Layer D state/phase.

## Practical mapping matrix

| Dominant condition now | Typical Layer A pattern | Route to Layer B mode |
|---|---|---|
| Solution space is still being discovered | high uncertainty, low spec maturity, weak knowledge locality | Research Scout |
| Objective is known but contract is still forming | scoped problem, draft contract, local ambiguity or design-heavy | Contract Builder |
| Clear bounded implementation slice | implementation-ready, known pattern, strong tests | Routine Implementer |
| Structural cleanup under invariants | behavior-preserving internal change, regression checkable | Refactor Surgeon |
| Failing behavior with unknown root cause | concrete defect, diagnosis loop needed | Debug Investigator |
| Compatibility/cutover/rollback dominates | migration-shaped risk or transition mechanics dominate | Migration Operator |
| Measurable technical tuning dominates | optimize intent, benchmark-based improvement target | Optimization Tuner |
| Output quality evidence dominates | offline eval required, weak ordinary correctness signal | Quality Evaluator |

## Secondary routing rules

### Rule A -- Specification maturity overrides raw intent

If a task says `implement` but specification maturity is still `scoped_problem` or `draft_contract`, implementation is not yet the correct operating mode. Prefer **Contract Builder** first.

### Rule B -- Diagnosis overrides direct fix execution

If a bug fix is requested but the root cause is still unknown, prefer **Debug Investigator** over direct implementation.

### Rule C -- Validation burden can override execution mode

If correctness cannot be established by ordinary tests, reroute toward **Quality Evaluator** or, for rollout-sensitive changes, **Migration Operator**.

### Rule D -- Control context can constrain but not redefine the mode

High-risk or high-consequence work does not automatically create a new Layer B mode. It may keep the same mode while adding a non-baseline Layer C `control_profile` and stricter Layer D checkpoints.

### Rule E -- Horizon affects containment, not atomic mode

If the work is multi-PR or `handoff_need = high`, that often justifies a Layer C `feature_cell` workstream wrapper, but the current Layer B mode should still reflect the dominant slice.

## Reclassification and transition rules

Layer B modes should be expected to change over time.

### Transition principles

#### 1. Reclassification is normal

Tasks and workstreams mature. A task that begins in uncertainty reduction may later become execution-ready. A work item that starts as implementation may be reclassified if hidden ambiguity or evaluation difficulty appears.

#### 2. Reclassification should be evidence-based

Do not reroute casually. A mode change should normally be triggered by one of:

- new ambiguity discovered,
- contract freeze achieved,
- root cause isolated,
- evidence burden increased,
- governance risk surfaced,
- or horizon expansion.

#### 3. Prefer early reroute over late failure

If the current mode no longer fits, reroute early instead of forcing the work through the wrong posture.

## Common transition patterns

### Research Scout -> Contract Builder

When exploratory work has reduced uncertainty enough to define a bounded contract.

### Contract Builder -> Routine Implementer

When the contract becomes implementation-ready and the slice is clear, bounded, and normally verifiable.

### Contract Builder -> Refactor Surgeon

When the frozen contract describes behavior-preserving structural change.

### Contract Builder -> Migration Operator

When the resulting execution path is primarily a controlled transition.

### Debug Investigator -> Routine Implementer

When the issue is isolated and the remaining work is just the fix.

### Routine Implementer -> Contract Builder

When unexpected ambiguity appears and the contract is no longer good enough.

### Routine Implementer -> Quality Evaluator

When ordinary tests are not enough to prove the change is good.

### Any execution mode -> Migration Operator

When rollout, compatibility, sequencing, or rollback becomes the dominant concern.

### Optimization Tuner -> Quality Evaluator

When the tuning question becomes a broader evidence or acceptance problem rather than a narrow technical metric problem.

### Quality Evaluator -> Routine Implementer

When the evidence is clear and remaining work is straightforward implementation or threshold application.

## Mode history

Because mode is current rather than permanent, long-running work should preserve a compact mode history.

Recommended fields:

- entered mode,
- reason for entry,
- key evidence created,
- exit trigger,
- next recommended mode.

This allows a higher-layer orchestrator to reason not only from the current snapshot but from the trajectory of the work.

## Relationship to Layer C

Layer C contains the `feature_cell` workstream wrapper and `control_profile` records. Layer B modes may be constrained or wrapped by them, but they should not be collapsed into them.

### `control_profile` as control context

A `control_profile` records explicit review, approval, evidence, traceability, or rollback obligations that sit around the current mode.

Use it when the primary requirement is:

- review before continuation,
- approval before crossing a gate,
- stronger evidence or traceability,
- stronger rollback discipline,
- or another explicit non-baseline control burden.

That control context does not necessarily change the underlying Layer B mode. A task may remain in the same mode while moving from baseline to `reviewed`, `change_controlled`, or `high_assurance` handling.

Examples:

- Migration Operator under a change-controlled profile,
- Debug Investigator under a reviewed profile,
- Contract Builder under a reviewed or high-assurance profile.

### `feature_cell` as workstream wrapper

`feature_cell` should be modeled as a long-horizon workstream wrapper, not as a Layer B peer.

Use it when:

- the horizon is multi-step or multi-PR,
- handoff/resume discipline matters,
- several Layer B modes will likely occur over time,
- planning, tracking, and traceability are required.

A `feature_cell` may contain a sequence such as:

- Research Scout,
- Contract Builder,
- Routine Implementer,
- Quality Evaluator,
- Migration Operator,

without contradiction.

## Relationship to Layer D

Layer D controls whether work may proceed, pause, wait for approval, or finish. Layer B controls how the agent should work inside that control state.

### The separation rule

Do not encode Layer B semantics into Layer D state names.

Examples:

- `active` does not mean Routine Implementer,
- `checkpoint` does not mean Contract Builder,
- `validating` does not mean Quality Evaluator,
- `awaiting_approval` does not mean a reviewed or change-controlled control context.

These remain distinct layers.

### Examples

#### Contract Builder across lifecycle states

A contract-definition slice may look like:

- `state = active`, `phase = contract_drafting`
- later `state = checkpoint`, `phase = tradeoff_review`
- later `state = active`, `phase = contract_finalization`

The mode remains Contract Builder while control status changes.

#### Migration Operator across lifecycle states

A migration slice may look like:

- `state = active`, `phase = rehearsal`
- later `state = awaiting_approval`, `phase = cutover_ready`
- later `state = validating`, `phase = rollout_observation`

The mode remains Migration Operator while control state changes.

## Recommended mode record

A minimal Layer B record should be compact, explicit, and easy to update.

### Suggested schema

```yaml
current_mode:
  name: research_scout | contract_builder | routine_implementer | refactor_surgeon | debug_investigator | migration_operator | optimization_tuner | quality_evaluator
  reason: >
    Free-text explanation of why this mode is selected from the current Layer A snapshot.
  entered_at: 2026-03-06
  expected_outputs:
    - scoped contract
    - acceptance criteria
  next_likely_modes:
    - routine_implementer
    - migration_operator
  reroute_triggers:
    - contract frozen
    - migration sequencing becomes dominant
  confidence: low | medium | high
```

## Recommended companion mode history

```yaml
mode_history:
  - name: research_scout
    entered_at: 2026-03-01
    exit_reason: solution space narrowed enough for contract definition
  - name: contract_builder
    entered_at: 2026-03-03
    exit_reason: frozen contract approved for implementation
```

## Worked examples

### Example 1 -- Small local feature slice

#### Layer A snapshot

- intent: implement
- uncertainty: known_pattern
- dependency_complexity: few_local_dependencies
- knowledge_locality: mostly_local
- specification_maturity: implementation_ready
- validation_burden: tests_strong_confidence
- blast_radius: local
- execution_horizon: atomic

#### Layer B result

**Routine Implementer**

#### Notes

No Layer C `feature_cell` workstream wrapper is needed. Lifecycle state is likely `active` with `phase = coding`.

### Example 2 -- Feature request with unclear behavior

#### Layer A snapshot

- intent: implement
- uncertainty: design_heavy
- knowledge_locality: scattered_internal
- specification_maturity: scoped_problem
- validation_burden: partial_signals_only
- execution_horizon: multi_pr
- handoff_need: high

#### Layer B result now

**Contract Builder**

#### Layer C note

Because `execution_horizon = multi_pr` and `handoff_need = high`, wrap the broader effort in a Layer C `feature_cell` workstream wrapper at workstream scope.

#### Likely sequence

Contract Builder -> Routine Implementer -> Quality Evaluator

### Example 3 -- Bug with unknown root cause

#### Layer A snapshot

- intent: debug
- uncertainty: local_ambiguity
- knowledge_locality: scattered_internal
- specification_maturity: frozen_contract for expected behavior
- validation_burden: tests_strong_confidence if repro exists
- blast_radius: subsystem

#### Layer B result

**Debug Investigator**

#### Likely transition

Once the cause is isolated, reroute to **Routine Implementer** for the fix.

### Example 4 -- Risky schema transition

#### Layer A snapshot

- intent: migrate
- dependency_complexity: cross_service
- validation_burden: production_confirmation_required
- blast_radius: cross_service
- reversibility: hard
- sensitivity: data_integrity
- approval_requirement: explicit_gate

#### Layer B result

**Migration Operator**

#### Layer C / D note

Apply a non-baseline `control_profile`, typically a `change_controlled` or `high_assurance` profile, and expect lifecycle states such as `checkpoint`, `awaiting_approval`, and `validating` during rollout.

### Example 5 -- Retrieval quality improvement slice

#### Layer A snapshot

- intent: optimize
- uncertainty: local_ambiguity
- validation_burden: offline_eval_required
- knowledge_locality: mostly_local
- artifact_type: eval_report

#### Layer B result now

**Quality Evaluator**

#### Reroute rule

- If the slice shifts from generating and interpreting evaluation evidence to measurable tuning against an established benchmark and target metric, reroute to **Optimization Tuner**.

## Adoption guidance

### Start with the canonical eight modes

Do not add more Layer B modes at first. Use the eight canonical modes and rely on Layer C control profiles and the `feature_cell` wrapper before inventing additional work modes.

### Prefer routing rules over rigid hard state machines

Layer B should normally be implemented as:

- a small routing policy,
- a compact mode record,
- and explicit reroute triggers,

not as a large hard-coded finite-state machine.

### Add a new mode only when all are true

Add a new Layer B mode only if:

- the distinction appears repeatedly in real work,
- it changes agent behavior materially,
- it cannot be represented by current modes plus Layer C control profiles or `feature_cell`,
- and operators can select it consistently.

### Keep mode definitions operational

A Layer B mode definition should always be useful at execution time. If a section cannot guide routing, expected outputs, or reroute behavior, it is probably too abstract.

## Final recommendation

Layer B should remain a compact catalog of **atomic operating modes** with these properties:

- downstream from Layer A,
- independent from Layer C control profiles and workstream wrappers,
- independent from Layer D lifecycle state,
- current-state rather than permanent identity,
- and explicit about routing, transitions, and mode recording.

The canonical set should remain:

- Research Scout
- Contract Builder
- Routine Implementer
- Refactor Surgeon
- Debug Investigator
- Migration Operator
- Optimization Tuner
- Quality Evaluator

The detailed operational references should live in `docs/harness/concepts/layer-b-modes/`.

This is the right level for answering:

> Given the current classification snapshot, how should the agent work now?
