# Layer C: Overlays and Containers for Agentic Work
## Status

Draft v1.1

## Purpose

This document defines **Layer C** in the layered model of agentic work: the layer that records the **control regime** and **orchestration wrapper** under which work proceeds, without recording the current lifecycle gate or status.

Layer C answers questions such as:

- what additional control regime applies to this work slice or workstream,
- whether reviewer-mediated continuation is required,
- whether governance is escalated above baseline,
- whether the work is wrapped as a long-horizon workstream,
- and what minimal operating package is implied by that wrapper.

Layer C is intentionally downstream from:

- **Layer A**, which describes the current work slice,
- **Layer B**, which describes how the agent should work now,
- and upstream-adjacent to **Layer D**, which records the current lifecycle gate or control status.

The core modeling rule is:

> Layer C owns the control regime and orchestration wrapper. Layer D owns the current gate or status inside that regime.

This separation keeps the ontology clean. A work item can therefore be represented as, for example:

- **Layer A**: `design_heavy`, `scoped_problem`, `multi_pr`, `high_handoff_need`
- **Layer B**: `contract_builder`
- **Layer C**: `feature_cell` container plus `review_gatekeeper` overlay
- **Layer D**: `checkpoint`, `phase = contract_review`

That is cleaner than collapsing work shape, operating posture, governance, and lifecycle into a single overloaded archetype or state.

## Position in the overall layered model

The intended stack is:

### Layer A -- Classification snapshot

Orthogonal descriptors of the current work slice.

Typical concerns include:

- intent,
- uncertainty,
- dependency complexity,
- knowledge locality,
- specification maturity,
- validation burden,
- blast radius,
- reversibility,
- sensitivity,
- approval requirement,
- execution horizon,
- handoff / resumability need.

Layer A answers:

> What is the current shape of this work slice?

### Layer B -- Atomic operating mode

The current answer to:

> How should the agent work now?

Examples:

- `research_scout`
- `contract_builder`
- `routine_implementer`
- `refactor_surgeon`
- `debug_investigator`
- `migration_operator`
- `optimization_tuner`
- `quality_evaluator`

Layer B is current-state routing, not permanent task identity.

### Layer C -- Overlays and containers

Structures that **modify, constrain, or wrap** work without changing the underlying task classification or current operating mode.

Canonical examples:

- `review_gatekeeper`
- `governance_escalation`
- `feature_cell`

Layer C answers:

> Under what control regime and orchestration wrapper is this work proceeding?

### Layer D -- Lifecycle control plane

Small shared lifecycle state plus workflow-local `phase`.

Examples:

- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

Layer D answers:

> What is the current execution-control status of this task or workstream?

## Why Layer C exists

Without a distinct Layer C, teams usually drift into one of four failure modes.

### Failure mode 1 -- governance becomes a fake operating mode

Reviewer-mediated continuation, approval obligations, or heightened control are modeled as if they were delivery modes.

Examples:

- treating `review_gatekeeper` as if it were a peer of `routine_implementer`,
- treating approval-heavy migration work as if the mode itself were "approval mode,"
- inventing extra Layer B modes to encode control rather than behavior.

### Failure mode 2 -- long-horizon orchestration becomes a fake task type

A workstream wrapper such as `feature_cell` is treated as if it were the same kind of thing as a problem-solving posture.

That collapses multi-slice orchestration into a single task identity and makes it harder to see the current operating mode.

### Failure mode 3 -- lifecycle state is overloaded with governance meaning

Teams start using lifecycle state names as substitutes for regime semantics.

Examples:

- assuming `checkpoint` means architecture review,
- assuming `awaiting_approval` means migration approval,
- assuming `validating` implies evaluation work.

Those states answer control-plane questions, not policy or wrapper questions.

### Failure mode 4 -- organization-specific process leaks into the core ontology

Concrete reviewer roles, packet formats, and approval mechanics are hard-coded into the shared conceptual model.

That reduces portability and causes the ontology to drift toward one local workflow implementation.

Layer C exists to avoid these failures.

It gives governance modifiers and orchestration wrappers their own layer, while preserving a minimal shared core that can later reference local policy artifacts.

## Core contract with Layer D

This boundary is strict.

### Layer C owns

- the **control regime** under which work proceeds,
- whether review obligations exist,
- whether approval obligations exist,
- whether elevated traceability or rollback evidence is required,
- whether work is wrapped as a long-horizon workstream,
- and what minimal operating package that wrapper typically implies.

### Layer D owns

- whether work is currently `draft`, `active`, `blocked`, `checkpoint`, `awaiting_approval`, `validating`, `complete`, or `cancelled`,
- the current workflow-local `phase`,
- and adjacent control-plane fields such as `next_step`, `blocking_reason`, `checkpoint_reason`, `approval_ref`, or `evidence_refs`.

### Consequence of the boundary

Layer C may influence how Layer D states are entered or exited, but it must not re-encode Layer D state semantics inside Layer C.

Therefore:

- `review_gatekeeper` is **not** the same thing as `checkpoint`,
- `governance_escalation` is **not** the same thing as `awaiting_approval`,
- `feature_cell` is **not** a lifecycle state,
- and Layer C should not contain transition labels such as `checkpoint_then_continue` or `awaiting_signoff_now`.

Layer C records regime and wrapper semantics. Layer D records current gate/status.

## Design principles
### 1. Control-regime only

Layer C should express how work is constrained or wrapped, not the current execution-control status.

### 2. Downstream, not descriptive

Layer C constructs are selected from Layer A signals and current Layer B context. They are downstream routing conclusions, not Layer A descriptors.

For example:

- `approval_requirement = explicit_gate` does not itself mean `governance_escalation`,
- `execution_horizon = multi_pr` does not itself mean `feature_cell`,
- `intent = review` does not itself mean `review_gatekeeper`.

Those are Layer C decisions.

### 3. Overlays modify; containers wrap

Layer C has two internal families:

- **overlays** modify control or governance expectations,
- **containers** wrap work across time when long-horizon orchestration is needed.

These should remain distinct.

### 4. Scope must be explicit

Every Layer C construct should declare whether it applies at:

- **slice scope** -- the current task slice,
- **workstream scope** -- the longer-running wrapper around multiple slices.

This matters because the same workstream may contain:

- a workstream-level `feature_cell`,
- a workstream-level `governance_escalation`,
- and a slice-level `review_gatekeeper` only on a particular design or acceptance slice.

### 5. Keep the canonical set small

Do not expand Layer C unless a repeated real distinction materially changes governance or orchestration in a way the current model cannot express.

### 6. Separate shared semantics from local policy

The shared Layer C model should define:

- canonical construct identity,
- abstract obligations,
- scope and inheritance,
- and optional references to policy/profile artifacts.

The shared core should not hard-code every local reviewer role, packet format, or approval mechanic.

### 7. Prefer composition over ontology growth

If work can be modeled as:

- Layer A snapshot,
- one current Layer B mode,
- one container,
- zero or more overlays,
- and one Layer D state plus local `phase`,

then do that instead of inventing a new Layer C construct.

### 8. Artifact expectations are implied defaults, not identity

A construct may imply a typical operating package, but that package is not the same thing as the construct's semantic identity.

For example, `feature_cell` is a long-horizon workstream wrapper. It typically implies workstream cards, task links, milestones, and handoff notes, but those artifacts do not define the construct itself.

## Scope and non-scope
## In scope

Layer C defines:

- the canonical set of overlays and containers,
- their semantic meaning,
- their scope,
- their abstract obligations,
- composition and precedence rules,
- typical artifact expectations,
- routing guidance from Layer A and Layer B,
- and a compact schema for representing regime and wrapper state.

## Out of scope

Layer C does **not** define:

- Layer A classification axes,
- Layer B operating modes,
- Layer D lifecycle states,
- detailed workflow-local phases,
- full organization-specific approval mechanics,
- product/business state machines,
- or project-management methodology beyond the minimum implied by a container.

## Internal structure of Layer C

Layer C consists of:

## 1. Overlays

An **overlay** changes the control regime under which work proceeds.

Typical effects:

- review is required before continuation,
- approval is required before certain actions,
- evidence expectations are elevated,
- traceability discipline is elevated,
- rollback or recovery evidence is required.

An overlay does not replace the current Layer B mode and does not itself say which Layer D state is currently active.

## 2. Containers

A **container** wraps work across time when the work is multi-slice, multi-PR, long-running, or high-handoff.

Typical effects:

- workstream-level visibility is required,
- linked task slices are expected,
- milestone tracking becomes meaningful,
- resumability and handoff discipline matter,
- workstream-scope lifecycle may need to be tracked alongside task-scope lifecycle.

A container is not a Layer B mode and not a Layer D state.

## Scope model: slice vs workstream

Layer C v1.1 introduces explicit scope.

### Slice scope

A construct with `scope = slice` applies to the current task slice only.

Use this when:

- a specific slice needs review,
- one migration step needs elevated control,
- one acceptance slice requires a particular evidence obligation.

### Workstream scope

A construct with `scope = workstream` applies across a longer-running `feature_cell` or equivalent workstream.

Use this when:

- the whole workstream is long-horizon,
- the whole workstream is under elevated governance,
- the workstream as a whole carries stronger traceability or approval obligations.

### Inheritance

Workstream-scope overlays may influence child slices, but inheritance should be explicit.

Recommended fields:

- `inherits_to_children: true | false`
- optional `applies_to: all_slices | selected_slices`

Guidance:

- use inheritance when the control regime truly applies across the whole workstream,
- avoid implicit inheritance when only selected slices need the overlay,
- prefer explicit local overlays on child slices when the obligation is episodic or local.

### Dual-scope modeling

When `feature_cell` is present, it is often correct to track:

- a **workstream-scope Layer C container**,
- zero or more **workstream-scope overlays**,
- and separate **slice-scope overlays** on specific tasks.

This aligns with Layer D's ability to record lifecycle at both task and workstream scope without inventing new state vocabularies.

## Canonical Layer C constructs

Layer C v1.1 standardizes on exactly three canonical constructs:

### Overlays

1. `review_gatekeeper`
2. `governance_escalation`

### Container

3. `feature_cell`

### Backward compatibility note

The earlier label `high_control_governance` should be treated as a deprecated alias for `governance_escalation`.

Reason:

- `governance_escalation` more clearly communicates that the overlay is a downstream control wrapper,
- while leaving the raw Layer A governance drivers visible rather than flattening them into one opaque "high risk" label.

## Construct definitions
## 1. `review_gatekeeper`
### Definition

A reviewer-mediated control overlay that requires findings, proposals, evidence, or outputs to be interpreted, critiqued, or dispositioned by a reviewer before continuation under certain conditions.

### What it changes conceptually

This overlay introduces a regime in which continuation depends on review-mediated judgment rather than purely autonomous progression.

It is appropriate when the key issue is not raw execution risk alone, but the need for:

- critique,
- architecture review,
- findings review,
- conformance checking,
- recommendation review,
- or acceptance interpretation.

### Typical operational obligations

Typical abstract obligations include:

- `review_required = true`
- elevated `evidence_required`
- optional `approval_required` when review also carries signoff implications

It may also imply that summaries, findings packets, or recommendation packets should be prepared, but the exact packet format should live in a policy/profile reference rather than in the portable core schema.

### Typical artifact expectations

Depending on context, this overlay commonly implies:

- findings summary,
- option comparison,
- architecture note,
- acceptance summary,
- evidence references.

### When to apply

Common triggers include:

- Layer A indicates `intent = review`,
- validation evidence exists but needs human interpretation,
- meaningful design trade-offs must be reviewed,
- policy or architecture review is required,
- acceptance depends on judgment rather than a purely mechanical threshold.

### What it does not mean

It does **not** mean the work is currently in `checkpoint`.

It often leads to `checkpoint`, and sometimes to `awaiting_approval`, but the overlay remains true across multiple Layer D states.

## 2. `governance_escalation`
### Definition

A governance overlay indicating that work is proceeding under stricter-than-baseline control obligations.

### What it changes conceptually

This overlay does **not** replace the underlying Layer A governance fields. Instead, it records the downstream conclusion that the current slice or workstream should proceed under an elevated governance regime.

This is the correct place to say that control is stricter than baseline while preserving the underlying reasons in Layer A.

### Typical Layer A drivers

Common drivers include:

- large `blast_radius`,
- `reversibility = hard` or `irreversible`,
- `sensitivity` involving data integrity, security, privacy, or public contracts,
- `approval_requirement = explicit_gate` or equivalent,
- rollout-sensitive or migration-sensitive transitions.

### Typical operational obligations

Typical abstract obligations include:

- `approval_required = true`
- elevated or strict `traceability_level`
- `rollback_evidence_required = true`
- elevated `evidence_required`

The exact signoff roles, packet forms, or go/no-go mechanics should be referenced via policy/profile artifacts rather than embedded into the shared core.

### Typical artifact expectations

Depending on context, this overlay commonly implies:

- readiness summary,
- risk summary,
- rollback or recovery notes,
- evidence references,
- decision log entries,
- explicit approval packet references.

### When to apply

Use this overlay when the work needs stronger control than the default autonomous/checkpoint baseline.

Especially common with:

- migrations,
- cutovers,
- cross-service contract changes,
- destructive or irreversible data changes,
- security-sensitive work,
- formally gated rollout or closure.

### What it does not mean

It does **not** mean the work is currently `awaiting_approval`.

It frequently increases the likelihood of `checkpoint`, `awaiting_approval`, and `validating`, but those remain Layer D states.

## 3. `feature_cell`
### Definition

A long-horizon workstream container used when the work extends across multiple slices, requires resumability, or needs explicit coordination over time.

### What it changes conceptually

This construct introduces a workstream wrapper around multiple task slices.

It means the work should no longer be treated as a one-shot task. Instead, it should be handled as a coordinated workstream that may pass through several Layer B modes and multiple Layer D states across time.

### Typical Layer A drivers

Common drivers include:

- `execution_horizon = multi_pr`, `long_running_program`, or equivalent,
- high handoff / resumability need,
- multiple expected operating-mode transitions,
- milestone tracking and workstream-level visibility requirements.

### Typical operational obligations

Typical implications include:

- maintain workstream-level visibility,
- link task slices to workstream context,
- preserve decision history,
- preserve resumability and handoff clarity,
- define sparse but explicit HITL points,
- and, where useful, track workstream-scope lifecycle alongside task-scope lifecycle.

### Typical artifact expectations

A `feature_cell` commonly implies a minimal operating package such as:

- workstream card,
- linked task cards,
- milestone list,
- decision log,
- handoff notes,
- declared HITL points,
- evidence references.

These are defaults of the operating package, not the semantic identity of the container.

### What it does not mean

It does **not** mean any particular Layer B mode or Layer D state.

A `feature_cell` may contain, over time:

- `contract_builder`,
- `routine_implementer`,
- `quality_evaluator`,
- `migration_operator`,
- and other Layer B modes,

without contradiction.

It also does not create a second lifecycle vocabulary. It creates a second **scope** at which the same Layer D vocabulary may be applied.

## Composition and precedence rules

Layer C constructs may co-exist.

To keep v1.1 operationally simple, use the following rules.

### 1. At most one container per scope

For v1.1, allow at most one container at a given scope.

Examples:

- one workstream-level `feature_cell` is allowed,
- do not stack multiple containers at the same scope,
- child slices under the same workstream normally do not need their own separate container unless there is a strong reason.

### 2. Overlays may stack

Multiple overlays may apply simultaneously.

Examples:

- `feature_cell` at workstream scope,
- `governance_escalation` at workstream scope,
- `review_gatekeeper` on one slice that needs design review.

### 3. Stricter obligation wins

When overlays conflict, the stricter obligation wins unless an explicit local override is documented.

Examples:

- if one overlay implies elevated evidence and another implies strict traceability, satisfy both,
- if one overlay implies approval and another does not, treat approval as required.

### 4. Overrides must be explicit

If a workstream-level overlay should not apply to a particular slice, record the exception explicitly rather than relying on silent interpretation.

### 5. Layer D remains separate under composition

Even when multiple overlays coexist, Layer D still uses the same shared state vocabulary.

Do not create composite state labels such as:

- `review_checkpoint`
- `approval_migration_gate`
- `feature_cell_active_review`

Those are layer-mixing anti-patterns.

## Selection order from Layer A / Layer B into Layer C

Use the following selection order.

### Step 1 -- Decide whether a container is needed

From Layer A temporal signals, ask:

- is the horizon multi-PR or long-running,
- is handoff/resumability important,
- are several Layer B mode transitions likely,
- does the work need workstream-level visibility?

If yes, apply `feature_cell` at workstream scope.

### Step 2 -- Decide whether the current slice needs a review overlay

Ask:

- does continuation depend on reviewer interpretation,
- does the slice produce findings, architecture options, or acceptance evidence that must be reviewed,
- is the current slice primarily mediated by critique or review?

If yes, apply `review_gatekeeper` at the appropriate scope.

### Step 3 -- Decide whether governance must be escalated

From Layer A governance fields, ask:

- is blast radius large,
- is reversibility hard,
- is sensitivity high,
- is explicit approval required,
- is this a rollout-sensitive or migration-sensitive transition?

If yes, apply `governance_escalation` at the appropriate scope.

### Step 4 -- Let Layer D describe the current gate/status

Once regime and wrapper are determined, use Layer D to say whether work is currently:

- `active`,
- `checkpoint`,
- `awaiting_approval`,
- `validating`,
- and so on.

Do not let Layer C become a hidden state machine.

## Relationship to Layer A

Layer A supplies the raw descriptors that make Layer C decisions possible.

Examples:

- `execution_horizon` and handoff need drive `feature_cell`,
- governance fields such as blast radius, reversibility, sensitivity, and approval requirement drive `governance_escalation`,
- validation burden and artifact type may help determine whether `review_gatekeeper` is needed.

Layer C should not flatten those raw fields into a single opaque label. The reasons should remain visible in Layer A even after a Layer C overlay is applied.

## Relationship to Layer B

Layer B remains the current answer to "how should the agent work now?"

Layer C modifies or wraps that mode without replacing it.

Examples:

- `contract_builder` with `review_gatekeeper`
- `migration_operator` with `governance_escalation`
- `quality_evaluator` with `review_gatekeeper`
- a `feature_cell` containing `contract_builder -> routine_implementer -> quality_evaluator`

A mode may appear inside many different Layer C regimes. Likewise, the same Layer C construct may wrap or constrain many different modes.

## Relationship to Layer D

Layer D remains the source of truth for current control status.

Layer C influences Layer D, but does not replace it.

Examples:

- `review_gatekeeper` may cause work to enter `checkpoint` when findings need review,
- `governance_escalation` may cause `awaiting_approval` before cutover,
- `feature_cell` may justify tracking both task-scope and workstream-scope Layer D records,
- but none of those constructs is equivalent to any one Layer D state.

## Relationship to HITL policy and policy profiles

Layer C should align with a minimal HITL model, but it should not duplicate the lifecycle control plane.

A useful split is:

- Layer C defines the regime: whether review, approval, elevated evidence, or workstream wrapper obligations apply.
- Layer D defines the current gate/status inside that regime.
- HITL policy defines how checkpoint and approval zones are interpreted operationally.

### Policy profile references

Because concrete reviewer roles, packet forms, signoff mechanics, and local control procedures often vary by organization or domain, Layer C should support optional references such as:

- `policy_profile_ref`
- `packet_template_ref`
- `review_protocol_ref`

These references allow the portable Layer C core to remain small while linking to concrete local process definitions.

## Relationship to task and workstream artifacts

Layer C should stay conceptually separate from artifacts, but in practice each construct commonly implies a minimum operating package.

### `review_gatekeeper`

Often implies:

- reviewable summary,
- findings or recommendation packet,
- evidence references,
- decision note.

### `governance_escalation`

Often implies:

- risk summary,
- rollback or recovery notes,
- approval packet reference,
- traceability references,
- decision log entry.

### `feature_cell`

Often implies:

- workstream card,
- linked task cards,
- milestone tracking,
- decision log,
- handoff notes,
- HITL points,
- validation/evidence references.

These are typical defaults, not semantic identity conditions.

## Recommended Layer C schema

The schema should express regime and wrapper semantics, not Layer D state.

```yaml
layer_c:
  overlays:
    - name: review_gatekeeper | governance_escalation
      scope: slice | workstream
      reason: >
        Why this overlay applies.
      entered_at: YYYY-MM-DD
      inherits_to_children: true | false
      applies_to: all_slices | selected_slices | null
      obligations:
        review_required: true | false | null
        approval_required: true | false | null
        evidence_required: standard | elevated | strict | null
        traceability_level: standard | elevated | strict | null
        rollback_evidence_required: true | false | null
      policy_profile_ref: <optional>
      notes: <optional>

  container:
    name: feature_cell | null
    scope: workstream | null
    reason: >
      Why long-horizon wrapping is needed.
    entered_at: YYYY-MM-DD
    operating_package:
      minimal_artifacts:
        - workstream_card
        - task_cards
        - decision_log
        - milestones
        - handoff_notes
        - hitl_points
      policy_profile_ref: <optional>
    notes: <optional>
```

### Schema guidance
### `name`

Required. Use canonical construct names.

### `scope`

Required for every construct. This is the key v1.1 addition.

### `reason`

Required. State why the construct applies in this case.

### `inherits_to_children`

Recommended for workstream-scope overlays.

### `applies_to`

Useful when the overlay does not apply uniformly to all child slices.

### `obligations`

Required for overlays. Keep these abstract and portable.

### `policy_profile_ref`

Optional but recommended when the organization has specific reviewer roles, signoff mechanics, or packet templates.

### `operating_package`

Used for containers to record the typical artifacts implied by the wrapper.

## Worked examples
## Example 1 -- Small local implementation task
### Context

- Layer A: low uncertainty, implementation-ready, local blast radius, one-shot horizon
- Layer B: `routine_implementer`
- Layer D: likely `active`, `phase = coding`

### Layer C

```yaml
layer_c:
  overlays: []
  container:
    name: null
```

### Why this is correct

No additional regime or wrapper is needed. The work is well represented by Layer A + Layer B + Layer D alone.

## Example 2 -- Research slice whose findings need review
### Context

- Layer A: exploratory, design-heavy, findings artifact
- Layer B: `research_scout`
- Layer D: `active` during evidence gathering, later `checkpoint` for review

### Layer C

```yaml
layer_c:
  overlays:
    - name: review_gatekeeper
      scope: slice
      reason: findings require review-mediated interpretation before next decision
      entered_at: 2026-03-06
      inherits_to_children: false
      applies_to: null
      obligations:
        review_required: true
        approval_required: false
        evidence_required: elevated
        traceability_level: standard
        rollback_evidence_required: null
      policy_profile_ref: null
  container:
    name: null
```

### Why this is correct

The regime requires review, but the current control state still belongs in Layer D. The same overlay can exist while the slice moves from `active` to `checkpoint`.

## Example 3 -- Ambiguous feature workstream
### Context

- Layer A: implement intent, scoped problem, design-heavy, multi-PR, high handoff need
- Layer B: starts as `contract_builder`, later becomes `routine_implementer`
- Layer D: task-scope and workstream-scope lifecycle may both exist

### Layer C

```yaml
layer_c:
  overlays: []
  container:
    name: feature_cell
    scope: workstream
    reason: multi-PR feature work requires workstream-level coordination and resumability
    entered_at: 2026-03-06
    operating_package:
      minimal_artifacts:
        - workstream_card
        - task_cards
        - decision_log
        - milestones
        - handoff_notes
        - hitl_points
      policy_profile_ref: null
```

### Why this is correct

The long-horizon wrapper belongs in Layer C. It does not replace the current mode and does not define the current lifecycle state.

## Example 4 -- Design slice inside a governed feature workstream
### Context

- Workstream already wrapped as `feature_cell`
- workstream has elevated governance because rollout risk is significant
- current slice needs architecture review
- Layer B: `contract_builder`

### Layer C

```yaml
layer_c:
  overlays:
    - name: governance_escalation
      scope: workstream
      reason: rollout-sensitive feature requires elevated governance across slices
      entered_at: 2026-03-06
      inherits_to_children: true
      applies_to: all_slices
      obligations:
        review_required: null
        approval_required: true
        evidence_required: elevated
        traceability_level: strict
        rollback_evidence_required: true
      policy_profile_ref: policy/governed-feature-v1

    - name: review_gatekeeper
      scope: slice
      reason: architecture trade-offs on this slice require reviewer interpretation
      entered_at: 2026-03-07
      inherits_to_children: false
      applies_to: null
      obligations:
        review_required: true
        approval_required: false
        evidence_required: elevated
        traceability_level: elevated
        rollback_evidence_required: null
      policy_profile_ref: policy/architecture-review-v1

  container:
    name: feature_cell
    scope: workstream
    reason: multi-slice feature workstream
    entered_at: 2026-03-06
    operating_package:
      minimal_artifacts:
        - workstream_card
        - task_cards
        - decision_log
        - milestones
        - handoff_notes
        - hitl_points
      policy_profile_ref: null
```

### Why this is correct

This shows scope-aware composition:

- one workstream container,
- one workstream-level governance overlay,
- one slice-level review overlay.

Layer D still separately records whether the current slice is `active`, `checkpoint`, or later `awaiting_approval`.

## Example 5 -- Risky schema transition
### Context

- Layer A: migrate intent, cross-service dependencies, hard reversibility, explicit approval requirement
- Layer B: `migration_operator`
- Layer D: likely moves through `active -> checkpoint -> awaiting_approval -> validating`

### Layer C

```yaml
layer_c:
  overlays:
    - name: governance_escalation
      scope: slice
      reason: schema transition requires elevated governance due to explicit gate and hard rollback
      entered_at: 2026-03-06
      inherits_to_children: false
      applies_to: null
      obligations:
        review_required: null
        approval_required: true
        evidence_required: strict
        traceability_level: strict
        rollback_evidence_required: true
      policy_profile_ref: policy/migration-governance-v1
  container:
    name: null
```

### Why this is correct

The overlay captures the stricter regime. Layer D captures the current gate/status at each stage of the transition.

## Example 6 -- Evaluation-heavy slice with acceptance review
### Context

- Layer A: offline evaluation required, artifact is eval report
- Layer B: `quality_evaluator`
- Layer D: `validating` during evidence generation, then `checkpoint` for findings review

### Layer C

```yaml
layer_c:
  overlays:
    - name: review_gatekeeper
      scope: slice
      reason: evaluation results require acceptance interpretation before rollout recommendation
      entered_at: 2026-03-06
      inherits_to_children: false
      applies_to: null
      obligations:
        review_required: true
        approval_required: false
        evidence_required: elevated
        traceability_level: standard
        rollback_evidence_required: null
      policy_profile_ref: policy/eval-review-v1
  container:
    name: null
```

### Why this is correct

`quality_evaluator` remains the current mode. Layer D says whether the slice is currently generating evidence or awaiting review. Layer C records the reviewer-mediated regime across both moments.

## Example 7 -- Long-running program with dual-scope lifecycle
### Context

- Layer A: long-running, mixed uncertainty across slices, high handoff need
- Layer B: changes over time across several modes
- Layer C: `feature_cell` plus workstream-scope governance
- Layer D: both workstream-scope and task-scope records may be tracked

### Layer C

```yaml
layer_c:
  overlays:
    - name: governance_escalation
      scope: workstream
      reason: program-level rollout and coordination require elevated governance across milestones
      entered_at: 2026-03-06
      inherits_to_children: true
      applies_to: selected_slices
      obligations:
        review_required: null
        approval_required: true
        evidence_required: elevated
        traceability_level: elevated
        rollback_evidence_required: true
      policy_profile_ref: policy/program-rollout-v1
  container:
    name: feature_cell
    scope: workstream
    reason: long-running program requires resumability, milestone tracking, and linked slices
    entered_at: 2026-03-06
    operating_package:
      minimal_artifacts:
        - workstream_card
        - task_cards
        - decision_log
        - milestones
        - handoff_notes
        - hitl_points
      policy_profile_ref: null
```

### Why this is correct

The workstream wrapper and governance regime sit in Layer C. Workstream-level and slice-level Layer D records may coexist without creating extra lifecycle vocabularies.

## Adoption guidance
### Start with the canonical three constructs

Do not expand Layer C immediately. Use:

- `review_gatekeeper`
- `governance_escalation`
- `feature_cell`

before inventing new constructs.

### Prefer abstract obligations in the shared core

Keep the Layer C schema portable. Put local reviewer roles, packet templates, and signoff mechanics in referenced policy/profile artifacts.

### Use explicit scope every time

In v1.1, scope is not optional. Long-running work becomes much clearer when slice-scope and workstream-scope constructs are distinguished explicitly.

### Keep Layer D clean

Do not encode regime semantics as state labels. If you find yourself inventing composite lifecycle labels, fix Layer C or `phase`, not Layer D.

### Add new Layer C constructs only when all are true

Introduce a new construct only if:

- a recurring distinction cannot be represented by the canonical three,
- the distinction materially changes governance or orchestration,
- multiple operators can apply it consistently,
- and composition with the existing model becomes awkward without it.

## Final recommendation

Layer C v1.1 should be implemented and used as a **small, scope-aware, state-free regime/wrapper layer**.

Its job is not to classify work, choose the current operating posture, or report the current gate/status. Its job is to say:

- what regime constrains continuation,
- what wrapper organizes work across time,
- what abstract obligations follow from that,
- and what minimal operating package is typically implied.

That gives the layered model a clean and durable division of labor:

- **Layer A** describes the work slice,
- **Layer B** chooses the current operating posture,
- **Layer C** records regime and wrapper,
- **Layer D** records the current gate/status.
