# Layer B: Atomic Operating Modes for Agentic Work
## Status

Draft v1.0

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

Examples:

- Research Scout
- Contract Builder
- Routine Implementer
- Refactor Surgeon
- Debug Investigator
- Migration Operator
- Optimization Tuner
- Quality Evaluator

### Layer C -- Overlays and containers

Structures that modify, constrain, or wrap work rather than describing the current problem-solving posture.

Examples:

- Review Gatekeeper as reviewer/control overlay,
- high-control governance overlay,
- Feature Cell as long-horizon workstream container.

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
   Long-running workstream structure belongs in Layer C rather than Layer B.
4. **Control state stays separate.**
   Whether the work can continue, needs a checkpoint, or is waiting on approval belongs in Layer D.

## Design principles
### 1. Modes are routing outputs

Layer B modes are selected **from** Layer A. They are not Layer A fields.

For example:

- `specification_maturity = scoped_problem` does not itself mean `Contract Builder`,
- `execution_horizon = multi_pr` does not itself mean `Feature Cell`,
- `validation_burden = offline_eval_required` does not itself mean `Quality Evaluator` in every case.

Those are downstream routing conclusions.

### 2. Modes are current, not permanent

A task may start in uncertainty-reduction mode and later become implementation-ready. A long-running workstream may pass through several modes across time. Layer B therefore records the **current dominant operating posture**, not the eternal identity of the task.

### 3. Modes should be atomic

A Layer B mode should capture one dominant way of working now. It should not encode an entire multi-stage delivery topology.

### 4. Keep overlays and containers out of Layer B

The following are **not** Layer B peers:

- Review Gatekeeper,
- high-control governance overlays,
- Feature Cell.

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
## In scope

Layer B defines:

- the canonical set of atomic operating modes,
- the purpose of each mode,
- the conditions under which each mode is selected,
- the expected outputs and evidence shape of each mode,
- common reroute triggers,
- common next modes,
- and the relationship between current mode and surrounding layers.

## Out of scope

Layer B does **not** define:

- Layer A classification axes,
- Layer C overlays and containers,
- Layer D lifecycle state,
- detailed playbook procedures,
- agent configuration internals such as tool authority or instruction regime,
- full workflow microstates,
- or organization-specific approval policy.

Those belong elsewhere.

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

## Standard mode template

Every Layer B mode should be specified using a consistent template.

### Mode fields

- **Purpose** -- what this mode is fundamentally for.
- **When to use** -- the dominant condition that should trigger this mode.
- **Typical Layer A signals** -- the Layer A patterns that commonly route here.
- **Primary working posture** -- how the agent should think and operate.
- **Primary outputs** -- the expected artifacts or outcomes.
- **Allowed autonomy pattern** -- the normal execution envelope for the mode.
- **Typical validation style** -- how confidence is built in this mode.
- **Common reroute triggers** -- what should cause transition to another mode.
- **Common next modes** -- where the work typically goes next.
- **Typical risks / failure modes** -- the main way this mode can go wrong.

## Mode definitions
## 1. Research Scout
### Purpose

Reduce uncertainty, gather evidence, compare options, and synthesize findings when the dominant problem is still exploratory.

### When to use

Use Research Scout when the primary task is not direct execution but discovery.

Typical situations:

- the path to a solution is unclear,
- multiple approaches are plausible,
- external research or scattered internal evidence is needed,
- the objective is broad enough that option comparison is required,
- implementation should not start until uncertainty is reduced.

### Typical Layer A signals

Common signals include:

- `intent = research`, or adjacent intent with strong discovery burden,
- `uncertainty = research_exploration` or `open_ended_investigation`,
- `knowledge_locality = external_research_required` or `tacit_human_required`,
- `specification_maturity = vague_idea` or `scoped_problem`,
- `validation_burden = partial_signals_only`.

### Primary working posture

Research Scout is evidence-first rather than implementation-first.

The agent should:

- frame the question,
- identify candidate approaches,
- gather evidence,
- compare trade-offs,
- make uncertainties explicit,
- and produce a recommendation rather than prematurely committing to execution.

### Primary outputs

Typical outputs:

- evidence summary,
- option comparison,
- recommendation memo,
- open-questions list,
- scoped problem framing,
- possible inputs to Contract Builder.

### Allowed autonomy pattern

Normally moderate autonomy. The agent should explore, synthesize, and recommend, but should not silently turn research into implementation when the problem is still materially uncertain.

### Typical validation style

Validation is usually based on:

- source quality,
- completeness of the option set,
- internal consistency,
- clarity of recommendation,
- and human review of findings.

### Common reroute triggers

Reroute away from Research Scout when:

- a clear direction has emerged,
- the intended behavior can now be bounded,
- the main remaining work is to define the contract,
- or the work is now implementable.

### Common next modes

- Contract Builder
- Quality Evaluator
- Routine Implementer in rare cases where the solution becomes straightforward

### Typical risks / failure modes

- endless exploration without convergence,
- weak comparison criteria,
- over-reliance on external analogies,
- recommendation without clear decision rationale,
- drifting into design or implementation without explicit reroute.

## 2. Contract Builder
### Purpose

Transform a partly known problem into an implementation-ready contract.

### When to use

Use Contract Builder when the objective is broadly known but the implementation contract is not yet mature enough for execution.

Typical situations:

- behavior or acceptance criteria are still ambiguous,
- trade-offs must be resolved before coding,
- the work needs decomposition into bounded slices,
- the current request is underspecified but not open-ended research.

### Typical Layer A signals

Common signals include:

- `specification_maturity = scoped_problem` or `draft_contract`,
- `uncertainty = local_ambiguity` or `design_heavy`,
- intent may be `implement`, `refactor`, `review`, or `migrate`,
- dependency complexity often `cross_module` or greater,
- knowledge locality often `mostly_local` or `scattered_internal`.

### Primary working posture

Contract Builder is clarification-first and boundary-setting.

The agent should:

- turn vague requests into a bounded contract,
- make assumptions explicit,
- separate goals, non-goals, constraints, and open questions,
- propose interfaces, acceptance criteria, and decomposition,
- identify what must be decided before implementation starts.

### Primary outputs

Typical outputs:

- scoped contract,
- acceptance criteria,
- interface or schema proposal,
- decomposition into slices,
- risk notes,
- explicit open questions,
- recommendation for next execution mode.

### Allowed autonomy pattern

Moderate autonomy with strong checkpoint discipline. The agent can shape the contract, but material trade-offs or unclear intended behavior often justify checkpoint review.

### Typical validation style

Validation is mostly based on:

- internal consistency,
- coverage of goals and non-goals,
- decision clarity,
- reviewability,
- and readiness for downstream execution.

### Common reroute triggers

Reroute away from Contract Builder when:

- the contract is frozen or implementation-ready,
- behavior-preserving restructuring becomes the main task,
- migration sequencing becomes dominant,
- or the remaining work is direct execution.

### Common next modes

- Routine Implementer
- Refactor Surgeon
- Migration Operator
- Quality Evaluator for eval-heavy contract definition

### Typical risks / failure modes

- over-designing beyond the needed boundary,
- pretending ambiguity is resolved when it is not,
- freezing the contract too early,
- or producing a document that does not materially guide execution.

## 3. Routine Implementer
### Purpose

Execute a clear, bounded, implementation-ready change with normal engineering discipline.

### When to use

Use Routine Implementer when the work is ready to be done directly.

Typical situations:

- the spec is clear,
- the behavior is known,
- the blast radius is modest,
- the main work is coding and verification,
- and standard tests provide strong confidence.

### Typical Layer A signals

Common signals include:

- `intent = implement`,
- `uncertainty = known_pattern` or limited `local_ambiguity`,
- `specification_maturity = frozen_contract` or `implementation_ready`,
- `validation_burden = trivial_local_check` or `tests_strong_confidence`,
- `blast_radius = local` or modest `subsystem`,
- `execution_horizon = one_shot` or bounded `multi_step`.

### Primary working posture

Routine Implementer is execution-first.

The agent should:

- plan only as much as needed,
- implement the change,
- add or update tests,
- run verification,
- and produce a concise implementation summary.

### Primary outputs

Typical outputs:

- code change,
- tests,
- short implementation note,
- updated task status,
- validation results.

### Allowed autonomy pattern

Usually the highest autonomy among the modes, subject to local operating policy and risk bounds.

### Typical validation style

Validation is usually:

- compile/test,
- targeted integration checks,
- and localized reasoning over the changed surface.

### Common reroute triggers

Reroute away from Routine Implementer when:

- core ambiguity appears during execution,
- the task turns out to be mostly diagnosis,
- structural refactoring dominates,
- migration sequencing becomes necessary,
- or tests are not enough to establish confidence.

### Common next modes

- Refactor Surgeon
- Debug Investigator
- Migration Operator
- Quality Evaluator
- Contract Builder if the spec proves less mature than expected

### Typical risks / failure modes

- starting execution on a not-actually-clear task,
- local optimization that breaks wider assumptions,
- insufficient verification,
- or silent scope expansion.

## 4. Refactor Surgeon
### Purpose

Perform behavior-preserving structural change with deliberate control over code shape and regression risk.

### When to use

Use Refactor Surgeon when the main goal is not new user-visible behavior, but improvement to structure, modularity, maintainability, or clarity under behavior-preservation constraints.

Typical situations:

- extracting abstractions,
- reorganizing modules,
- renaming and decomposing code paths,
- reducing duplication,
- or isolating seams for future work.

### Typical Layer A signals

Common signals include:

- `intent = refactor`,
- `uncertainty = known_pattern` or `local_ambiguity`,
- `specification_maturity = frozen_contract` or `implementation_ready`,
- change scope may still be `cross_module`,
- validation burden is often `tests_strong_confidence` but may be `partial_signals_only` if legacy coverage is weak.

### Primary working posture

Refactor Surgeon is structure-first with strong invariants.

The agent should:

- identify invariants that must remain true,
- minimize unnecessary semantic drift,
- separate mechanical transformation from logical change,
- preserve behavior unless contractually approved otherwise,
- and stage risky refactors incrementally when possible.

### Primary outputs

Typical outputs:

- restructured code,
- clarified boundaries,
- preserved tests or added regression tests,
- refactor notes explaining invariants and risk.

### Allowed autonomy pattern

Moderate to high autonomy for local refactors; lower autonomy as the refactor becomes non-local or weakly verifiable.

### Typical validation style

Validation often relies on:

- regression tests,
- invariant checks,
- static analysis,
- and careful review of behavior-preservation assumptions.

### Common reroute triggers

Reroute away from Refactor Surgeon when:

- the work becomes a functional redesign,
- intended behavior is actually under-specified,
- diagnosis becomes dominant,
- migration mechanics emerge,
- or quality evidence beyond tests becomes necessary.

### Common next modes

- Routine Implementer
- Contract Builder
- Debug Investigator
- Quality Evaluator

### Typical risks / failure modes

- accidental behavior change,
- hidden coupling,
- sweeping edits without stable invariants,
- or underestimating legacy knowledge locality.

## 5. Debug Investigator
### Purpose

Diagnose known failing behavior when the root cause is not yet isolated.

### When to use

Use Debug Investigator when the dominant problem is diagnosis rather than direct repair.

Typical situations:

- a bug is observed but the cause is unknown,
- reproduction is partial or unstable,
- logs, traces, and code inspection must be combined,
- the issue may involve environment or integration behavior.

### Typical Layer A signals

Common signals include:

- `intent = debug`,
- uncertainty often `local_ambiguity` or `design_heavy` at the causal level,
- specification maturity may be clear about expected behavior but not about the defect source,
- validation burden may be `tests_strong_confidence` if repro exists or `partial_signals_only` if repro is weak,
- knowledge locality is often `scattered_internal`.

### Primary working posture

Debug Investigator is diagnosis-first.

The agent should:

- reproduce or sharpen the failing behavior,
- narrow the causal search space,
- test hypotheses,
- isolate the root cause,
- distinguish symptom from cause,
- and avoid premature fixes before the issue is understood.

### Primary outputs

Typical outputs:

- repro notes,
- causal hypotheses,
- narrowed suspect set,
- root-cause explanation,
- recommended or implemented fix after reroute.

### Allowed autonomy pattern

Moderate autonomy with iterative loops. Production-adjacent or incident-like debugging may need stricter control overlays.

### Typical validation style

Validation is usually based on:

- reproduction quality,
- hypothesis elimination,
- fix confirmation against repro,
- and regression checks.

### Common reroute triggers

Reroute away from Debug Investigator when:

- the issue is isolated and remaining work is just the fix,
- the real issue is contract ambiguity rather than defect,
- evaluation evidence is needed across a wider slice,
- or migration/rollback risk dominates the repair path.

### Common next modes

- Routine Implementer
- Contract Builder
- Quality Evaluator
- Migration Operator

### Typical risks / failure modes

- patching symptoms,
- weak reproduction discipline,
- misreading environmental evidence,
- or overfitting a fix to one observed manifestation.

## 6. Migration Operator
### Purpose

Execute or prepare rollout-sensitive transitions where sequencing, compatibility, reversibility, and operational safety matter.

### When to use

Use Migration Operator when the work involves controlled transition rather than ordinary implementation.

Typical situations:

- schema change,
- data backfill,
- protocol or contract migration,
- storage or infrastructure transition,
- staged cutover,
- rollback planning,
- or compatibility-window management.

### Typical Layer A signals

Common signals include:

- `intent = migrate`, or another intent with migration-shaped mechanics,
- `blast_radius = subsystem`, `cross_service`, or `platform`,
- `reversibility = hard` or `irreversible`,
- `sensitivity = data_integrity`, `security`, or `compliance`,
- `validation_burden = production_confirmation_required` or rehearsal-heavy testing,
- dependency complexity often `cross_service` or `external_or_multi_party`.

### Primary working posture

Migration Operator is control-first and sequencing-aware.

The agent should:

- define ordered stages,
- preserve compatibility where necessary,
- plan rehearsal and rollback,
- surface irreversible points,
- specify go/no-go checks,
- and avoid casual execution on risky transitions.

### Primary outputs

Typical outputs:

- migration plan,
- stage or phase breakdown,
- compatibility notes,
- rollback plan,
- cutover checklist,
- rehearsal evidence,
- controlled implementation slices.

### Allowed autonomy pattern

Usually lower autonomy than ordinary implementation. High-risk migrations should often run inside stronger Layer C governance overlays and may require explicit approval states in Layer D.

### Typical validation style

Validation often relies on:

- migration rehearsal,
- compatibility checks,
- staged rollout signals,
- manual verification,
- and explicit go/no-go criteria.

### Common reroute triggers

Reroute away from Migration Operator when:

- the risky transition has been fully decomposed and local slices become standard implementation,
- the dominant remaining problem is contract clarification,
- or evidence production becomes the main task.

### Common next modes

- Routine Implementer
- Contract Builder
- Quality Evaluator

### Typical risks / failure modes

- insufficient rollback planning,
- hidden coupling across services,
- underestimating irreversibility,
- compressing too many risky steps into one move,
- or treating migration as ordinary coding.

## 7. Optimization Tuner
### Purpose

Improve measurable performance, efficiency, latency, throughput, resource usage, or cost when tuning rather than raw implementation dominates the slice.

### When to use

Use Optimization Tuner when the system works functionally but can be improved against measurable technical objectives.

Typical situations:

- latency reduction,
- throughput increase,
- token or inference cost reduction,
- cache strategy tuning,
- query performance work,
- resource efficiency changes.

### Typical Layer A signals

Common signals include:

- `intent = optimize`,
- uncertainty often `local_ambiguity` or `design_heavy` around the best tuning path,
- validation burden often `offline_eval_required` or benchmark-heavy checks,
- feedback cadence may be medium or slow,
- the solution may be local even when evidence collection is broader.

### Primary working posture

Optimization Tuner is profile-measure-adjust-repeat.

The agent should:

- define the target metric,
- establish a baseline,
- identify candidate levers,
- run disciplined experiments,
- compare deltas against baseline,
- and guard against regressions in non-target dimensions.

### Primary outputs

Typical outputs:

- benchmark plan,
- baseline measurements,
- tuned implementation,
- comparison report,
- recommendation on whether the change is worth adopting.

### Allowed autonomy pattern

Moderate autonomy with a strong requirement for measurable evidence. Tuning without baseline or without comparison discipline is not acceptable.

### Typical validation style

Validation is generally:

- benchmark-driven,
- profile-driven,
- experiment-based,
- or threshold-based.

### Common reroute triggers

Reroute away from Optimization Tuner when:

- the real blocker is not tuning but contract ambiguity,
- quality evaluation rather than system performance becomes dominant,
- the work turns into a migration,
- or the change becomes ordinary implementation after the key decision is made.

### Common next modes

- Routine Implementer
- Quality Evaluator
- Contract Builder
- Migration Operator

### Typical risks / failure modes

- optimizing the wrong metric,
- comparing against unstable baselines,
- hidden regressions,
- insufficient experimental control,
- or confusing quality tuning with performance tuning.

## 8. Quality Evaluator
### Purpose

Produce or interpret evidence about output quality when correctness cannot be established by ordinary tests alone.

### When to use

Use Quality Evaluator when the main problem is epistemic: how to know whether the system is good enough.

Typical situations:

- retrieval quality evaluation,
- ranking quality comparison,
- segmentation quality assessment,
- classifier behavior analysis,
- threshold definition,
- benchmark or evaluation harness work,
- evaluation-driven acceptance decisions.

### Typical Layer A signals

Common signals include:

- `validation_burden = offline_eval_required` or `partial_signals_only`,
- intent may be `research`, `optimize`, `implement`, or `review`,
- uncertainty may remain moderate even with a known implementation path,
- observability of correctness is weaker than normal testable software behavior.

### Primary working posture

Quality Evaluator is evidence-design and evidence-interpretation first.

The agent should:

- define evaluation questions,
- identify or design benchmarks,
- choose slices or comparison sets,
- run comparisons,
- interpret ambiguous signals carefully,
- and state confidence and limitations explicitly.

### Primary outputs

Typical outputs:

- evaluation plan,
- metric definitions,
- benchmark or slice design,
- evaluation results,
- recommendation with threshold reasoning,
- acceptance or rejection rationale.

### Allowed autonomy pattern

Moderate autonomy. Evaluation usually benefits from explicit review because it shapes acceptance thresholds and can hide assumptions.

### Typical validation style

Validation is based on:

- benchmark design quality,
- metric validity,
- result interpretation,
- consistency across slices,
- and clarity about uncertainty and limitations.

### Common reroute triggers

Reroute away from Quality Evaluator when:

- the evidence is sufficient and the remaining work is straightforward implementation,
- the core task becomes research or contract definition,
- or migration/rollout mechanics become dominant.

### Common next modes

- Routine Implementer
- Contract Builder
- Research Scout
- Migration Operator

### Typical risks / failure modes

- weak benchmark design,
- optimizing to the eval instead of the true objective,
- false precision,
- unexamined slice bias,
- or overstating confidence from partial signals.

## Routing guidance from Layer A to Layer B

This section provides routing guidance, not a rigid deterministic state machine.

## Core routing logic
### 1. Start from the dominant question

Ask which of these is most true **now**:

- Do we need to **discover**?
- Do we need to **bound the contract**?
- Do we need to **execute directly**?
- Do we need to **diagnose**?
- Do we need to **stage a risky transition**?
- Do we need to **optimize against a measurable technical target**?
- Do we need to **produce quality evidence**?

That question usually determines the initial Layer B mode.

### 2. Use Layer A signals as routing constraints

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

### 3. Prefer the dominant mode, not a blended label

Do not invent composite labels such as:

- `research-plus-implementation`,
- `debug-plus-review`,
- `migration-plus-feature`.

Pick the dominant current mode, then represent other concerns through:

- reroute triggers,
- Layer C overlays,
- Layer C workstream containers,
- and Layer D state/phase.

## Practical mapping matrix

| Dominant condition now | Typical Layer A pattern | Route to Layer B mode |
|---|---|---|
| Solution space is still being discovered | high uncertainty, low spec maturity, low knowledge locality | Research Scout |
| Objective is known but contract is still forming | scoped problem, draft contract, local ambiguity or design-heavy | Contract Builder |
| Clear bounded implementation slice | implementation-ready, known pattern, strong tests | Routine Implementer |
| Structural cleanup under invariants | intent=refactor, behavior-preserving, regression checkable | Refactor Surgeon |
| Failing behavior with unknown root cause | intent=debug, repro/hypothesis loop needed | Debug Investigator |
| Compatibility/cutover/rollback dominates | migrate intent or migration-shaped governance profile | Migration Operator |
| Measurable technical tuning dominates | optimize intent, benchmark-based improvement target | Optimization Tuner |
| Output quality evidence dominates | offline eval required, weak ordinary correctness signal | Quality Evaluator |

## Secondary routing rules
### Rule A -- Specification maturity overrides raw intent

If a task says `implement` but specification maturity is still `scoped_problem` or `draft_contract`, implementation is not yet the correct operating mode. Prefer **Contract Builder** first.

### Rule B -- Diagnosis overrides direct fix execution

If a bug fix is requested but the root cause is still unknown, prefer **Debug Investigator** over direct implementation.

### Rule C -- Validation burden can override execution mode

If correctness cannot be established by ordinary tests, reroute toward **Quality Evaluator** or, for rollout-sensitive changes, **Migration Operator**.

### Rule D -- Governance can constrain but not redefine the mode

High-risk work does not automatically create a new Layer B mode. It may keep the same mode while adding Layer C control overlays and stricter Layer D checkpoints.

### Rule E -- Horizon affects containment, not atomic mode

If the work is multi-PR or high-handoff, that often justifies a Layer C workstream container such as **Feature Cell**, but the current Layer B mode should still reflect the dominant slice: Research Scout, Contract Builder, Routine Implementer, and so on.

## Reclassification and transition rules

Layer B modes should be expected to change over time.

## Transition principles
### 1. Reclassification is normal

Tasks and workstreams mature. A task that begins in uncertainty reduction may later become execution-ready. A work item that starts as implementation may be reclassified if hidden ambiguity or evaluation difficulty appears.

### 2. Reclassification should be evidence-based

Do not reroute casually. A mode change should normally be triggered by one of:

- new ambiguity discovered,
- contract freeze achieved,
- root cause isolated,
- evidence burden increased,
- governance risk surfaced,
- or horizon expansion.

### 3. Prefer early reroute over late failure

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

Layer C contains overlays and containers. Layer B modes may be modified or wrapped by them, but they should not be collapsed into them.

## Review Gatekeeper as overlay

Review Gatekeeper should usually be modeled as a **reviewer/control overlay** rather than an atomic operating mode.

Use it when the primary requirement is:

- critique,
- policy interpretation,
- approval review,
- architecture review,
- or conformance checking.

In practice, Review Gatekeeper often attaches to another mode by constraining continuation or by defining who must sign off.

## High-control governance overlays

High-control overlays tighten:

- checkpoint requirements,
- approval requirements,
- rollback expectations,
- traceability discipline,
- and amendment rules.

They do not necessarily change the underlying Layer B mode.

Examples:

- Migration Operator with explicit approval overlay,
- Debug Investigator in incident-like conditions with stricter control,
- Contract Builder under design review checkpoints.

## Feature Cell as workstream container

Feature Cell should be modeled as a **long-horizon workstream container**, not as a Layer B peer.

Use it when:

- the horizon is multi-step or multi-PR,
- handoff/resume discipline matters,
- several Layer B modes will likely occur over time,
- planning, tracking, and traceability are required.

A Feature Cell may contain a sequence such as:

- Research Scout,
- Contract Builder,
- Routine Implementer,
- Quality Evaluator,
- Migration Operator,

without contradiction.

## Relationship to Layer D

Layer D controls whether work may proceed, pause, wait for approval, or finish. Layer B controls how the agent should work inside that control state.

## The separation rule

Do not encode Layer B semantics into Layer D state names.

Examples:

- `active` does not mean Routine Implementer,
- `checkpoint` does not mean Contract Builder,
- `validating` does not mean Quality Evaluator,
- `awaiting_approval` does not mean Review Gatekeeper.

These remain distinct layers.

## Examples
### Contract Builder across lifecycle states

A contract-definition slice may look like:

- `state = active`, `phase = contract_drafting`
- later `state = checkpoint`, `phase = tradeoff_review`
- later `state = active`, `phase = contract_finalization`

The mode remains Contract Builder while control status changes.

### Migration Operator across lifecycle states

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
  name: contract_builder | research_scout | routine_implementer | refactor_surgeon | debug_investigator | migration_operator | optimization_tuner | quality_evaluator
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
## Example 1 -- Small local feature slice
### Layer A snapshot

- intent: implement
- uncertainty: known_pattern
- dependency_complexity: few_local_dependencies
- knowledge_locality: mostly_local
- specification_maturity: implementation_ready
- validation_burden: tests_strong_confidence
- blast_radius: local
- execution_horizon: one_shot

### Layer B result

**Routine Implementer**

### Notes

No Layer C workstream container is needed. Lifecycle state is likely `active` with `phase = coding`.

## Example 2 -- Feature request with unclear behavior
### Layer A snapshot

- intent: implement
- uncertainty: design_heavy
- knowledge_locality: scattered_internal
- specification_maturity: scoped_problem
- validation_burden: partial_signals_only
- execution_horizon: multi_pr
- handoff need: high

### Layer B result now

**Contract Builder**

### Layer C note

Because the horizon is multi-PR and handoff need is high, wrap the work in a **Feature Cell** container.

### Likely sequence

Contract Builder -> Routine Implementer -> Quality Evaluator

## Example 3 -- Bug with unknown root cause
### Layer A snapshot

- intent: debug
- uncertainty: local_ambiguity
- knowledge_locality: scattered_internal
- specification_maturity: frozen_contract for expected behavior
- validation_burden: tests_strong_confidence if repro exists
- blast_radius: subsystem

### Layer B result

**Debug Investigator**

### Likely transition

Once the cause is isolated, reroute to **Routine Implementer** for the fix.

## Example 4 -- Risky schema transition
### Layer A snapshot

- intent: migrate
- dependency_complexity: cross_service
- validation_burden: production_confirmation_required
- blast_radius: cross_service
- reversibility: hard
- sensitivity: data_integrity
- approval_requirement: explicit_gate

### Layer B result

**Migration Operator**

### Layer C / D note

Apply stronger governance overlays and expect lifecycle states such as `checkpoint`, `awaiting_approval`, and `validating` during rollout.

## Example 5 -- Retrieval quality improvement slice
### Layer A snapshot

- intent: optimize
- uncertainty: local_ambiguity
- validation_burden: offline_eval_required
- knowledge_locality: mostly_local
- artifact_type: eval_report

### Layer B result now

**Quality Evaluator** or **Optimization Tuner**, depending on the dominant question.

### Decision rule

- If the main task is experiment design, benchmark construction, and interpretation, choose **Quality Evaluator**.
- If the main task is measurable system tuning against an existing benchmark and target metric, choose **Optimization Tuner**.

## Adoption guidance
### Start with the canonical eight modes

Do not add more Layer B modes at first. Use the eight canonical modes and rely on Layer C overlays and containers before inventing additional work modes.

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
- it cannot be represented by current modes plus Layer C overlays/containers,
- and operators can select it consistently.

### Keep mode definitions operational

A Layer B mode definition should always be useful at execution time. If a section cannot guide routing, expected outputs, or reroute behavior, it is probably too abstract.

## Final recommendation

Layer B should remain a compact catalog of **atomic operating modes** with these properties:

- downstream from Layer A,
- independent from Layer C overlays and containers,
- independent from Layer D lifecycle state,
- current-state rather than permanent identity,
- and explicit about outputs, validation, and reroute triggers.

The canonical set should remain:

- Research Scout
- Contract Builder
- Routine Implementer
- Refactor Surgeon
- Debug Investigator
- Migration Operator
- Optimization Tuner
- Quality Evaluator

This is the right level for answering:

> Given the current classification snapshot, how should the agent work now?
