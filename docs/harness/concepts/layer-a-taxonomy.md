# Layer A Taxonomy: Orthogonal Classification Axes for Agentic Work
## Status

Draft v1.0

## Purpose

This document defines the **final version of Layer A** in the agentic work model: a compact, orthogonal taxonomy for classifying a unit of work **at a point in time**.

Layer A is intentionally narrow. It does **not** define:

- the current operating mode,
- the lifecycle state,
- the control overlay,
- or the workstream container.

Instead, it describes the current work slice as observed now so that later layers can make routing and governance decisions consistently.

The design goal is to separate:

- **classification** of the work,
- **routing** into an operating mode,
- **overlays / containers** such as review gates or long-horizon orchestration,
- and **lifecycle state** in the control plane.

This keeps the taxonomy stable even when the task changes mode over time.

## Position in the overall model

The intended stack is:

### Layer A -- Classification snapshot

Orthogonal descriptors of the current work slice.

### Layer B -- Atomic operating mode

The current answer to: **how should the agent work now?**

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

Structures that modify or wrap work rather than describing the problem itself.

Examples:

- Review Gatekeeper
- `governance_escalation` overlay
- Feature Cell as long-horizon workstream pattern

### Layer D -- Lifecycle control plane

Small shared state model and local phase information.

Examples:

- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

The critical modeling rule is:

> Layer A describes the work. It does not describe how the agent is currently behaving or what the workflow state machine is doing.
## Why Layer A exists

Without a dedicated classification layer, taxonomy tends to collapse several different things into one bucket:

- work type,
- execution style,
- approval pattern,
- and lifecycle stage.

That creates confusion such as:

- treating `Feature Cell` as if it were the same kind of thing as `Routine Implementer`,
- treating `Review Gatekeeper` as if it were a task type rather than a control overlay,
- or treating temporary work modes as permanent identity labels for a task.

Layer A avoids this by answering only one question:

> What is the current shape of this work slice?

That snapshot can later be used to select an operating mode, apply overlays, escalate controls, or upgrade into a long-horizon container.

## Design principles
### 1. Orthogonality first

Each axis should answer one question only.

If two axes cannot vary independently in plausible cases, the model is probably mixing concepts.

### 2. Snapshot, not destiny

Classification is **current-state descriptive**, not a permanent label.

A work item may start with:

- high uncertainty,
- partial specification,
- and multi-PR horizon,

then later become: work rather than describing the problem itself.

Examples:

- Review Gatekeeper
- `governance_escalation` overlay
- Feature Cell as long-horizon workstream pattern
- low uncertainty,
- implementation-ready,
- and narrow local execution.

The classification snapshot should be allowed to change accordingly.

### 3. Routing is downstream

Layer A should contain the information needed for routing, but not the routing result itself.

For example:

- `specification_maturity = scoped_problem` does **not** mean the task is `Contract Builder`.
- `execution_horizon = multi_pr` does **not** mean the task is `Feature Cell`.

Those are downstream conclusions.

### 4. Minimal stable vocabulary

Every axis should have a small set of values that:

- people can apply consistently,
- meaningfully change downstream behavior,
- and do not require case-specific interpretation every time.

### 5. Keep control-plane state separate

Do not encode routing and workflow semantics into lifecycle states.

`active` and `checkpoint` answer control questions.

They do not replace descriptors such as uncertainty, risk, or validation burden.

### 6. Prefer raw dimensions over flattened composite labels

Avoid a single `risk = high` field as the only representation of control requirements.

Where possible, keep the components visible:

- blast radius,
- reversibility,
- sensitivity,
- approval requirement.

That makes the model easier to reason about and easier to evolve.

## Scope of Layer A

Layer A should classify the **current work slice** along five groups of axes:

1. task classification,
2. problem classification,
3. readiness classification,
4. governance classification,
5. temporal classification.

These groups are practical rather than metaphysical. They exist to keep the model easy to read and easy to apply.

## Final taxonomy
# 1. Task classification

This group answers:

> What kind of work request is this slice concerned with?

These fields describe the **change object and work surface**, not the operating mode.

## 1.1 Intent

What kind of work is being requested?

Allowed values:

- `implement`
- `refactor`
- `debug`
- `research`
- `review`
- `migrate`
- `optimize`

Guidance:

- `implement` -- add or complete intended behavior.
- `refactor` -- change structure while preserving intended behavior.
- `debug` -- diagnose and fix a failure or incorrect behavior.
- `research` -- gather evidence, compare options, reduce uncertainty.
- `review` -- critique, audit, assess, approve, or identify risks.
- `migrate` -- change data, schema, interface, or protocol with transition semantics.
- `optimize` -- improve latency, cost, throughput, memory, or another measurable efficiency target.

Notes:

- `research` does not mean "no implementation will ever happen." It means the current slice is primarily evidence-gathering or uncertainty-reduction.
- `debug` is distinct from `implement` because diagnosis is often the dominant activity even when the final deliverable is a code fix.

## 1.2 Technical surface

Which technical area is primarily involved?

Allowed values:

- `backend`
- `frontend`
- `infra`
- `data`
- `api`
- `schema`
- `ci_cd`
- `docs`
- `ml_pipeline`
- `evaluation`
- `multi_surface`

Guidance:

- Use the dominant surface when one clearly leads.
- Use `multi_surface` when the work is genuinely cross-surface and that distinction matters downstream.

## 1.3 Scope topology

How widely does the requested change reach structurally?

Allowed values:

- `local`
- `cross_module`
- `cross_service`
- `cross_repo`
- `external_boundary`

Guidance:

- `local` -- contained to one small area.
- `cross_module` -- spans multiple modules or packages within one codebase.
- `cross_service` -- changes interactions across services or deployable units.
- `cross_repo` -- requires coordinated changes across repositories.
- `external_boundary` -- affects external integrations, third-party systems, or public boundaries.

## 1.4 Artifact type

What is the dominant output artifact for this slice?

Allowed values:

- `code`
- `tests`
- `design_doc`
- `plan`
- `runbook`
- `migration`
- `eval_report`
- `dashboard_or_metric_config`
- `review_findings`
- `mixed`

Guidance:

This field matters because many work items are "feature work" in a broad sense but produce a non-code artifact first.

Examples:

- a specification slice may primarily produce `design_doc`,
- a quality investigation may primarily produce `eval_report`,
- a risk assessment may primarily produce `review_findings`.

# 2. Problem classification

This group answers:

> What kind of cognition does this slice require?

This is the core of Layer A.

## 2.1 Problem uncertainty

How known is the path to a good solution?

Allowed values:

- `known_pattern`
- `local_ambiguity`
- `design_heavy`
- `research_exploration`
- `open_ended_investigation`

Guidance:

- `known_pattern` -- the solution shape is well understood.
- `local_ambiguity` -- the overall approach is known, but one or more local decisions are unclear.
- `design_heavy` -- the main work is selecting or shaping a design under constraints.
- `research_exploration` -- the work requires option discovery, comparison, and evidence.
- `open_ended_investigation` -- the objective or solution space is still materially unresolved.

Key distinction:

This is **not** the same as specification maturity.

- A task may have `design_heavy` uncertainty even when the problem statement is well scoped.
- A task may have `known_pattern` uncertainty while still having poor requirements.

## 2.2 Novelty

How familiar is the solution pattern in this context?

Allowed values:

- `familiar_pattern`
- `local_variant`
- `unfamiliar_subsystem`
- `new_solution_pattern`
- `unknown_domain`

Guidance:

- `familiar_pattern` -- common, repeated, well-understood pattern.
- `local_variant` -- mostly familiar with localized adaptation.
- `unfamiliar_subsystem` -- known class of work, but not in a familiar subsystem.
- `new_solution_pattern` -- materially different approach is required.
- `unknown_domain` -- the agent or operator lacks meaningful prior pattern familiarity.

Novelty is useful because two tasks with the same uncertainty may differ sharply in routing if one follows a familiar repository pattern and the other does not.

## 2.3 Dependency complexity

How many coupled dependencies must align for this slice to succeed?

Allowed values:

- `self_contained`
- `few_local_dependencies`
- `cross_module`
- `cross_service`
- `external_or_multi_party`

Guidance:

- `self_contained` -- essentially isolated.
- `few_local_dependencies` -- relies on a small number of nearby internals.
- `cross_module` -- several internal modules or packages must coordinate.
- `cross_service` -- service boundaries or deployable systems are involved.
- `external_or_multi_party` -- third parties, external teams, or multi-system dependencies dominate.

Key distinction:

Dependency complexity is **not** the same as knowledge locality.

A task can be structurally cross-service but still be well documented and fully understood locally.

## 2.4 Knowledge locality

Where does the required knowledge live?

Allowed values:

- `fully_local`
- `mostly_local`
- `scattered_internal`
- `external_research_required`
- `tacit_human_required`

Guidance:

- `fully_local` -- the necessary knowledge is in repo-local artifacts.
- `mostly_local` -- repo-local information dominates, with some surrounding context.
- `scattered_internal` -- knowledge is spread across docs, chats, issues, previous PRs, or multiple internal sources.
- `external_research_required` -- external sources are necessary to proceed responsibly.
- `tacit_human_required` -- essential knowledge exists mainly in human judgment or undocumented practice.

This axis is especially important when deciding whether the work should remain agent-driven or should force a human checkpoint.

# 3. Readiness classification

This group answers:

> Is this slice ready for direct execution, or does it still need framing, contract work, or stronger evaluation design?

## 3.1 Specification maturity

How mature is the requested behavior or contract?

Allowed values:

- `vague_idea`
- `scoped_problem`
- `draft_contract`
- `frozen_contract`
- `implementation_ready`

Guidance:

- `vague_idea` -- the request is directionally meaningful but too underspecified to execute.
- `scoped_problem` -- the objective is bounded, but behavior/contract details remain incomplete.
- `draft_contract` -- intended behavior and acceptance direction exist, but some details are still provisional.
- `frozen_contract` -- expected behavior is stable enough to implement against.
- `implementation_ready` -- inputs, outputs, scope, and acceptance criteria are clear enough for execution.

Key distinction:

This field measures **contract maturity**, not whether the solution is intellectually easy.

## 3.2 Validation burden

How hard is it to know that the work is correct?

Allowed values:

- `trivial_local_check`
- `tests_strong_confidence`
- `partial_signals_only`
- `offline_eval_required`
- `production_confirmation_required`

Guidance:

- `trivial_local_check` -- correctness is obvious or directly observable with a simple local check.
- `tests_strong_confidence` -- automated tests provide strong confidence.
- `partial_signals_only` -- tests or checks exist but do not fully confirm success.
- `offline_eval_required` -- a benchmark, comparison, or evaluation artifact is needed.
- `production_confirmation_required` -- some critical confirmation requires rollout or production-like observation.

This axis is critical because tasks often look like implementation but are really evaluation-constrained.

# 4. Governance classification

This group answers:

> How tightly should this slice be controlled?

Do not collapse all governance concerns into one unstructured `risk` field.

## 4.1 Blast radius

If this slice is wrong, how far does the effect propagate?

Allowed values:

- `local`
- `subsystem`
- `cross_service`
- `platform`

Guidance:

- `local` -- small isolated area.
- `subsystem` -- broader but still bounded internal surface.
- `cross_service` -- can affect multiple services or systems.
- `platform` -- can affect shared foundations, broad system behavior, or many downstream consumers.

## 4.2 Reversibility

How easy is it to undo safely?

Allowed values:

- `easy`
- `moderate`
- `hard`
- `irreversible`

Guidance:

This field matters because some high-impact work can still be acceptable under automation if rollback is straightforward, while some moderate-impact work should remain tightly controlled if rollback is hard.

## 4.3 Sensitivity

What kind of failure is most important here?

Allowed values:

- `none`
- `user_visible`
- `data_integrity`
- `security`
- `compliance`

Guidance:

- `none` -- no special sensitivity beyond routine correctness.
- `user_visible` -- incorrect behavior is visible to users or stakeholders.
- `data_integrity` -- corruption, loss, or semantic inconsistency is a core concern.
- `security` -- auth, secrets, privilege, security posture, or attack surface is materially involved.
- `compliance` -- policy, legal, governance, or regulated constraints apply.

## 4.4 Approval requirement

What level of human signoff is required before proceeding or shipping?

Allowed values:

- `none`
- `reviewer`
- `domain_owner`
- `explicit_gate`

Guidance:

- `none` -- no special signoff beyond normal workflow.
- `reviewer` -- standard code/design review is required.
- `domain_owner` -- a responsible owner must approve.
- `explicit_gate` -- a deliberate approval checkpoint is mandatory.

This field is helpful because the same blast radius may require different workflow controls in different organizations.

# 5. Temporal classification

This group answers:

> What is the execution shape of this work over time?

These fields are important because some tasks should be routed into long-horizon structures even when the immediate next step is small.

## 5.1 Execution horizon

How long-running or stateful is the work expected to be?

Allowed values:

- `atomic`
- `multi_step`
- `multi_pr`
- `long_running_program`
- `ongoing_lane`

Guidance:

- `atomic` -- one bounded unit of work.
- `multi_step` -- several coordinated steps but still a short bounded effort.
- `multi_pr` -- likely to span multiple pull requests or handoff points.
- `long_running_program` -- sustained workstream with planning, status, checkpoints, and evidence over time.
- `ongoing_lane` -- recurring maintenance or operational lane rather than a bounded project.

Important note:

This axis may later trigger a container such as `Feature Cell`, but the container itself should not be encoded in Layer A.

## 5.2 Feedback loop speed

How quickly does the environment reveal whether the current step worked?

Allowed values:

- `immediate`
- `medium`
- `slow`
- `rollout_slow`

Guidance:

- `immediate` -- rapid compile/test/local feedback.
- `medium` -- some integration or environment delay.
- `slow` -- feedback requires longer-running setup or evaluation.
- `rollout_slow` -- meaningful evidence arrives only during staged rollout or long-horizon observation.

## 5.3 Handoff / resumability need

How important is durable continuation across sessions, people, or checkpoints?

Allowed values:

- `low`
- `medium`
- `high`

Guidance:

- `low` -- work can be completed in one focused pass.
- `medium` -- continuation artifacts matter but are not dominant.
- `high` -- the work will likely outlive one session or one executor and requires strong handoff discipline.

This field is often the practical signal for whether stronger workstream structure is justified.

## Orthogonality rules

These are the main guardrails that keep the taxonomy clean.

### Rule 1 -- Uncertainty is not specification maturity

- **uncertainty** asks whether the path to a solution is known.
- **specification maturity** asks whether the intended behavior or contract is clearly defined.

Examples:

- A task may be `known_pattern` but only `scoped_problem` if the behavior is still under-specified.
- A task may be `design_heavy` and still have `frozen_contract` if the problem is well defined but the best solution architecture is not yet chosen.

### Rule 2 -- Dependency complexity is not knowledge locality

- **dependency complexity** is structural.
- **knowledge locality** is informational.

Examples:

- A cross-service change may still be fully documented and `mostly_local`.
- A local change may be `tacit_human_required` if critical knowledge exists only in practice.

### Rule 3 -- Validation burden is not risk

- **validation burden** is epistemic: how hard it is to know the change worked.
- **risk** is control-oriented: how costly failure would be.

Examples:

- A low-risk optimization experiment may require offline evaluation.
- A high-risk migration may be easy to validate but hard to roll back.

### Rule 4 -- Execution horizon is not lifecycle state

- **execution_horizon** describes the shape of work over time.
- **lifecycle state** describes current control status such as active, blocked, validating, or awaiting approval.

### Rule 5 -- No axis value may be an operating mode, overlay, or container

The following do **not** belong in Layer A values:

- `Research Scout`
- `Contract Builder`
- `Routine Implementer`
- `Review Gatekeeper`
- `Feature Cell`
- `high_control`

These are routing or governance constructs from later layers.

## What is explicitly out of scope for Layer A

Layer A should not include the following fields.

### Agent configuration fields

Examples:

- role
- autonomy level
- tool authority
- control loop
- instruction regime

These describe how an agent is configured to work, not the work itself.

### Operating mode / archetype fields

Examples:

- Research Scout
- Contract Builder
- Routine Implementer
- Refactor Surgeon
- Debug Investigator
- Migration Operator
- Optimization Tuner
- Quality Evaluator

These are routing outputs.

### Overlays and containers

Examples:

- Review Gatekeeper
- `governance_escalation` overlay
- Feature Cell

These are not task descriptors. They are modifiers or orchestration structures.

### Lifecycle state

Examples:

- draft
- active
- blocked
- checkpoint
- awaiting_approval
- validating
- complete
- cancelled

These belong to the control plane.

## Minimal required subset for v1

If a smaller version is needed, use this required core:

- `intent`
- `problem_uncertainty`
- `dependency_complexity`
- `knowledge_locality`
- `specification_maturity`
- `validation_burden`
- `blast_radius`
- `execution_horizon`

This is the smallest durable subset that still meaningfully affects routing.

Recommended use:

- make the required core mandatory,
- keep other fields optional at first,
- promote optional fields to required only when they repeatedly change routing or governance decisions.

## Compact schema

```yaml
classification_snapshot:
  task:
    intent: implement | refactor | debug | research | review | migrate | optimize
    technical_surface: backend | frontend | infra | data | api | schema | ci_cd | docs | ml_pipeline | evaluation | multi_surface
    scope_topology: local | cross_module | cross_service | cross_repo | external_boundary
    artifact_type: code | tests | design_doc | plan | runbook | migration | eval_report | dashboard_or_metric_config | review_findings | mixed

  problem:
    uncertainty: known_pattern | local_ambiguity | design_heavy | research_exploration | open_ended_investigation
    novelty: familiar_pattern | local_variant | unfamiliar_subsystem | new_solution_pattern | unknown_domain
    dependency_complexity: self_contained | few_local_dependencies | cross_module | cross_service | external_or_multi_party
    knowledge_locality: fully_local | mostly_local | scattered_internal | external_research_required | tacit_human_required

  readiness:
    specification_maturity: vague_idea | scoped_problem | draft_contract | frozen_contract | implementation_ready
    validation_burden: trivial_local_check | tests_strong_confidence | partial_signals_only | offline_eval_required | production_confirmation_required

  governance:
    blast_radius: local | subsystem | cross_service | platform
    reversibility: easy | moderate | hard | irreversible
    sensitivity: none | user_visible | data_integrity | security | compliance
    approval_requirement: none | reviewer | domain_owner | explicit_gate

  temporal:
    execution_horizon: atomic | multi_step | multi_pr | long_running_program | ongoing_lane
    feedback_loop_speed: immediate | medium | slow | rollout_slow
    handoff_need: low | medium | high
```

## Example classification snapshots
### Example 1 -- Small local implementation

```yaml
classification_snapshot:
  task:
    intent: implement
    technical_surface: backend
    scope_topology: local
    artifact_type: code
  problem:
    uncertainty: known_pattern
    novelty: familiar_pattern
    dependency_complexity: self_contained
    knowledge_locality: fully_local
  readiness:
    specification_maturity: implementation_ready
    validation_burden: tests_strong_confidence
  governance:
    blast_radius: local
    reversibility: easy
    sensitivity: none
    approval_requirement: reviewer
  temporal:
    execution_horizon: atomic
    feedback_loop_speed: immediate
    handoff_need: low
```

Interpretation:

This is a strong candidate for a direct execution mode with light controls.

### Example 2 -- Long-running feature at the beginning

```yaml
classification_snapshot:
  task:
    intent: implement
    technical_surface: backend
    scope_topology: cross_module
    artifact_type: design_doc
  problem:
    uncertainty: design_heavy
    novelty: local_variant
    dependency_complexity: cross_module
    knowledge_locality: scattered_internal
  readiness:
    specification_maturity: scoped_problem
    validation_burden: partial_signals_only
  governance:
    blast_radius: subsystem
    reversibility: moderate
    sensitivity: user_visible
    approval_requirement: domain_owner
  temporal:
    execution_horizon: multi_pr
    feedback_loop_speed: medium
    handoff_need: high
```

Interpretation:

This should **not** be represented as "the task is Feature Cell" or "the task is Contract Builder" inside Layer A.

Instead, Layer A says:

- uncertainty is still high enough that direct execution is premature,
- the contract is not yet mature,
- the work has long-horizon shape,
- and handoff discipline matters.

Downstream routing may then decide to:

- start in `Contract Builder`,
- apply stronger checkpoints,
- and wrap the workstream in a `Feature Cell` container later.

### Example 3 -- Migration with strong controls

```yaml
classification_snapshot:
  task:
    intent: migrate
    technical_surface: schema
    scope_topology: cross_service
    artifact_type: migration
  problem:
    uncertainty: local_ambiguity
    novelty: unfamiliar_subsystem
    dependency_complexity: cross_service
    knowledge_locality: mostly_local
  readiness:
    specification_maturity: draft_contract
    validation_burden: production_confirmation_required
  governance:
    blast_radius: cross_service
    reversibility: hard
    sensitivity: data_integrity
    approval_requirement: explicit_gate
  temporal:
    execution_horizon: multi_step
    feedback_loop_speed: slow
    handoff_need: medium
```

Interpretation:

The classification should likely trigger a migration-oriented operating mode and stronger control overlays, but those remain outside Layer A.

### Example 4 -- Research / evaluation slice

```yaml
classification_snapshot:
  task:
    intent: research
    technical_surface: evaluation
    scope_topology: external_boundary
    artifact_type: eval_report
  problem:
    uncertainty: research_exploration
    novelty: new_solution_pattern
    dependency_complexity: external_or_multi_party
    knowledge_locality: external_research_required
  readiness:
    specification_maturity: scoped_problem
    validation_burden: offline_eval_required
  governance:
    blast_radius: local
    reversibility: easy
    sensitivity: none
    approval_requirement: reviewer
  temporal:
    execution_horizon: multi_step
    feedback_loop_speed: slow
    handoff_need: medium
```

Interpretation:

This is primarily an evidence-producing slice rather than an implementation slice.

## How Layer A feeds downstream layers

Layer A is intended to support the following downstream decisions.

### Into Layer B -- atomic operating mode

Examples:

- high uncertainty + low spec maturity may route to `Contract Builder` or `Research Scout`
- low uncertainty + implementation-ready + strong tests may route to `Routine Implementer`
- diagnosis-heavy `debug` work may route to `Debug Investigator`
- heavy evaluation burden may route to `Quality Evaluator`

### Into Layer C -- overlays / containers

Examples:

- high governance requirements may apply stronger approval overlays
- `execution_horizon = multi_pr` plus `handoff_need = high` may justify a long-horizon workstream container such as `Feature Cell`
- high sensitivity may require stricter reviewer overlays

### Into Layer D -- lifecycle / phase handling

Examples:

- partial specification may imply a `draft` or `checkpoint` phase rather than immediate execution
- explicit gates may imply `awaiting_approval`
- production confirmation may imply a `validating` phase

The key modeling rule is:

> Layer A informs these downstream decisions. It does not absorb them.
## Adoption guidance
### Recommended rollout

1. Start with the **minimal required subset**.
2. Capture optional fields only when they materially change behavior.
3. Review real task cards for repeated ambiguity.
4. Promote recurring distinctions into the standard taxonomy only when justified.

### When to add new axes

Add a new field only if all are true:

- the distinction appears repeatedly,
- it changes routing, control, or validation decisions,
- it can be defined clearly,
- and operators can assign it consistently.

### When not to add new axes

Do not add fields merely because they are interesting or theoretically complete.

Layer A should stay compact enough that operators can classify work quickly and consistently.

## Final recommendation

The final taxonomy should remain a **Layer A classification snapshot** with these properties:

- orthogonal,
- current-state descriptive,
- independent from operating mode,
- independent from lifecycle state,
- and expressive enough to drive routing and governance.

The five stable groups are:

1. task classification,
2. problem classification,
3. readiness classification,
4. governance classification,
5. temporal classification.

This is the right place to classify a long-running feature at the beginning as:

- uncertain,
- partially specified,
- multi-PR,
- and `handoff_need = high`,

without prematurely calling it `Contract Builder`, `Feature Cell`, or any other downstream construct.
