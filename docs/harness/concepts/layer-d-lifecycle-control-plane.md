# Layer D: Lifecycle Control Plane for Agentic Work
## Status

Draft v1.1

## Purpose

This document defines **Layer D** in the layered model of agentic work: the minimal shared **lifecycle control plane** used to represent the current execution-control status of a task or workstream slice.

Layer D answers a narrow but operationally important class of questions:

- can the work continue now,
- is it paused,
- is it blocked,
- does it require checkpoint review,
- does it require explicit approval,
- is validation now the dominant activity,
- is the scoped work complete,
- has the work been intentionally cancelled.

Layer D is intentionally small. It exists to standardize **control status** across tasks and workstreams without collapsing the rest of the stack into one overloaded state machine.

In this layered model:

- **Layer A** classifies the current work slice,
- **Layer B** records the current atomic operating mode,
- **Layer C** records the `feature_cell` workstream wrapper and `control_profile` records that define control regime,
- **Layer D** records the current lifecycle gate or control status.

The design target is:

- one **small shared lifecycle model**,
- workflow-local `phase` for detailed progression,
- richer detail in companion fields and linked artifacts,
- strict separation from classification, operating mode, and governance regime.

That pattern is sufficient for routing, HITL orchestration, resumability, workstream visibility, dashboards, and handoff without introducing a giant universal workflow state machine.

## Position in the overall layered model

The intended stack is:

### Layer A -- Classification snapshot

Orthogonal descriptors of the **current work slice**.

Typical questions answered by Layer A:

- what kind of task is this,
- how uncertain is it,
- how mature is the specification,
- how difficult is validation,
- how risky or sensitive is it,
- how long-horizon is the work.

Layer A answers:

> What is the current shape of this work slice?

### Layer B -- Atomic operating mode

The current answer to:

> How should the agent work now?

Examples include:

- Research Scout,
- Contract Builder,
- Routine Implementer,
- Refactor Surgeon,
- Debug Investigator,
- Migration Operator,
- Optimization Tuner,
- Quality Evaluator.

Layer B is current-state routing, not permanent identity.

### Layer C -- Workstream wrapper and control regime

Structures that wrap work across time or impose explicit control obligations without changing the underlying task classification or current operating mode.

Canonical examples include:

- `feature_cell`,
- `control_profile`,
- presets such as `reviewed`, `change_controlled`, and `high_assurance`.

Layer C answers questions such as:

- what additional control regime applies,
- what continuation rules or review constraints are in force,
- whether the work is being wrapped as a long-horizon workstream.

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

This distinction is strict:

- Layer C owns the **control regime** under which work proceeds.
- Layer D owns the **current gate or status** inside that regime.

That means Layer D records whether work is active, paused, blocked, awaiting approval, validating, complete, or cancelled. It does **not** define reviewer roles, approval packet requirements, continuation rules, rollback obligations, or traceability requirements. Those belong to Layer C control profiles and related policy artifacts.

## Why Layer D exists

Without a distinct lifecycle control plane, teams usually drift into one of two bad patterns.

### Failure mode 1 -- giant universal workflow state machine

A single top-level state model tries to encode:

- research,
- contract shaping,
- implementation,
- debugging,
- evaluation,
- migration,
- rollout,
- review,
- and approval behavior

inside one large shared vocabulary.

That usually fails because the same state label starts meaning different things in different workflows. State names become overloaded. Routing becomes fragile. Cross-workflow reporting becomes ambiguous.

### Failure mode 2 -- every workflow invents unrelated top-level states

Each workflow family creates its own incompatible top-level lifecycle model.

That usually causes:

- weak cross-workflow visibility,
- inconsistent dashboard semantics,
- poor handoff readability,
- duplicated orchestration logic,
- confusing HITL behavior,
- and status reports that cannot be compared across work types.

### Target pattern

Layer D exists to avoid both failure modes.

The intended pattern is:

- one minimal universal lifecycle model,
- workflow-local `phase` for detailed progression,
- Layer C control profiles for control modifiers,
- the Layer C `feature_cell` wrapper for long-horizon orchestration,
- companion fields and linked artifacts for evidence and decisions.

This gives the system one shared answer to the control questions that actually need standardization:

- may work continue now,
- must work pause for review,
- must work stop for approval,
- is work blocked,
- is validation now the dominant activity,
- is the scoped work complete,
- has the scoped work been cancelled.

That is enough for a control plane.

## Design principles
### 1. Control-plane only

Layer D is for **execution-control status** only.

It should express whether work may proceed, must pause, is blocked, requires a decision gate, is validating, is complete, or has been cancelled.

It should not encode:

- problem shape,
- operating posture,
- Layer C control-profile identity,
- workstream wrapper identity,
- deep technical microstates,
- product or business workflow transitions.

### 2. One small shared state model

The shared state vocabulary should remain small and stable.

A new universal state should be added only when all are true:

- the distinction appears repeatedly across multiple workflow families,
- it changes routing or governance behavior materially,
- existing states plus `phase` cannot model it clearly,
- operators can apply it consistently.

If the distinction is local, represent it in `phase` or companion fields instead.

### 3. Local `phase` carries workflow detail

Layer D should preserve the pattern:

- **shared state** for control status,
- **local `phase`** for workflow-specific progression.

Examples:

- `state = active`, `phase = contract_drafting`
- `state = active`, `phase = coding`
- `state = validating`, `phase = benchmark_run`
- `state = awaiting_approval`, `phase = cutover_ready`

This is the main mechanism that keeps the ontology compact without losing operational usefulness.

### 4. Keep Layer A out of Layer D

Layer A descriptors such as uncertainty, novelty, dependency complexity, knowledge locality, validation burden, sensitivity, blast radius, and execution horizon remain classification fields.

They may influence Layer D, but they must not be absorbed into it.

### 5. Keep Layer B out of Layer D

Layer B modes answer how the agent should work now. Layer D answers what control status the work is in now.

A mode may appear across several states. A state may host several modes.

### 6. Keep Layer C out of Layer D

Layer C records the control regime and workstream wrapper under which work proceeds. It does not replace lifecycle state.

Examples:

- `checkpoint` is not the same as a reviewed control profile.
- `awaiting_approval` is not the same as a change-controlled or high-assurance control profile.
- `active` inside a `feature_cell` is still just `active`.

### 7. Prefer explicit control boundaries

When work crosses a real control boundary, Layer D should reflect it.

Examples:

- a contract-definition slice reaches trade-off review -> `checkpoint`
- a migration reaches a formal go/no-go boundary -> `awaiting_approval`
- implementation is done and verification now dominates -> `validating`

### 8. Optimize for resumability and handoff

Another agent or human should be able to answer quickly:

- what is happening now,
- why the item is in this state,
- what the next step is,
- what evidence exists,
- what decision is pending,
- what blocks continuation.

A good Layer D record is small, explicit, and legible.

### 9. Separate control status from control regime

This is the key refinement relative to earlier drafts.

Layer D records the **current lifecycle gate or status**.

Layer C records the **governance regime or wrapper** under which that state exists.

That means Layer D may reference review or approval artifacts, but it should not define fields that properly belong to control profiles, such as:

- reviewer role,
- signoff role,
- continuation rule semantics,
- rollback plan requirement,
- traceability requirement,
- approval packet requirement.

Those are Layer C concerns.

## Scope and non-scope
## In scope

Layer D defines:

- the universal lifecycle state set,
- the meaning of each state,
- transition principles,
- the role of workflow-local `phase`,
- alignment with HITL control zones,
- relationship to routing and reclassification,
- relationship to task and workstream artifacts,
- a compact control-plane schema.

## Out of scope

Layer D does **not** define:

- Layer A taxonomy axes,
- Layer B operating mode selection,
- Layer C control-profile or `feature_cell` selection,
- detailed workflow-specific phase machines,
- product or business state transitions,
- organization-specific release methodology,
- deep approval protocol details,
- reviewer/conformance policy semantics.

Those belong elsewhere.

## What Layer D is for

Layer D should be used to represent:

- whether work can continue autonomously,
- whether work is paused for checkpoint review,
- whether explicit approval is required,
- whether work is blocked by an unresolved dependency or issue,
- whether validation is now the dominant activity,
- whether the scoped work is complete or cancelled,
- the current phase label inside that control state.

This makes it suitable for:

- task cards,
- workstream cards,
- routing and escalation logic,
- HITL orchestration,
- dashboards and status reporting,
- resumability and handoff,
- milestone and stage-gate visibility.

## What Layer D is not for

Layer D must **not** be used to encode:

- Layer A descriptors such as uncertainty, novelty, dependency complexity, knowledge locality, validation burden, or execution horizon,
- Layer B modes such as Research Scout, Contract Builder, Routine Implementer, Debug Investigator, Migration Operator, or Quality Evaluator,
- Layer C constructs such as `control_profile` or `feature_cell`,
- deep workflow-specific microstates,
- detailed technical activity labels when `phase` is sufficient,
- product or business state transitions.

The following blurs are explicitly incorrect:

- `checkpoint` != Contract Builder
- `validating` != Quality Evaluator
- `awaiting_approval` != reviewed control context
- `awaiting_approval` != change-controlled or high-assurance control context
- `active` != Routine Implementer
- `feature_cell` != any lifecycle state

## Universal lifecycle states

Layer D standardizes on the following eight universal states:

- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

This is the default shared control-plane vocabulary for both task-scope and workstream-scope lifecycle tracking.

## Why this set is enough

This set is enough because it distinguishes the control questions that matter operationally:

- not started or not yet actionable -> `draft`
- may proceed now -> `active`
- cannot proceed because something prevents progress -> `blocked`
- must pause and summarize before continuation -> `checkpoint`
- must stop until a decision exists -> `awaiting_approval`
- evidence generation and verification now dominate -> `validating`
- scoped work is done -> `complete`
- work has been intentionally terminated -> `cancelled`

Most missing nuance does **not** justify a new universal state. It usually requires:

- a better `phase`,
- a clearer `next_step`,
- a specific `blocking_reason`,
- linked evidence,
- a decision reference,
- or a proper Layer A / B / C record.

## When this set is not enough

The set is insufficient only when there is a recurring control-plane distinction that:

- appears across many workflow families,
- changes automation, routing, or governance behavior,
- cannot be represented by an existing state plus `phase` and companion fields.

That bar should remain deliberately high.

Examples that usually **do not** justify a new universal state:

- `researching`
- `planning`
- `coding`
- `rehearsal`
- `rolling_out`
- `acceptance_review`
- `handoff_ready`
- `findings_packaged`

These are normally better represented as workflow-local `phase` values.

## State definitions
### 1. `draft`
#### Meaning

The work item exists, but active progression has not started or is not yet actionable.

#### Use when

Use `draft` when one or more are true:

- intake is incomplete,
- framing or scoping is still incomplete,
- the work slice is not yet ready for execution,
- the contract is too immature for direct execution,
- the task or workstream exists but has not entered active work.

#### Typical examples

- a newly created task card with unresolved scope,
- a feature slice captured for later framing,
- a workstream created before kickoff,
- an ambiguous request that still needs contract clarification.

#### Notes

`draft` does not mean low importance. It means control status is not yet active.

### 2. `active`
#### Meaning

The agent may continue working within the current scope, mode, authority boundary, and applicable control context.

#### Use when

Use `active` when:

- the next step is executable,
- no current block prevents progress,
- no required checkpoint is active,
- no hard approval gate is active,
- validation is not yet the dominant control activity.

#### Typical examples

- implementing a clear local change,
- conducting approved research,
- drafting a contract,
- isolating a bug cause,
- rehearsing a migration step,
- running a planned evaluation design activity.

#### Notes

`active` is the default autonomous execution state. It says nothing about work type.

### 3. `blocked`
#### Meaning

Progress cannot safely or meaningfully continue because an unresolved dependency, missing input, or external failure prevents continuation.

#### Use when

Use `blocked` when:

- required context is missing,
- another system, team, or artifact is unavailable,
- conflicting instructions prevent safe continuation,
- repeated attempts failed and the next move is not executable,
- an environment or dependency failure prevents progress.

#### Typical examples

- missing logs needed for diagnosis,
- waiting on another team for interface details,
- unresolved contradiction between two specifications,
- environment failure blocking validation.

#### Required companion field

`blocked` should include a `blocking_reason` and, preferably, an `unblock_condition` or concrete dependency reference.

#### Notes

`blocked` is **not** automatically a HITL state. Work may be blocked by infrastructure, missing data, or external dependency without requiring a checkpoint or approval decision.

### 4. `checkpoint`
#### Meaning

The agent must pause, summarize status, and present evidence before continuation.

#### Use when

Use `checkpoint` when:

- a formal review boundary has been reached,
- scope changed materially,
- trade-offs need interpretation,
- evidence is mixed or non-obvious,
- the next step should be reviewed before normal continuation,
- a predefined checkpoint exists in the workflow or container.

#### Typical examples

- a contract draft is ready for review,
- bug investigation found several plausible root causes,
- evaluation results need interpretation,
- a migration rehearsal succeeded and the next step becomes more sensitive.

#### Notes

`checkpoint` is a **pause-and-summarize** state.

It is not inherently a hard approval state. The expected output is a reviewable packet such as:

- current status,
- what changed,
- what was learned,
- current risks,
- recommendation,
- evidence supporting that recommendation.

### 5. `awaiting_approval`
#### Meaning

A human or designated decision authority must approve the next step before continuation may occur.

#### Use when

Use `awaiting_approval` when:

- the next step is high-risk,
- migration, cutover, rollout, or irreversible action is proposed,
- security-sensitive or externally significant action requires signoff,
- cross-service or public contract change requires formal approval,
- closure or acceptance requires explicit approver consent.

#### Typical examples

- cutover-ready migration waiting for go/no-go,
- security-sensitive change waiting on domain owner approval,
- cross-service interface change waiting for approver signoff,
- workstream closeout awaiting explicit acceptance.

#### Notes

`awaiting_approval` is a **hard gate**. Autonomous continuation past the decision boundary should not occur.

Layer D may reference the relevant approval packet or decision record, but the semantics of who must sign off and what packet is required belong to Layer C control profiles and the relevant policy.

### 6. `validating`
#### Meaning

The main work is now evidence generation, verification, or acceptance checking rather than new implementation.

#### Use when

Use `validating` when:

- implementation or preparation is sufficiently complete that verification dominates,
- evaluation runs are the main remaining activity,
- rollout observation is the controlling activity,
- migration readiness or compatibility is being confirmed,
- acceptance evidence is being assembled.

#### Typical examples

- running test or eval suites after implementation,
- observing staged rollout metrics,
- validating a retrieval change against offline benchmarks,
- checking migration readiness evidence.

#### Notes

`validating` is useful because "done building" and "accepted as sufficient" are not the same thing.

`validating` may involve HITL or may remain autonomous, depending on the workflow and control profile. It is a lifecycle state, not a governance regime.

### 7. `complete`
#### Meaning

The scoped work is finished and the declared acceptance path for that scope has been satisfied.

#### Use when

Use `complete` when:

- the agreed scope is done,
- relevant evidence exists,
- required validation has passed,
- required approval or acceptance has occurred,
- no further work remains inside the declared scope.

#### Typical examples

- a local implementation task with passing tests,
- a research slice with findings delivered and accepted,
- a migration slice completed through its approved scope,
- a workstream milestone accepted as complete.

#### Notes

Completion is always **scope-relative**. It means complete for this task or workstream slice, not complete for the entire domain forever.

### 8. `cancelled`
#### Meaning

The work is intentionally stopped, rejected, superseded, or no longer relevant.

#### Use when

Use `cancelled` when:

- priority changed,
- direction was rejected,
- the work was merged into another item,
- the task or milestone is no longer needed,
- the workstream is intentionally terminated.

#### Typical examples

- a research path rejected after review,
- a task superseded by a new contract,
- a workstream cancelled due to reprioritization,
- an evaluation slice abandoned because the benchmark is no longer needed.

#### Notes

`cancelled` should include a brief reason and, where relevant, a pointer to the superseding task, workstream, or decision record.

## Transition principles

Layer D should be implemented as a **small hard lifecycle model plus workflow-local `phase`**, not as a giant workflow-specific state machine.

### Principle 1 -- transitions reflect control changes

A state transition should occur when control status changes, not merely because the local activity label changed.

Examples:

- `phase: coding -> integration_fix` does not require a state change if the item is still simply `active`.
- `phase: contract_drafting -> tradeoff_review` may require `active -> checkpoint` if a real review boundary has been reached.

### Principle 2 -- prefer `phase` for local progression

Use `phase` instead of a new universal state when the distinction answers:

- what substep is happening,
- what local stage is next,
- what detailed workflow activity is active,

rather than:

- whether work may proceed,
- whether it is paused,
- whether approval is required,
- whether validation dominates,
- whether the item is done.

### Principle 3 -- use the least restrictive safe state

Prefer the least restrictive control state that remains safe.

Examples:

- do not use `awaiting_approval` when checkpoint review is sufficient,
- do not use `checkpoint` when ordinary active execution is still appropriate,
- do not use `blocked` when the real condition is a required approval gate,
- do not use `draft` when the item is already underway.

### Principle 4 -- checkpoint before approval when interpretation comes first

When the immediate need is interpretation, recommendation, or review of evidence, use `checkpoint`.

When the immediate need is a formal go/no-go decision, use `awaiting_approval`.

A common sequence is:

`active -> checkpoint -> awaiting_approval -> active`

But do not force that sequence when a direct approval gate is already the right model.

### Principle 5 -- validation is a real state

If evidence generation is the dominant activity, use `validating` explicitly.

Do not collapse all post-implementation work into `active`, because that hides the operational difference between:

- building,
- verifying,
- and waiting for acceptance.

### Principle 6 -- completion should be evidence-based

Do not move to `complete` merely because the agent believes the work is done.

Completion should be backed by the declared acceptance path for that task or workstream:

- tests,
- eval report,
- migration evidence,
- manual verification,
- explicit approval,
- or another declared validation mode.

### Principle 7 -- workflow detail belongs in `phase`, not new top-level states

If a workflow family wants to add labels such as:

- `researching`,
- `contract_shaping`,
- `ready_for_rehearsal`,
- `acceptance_review`,
- `rollout_observation`,

those should normally be modeled as local `phase` values.

Only add a new universal state when the distinction is control-plane material across many workflows.

## Recommended transitions

Typical allowed transitions include:

- `draft -> active`
- `draft -> cancelled`
- `active -> blocked`
- `active -> checkpoint`
- `active -> awaiting_approval`
- `active -> validating`
- `blocked -> active`
- `blocked -> checkpoint`
- `blocked -> cancelled`
- `checkpoint -> active`
- `checkpoint -> awaiting_approval`
- `checkpoint -> blocked`
- `awaiting_approval -> active`
- `awaiting_approval -> cancelled`
- `validating -> active`
- `validating -> checkpoint`
- `validating -> awaiting_approval`
- `validating -> complete`
- `complete -> active` in rare explicit reopen cases
- `cancelled -> draft` or `cancelled -> active` only by explicit reinstatement

## Discouraged transitions

Avoid the following unless there is strong explicit justification:

- `draft -> complete`
- `draft -> validating`
- `blocked -> complete`
- `complete -> draft` for materially new scope
- using `blocked` when the real state is `awaiting_approval`
- using `active` when a required checkpoint is actually in effect
- using `validating` to mean "someone else owns this now"

If materially new scope begins after completion, prefer a new task rather than mutating the old item into a new lifecycle.

## Terminal states

The typical terminal states are:

- `complete`
- `cancelled`

These normally stop ordinary progression.

## Reopening guidance

Reopening is allowed, but should be explicit and relatively rare.

### Reopen `complete` when

- accepted scope was not actually satisfied,
- a regression invalidates acceptance,
- additional work is discovered inside the same original scope,
- the responsible human owner explicitly reopens the item.

### Reopen `cancelled` when

- the work is formally reinstated,
- or an earlier cancellation is reversed by explicit decision.

### Prefer a new item when

- the new work is materially different in scope,
- the acceptance basis changed substantially,
- preserving historical accountability matters more than continuity in one record.

## Relationship to `phase`

`phase` is the workflow-local progression label that sits beneath the shared lifecycle state.

Layer D should preserve this rule:

> shared state answers control status; local `phase` answers local progression.

## What `phase` is for

Use `phase` to capture distinctions such as:

- `framing`
- `contract_drafting`
- `tradeoff_review`
- `coding`
- `repro`
- `root_cause_isolation`
- `rehearsal`
- `cutover_ready`
- `benchmark_run`
- `rollout_observation`
- `findings_delivered`

These are meaningful workflow-local stages, but they are not universal control-plane states.

## What `phase` is not for

`phase` should not replace the shared lifecycle state.

It should not be the only answer to questions like:

- may the agent continue,
- is a pause required,
- is approval pending,
- is validation now dominant,
- is the item complete.

## Recommended usage pattern

A Layer D record should normally contain:

- one universal `state`,
- one local `phase`,
- one explicit `next_step`,
- optional control-specific companion fields.

Examples:

```yaml
state: active
phase: contract_drafting
next_step: draft acceptance criteria and boundary assumptions
```

```yaml
state: checkpoint
phase: tradeoff_review
next_step: present design options with recommendation and evidence
```

```yaml
state: awaiting_approval
phase: cutover_ready
next_step: request go/no-go for staged migration
```

## When to use `phase` instead of a new universal state

Use `phase` when the distinction is:

- local to one workflow family,
- descriptive of substep or sequencing,
- not directly changing control permissions.

Examples that belong in `phase`, not as new universal states:

- `researching`
- `planning`
- `contract_drafting`
- `coding`
- `bug_repro`
- `benchmark_design`
- `rehearsal`
- `rollout_observation`

## Relationship to Layer A

Layer A remains the **descriptive classification snapshot**.

Layer D is downstream-compatible with Layer A, but it is not a substitute for it.

## How Layer A may influence Layer D

Layer A often influences which Layer D state is appropriate.

Examples:

- partial specification maturity may justify `draft` or `checkpoint` rather than immediate execution,
- explicit approval requirements may imply `awaiting_approval`,
- production confirmation requirements may imply `validating`,
- high governance burden may increase the frequency of checkpoints or approval states,
- long execution horizon may increase the importance of explicit state updates at workstream level.

## Examples of influence without collapse
### Partial specification

A slice classified as:

- `specification_maturity = scoped_problem`
- `uncertainty = design_heavy`

may be represented as:

- `state = draft`, `phase = framing`

or later:

- `state = checkpoint`, `phase = contract_review`

The Layer A facts explain *why* that state is reasonable. They do not become Layer D fields.

### Explicit approval requirement

A slice classified with:

- `approval_requirement = explicit_gate`

may reach:

- `state = awaiting_approval`, `phase = ready_for_signoff`

Layer A explains why approval is needed. Layer D records that approval is currently the controlling gate.

### Production confirmation requirement

A slice classified with:

- `validation_burden = production_confirmation_required`

may reach:

- `state = validating`, `phase = rollout_observation`

Layer A explains the burden. Layer D records that validation is now the dominant control state.

## Why Layer D is not a substitute for Layer A

Layer D does not answer:

- whether the work is design-heavy,
- whether knowledge is local or tacit,
- whether reversibility is hard,
- whether the horizon is multi-PR,
- whether correctness is hard to evaluate,
- whether the problem is exploratory or routine.

Those are classification facts, not lifecycle facts.

## Relationship to Layer B

Layer B remains the **current operating mode**.

Layer D remains the **shared lifecycle status**.

They are orthogonal.

## How Layer B may operate inside Layer D states

A single Layer B mode may appear in several Layer D states.

### Contract Builder

Contract Builder may be:

- `active` while drafting a contract,
- `checkpoint` when presenting trade-offs for review,
- `awaiting_approval` if explicit contract signoff is required,
- `complete` when the contract-definition slice is accepted.

### Migration Operator

Migration Operator may be:

- `active` while planning or rehearsing,
- `checkpoint` when readiness must be reviewed,
- `awaiting_approval` when cutover is ready,
- `validating` during staged rollout observation,
- `complete` once the declared migration scope is accepted.

### Quality Evaluator

Quality Evaluator may be:

- `active` while designing an evaluation plan,
- `checkpoint` when findings need interpretation,
- `validating` while benchmarks or evidence runs are underway,
- `complete` when the evaluation slice has delivered accepted findings.

## Why Layer D is not a substitute for Layer B

Layer D does not answer:

- whether the dominant posture is investigation, implementation, evaluation, migration, or contract-definition,
- what the primary output should be,
- what working style the agent should use,
- what reroute trigger should change the operating mode.

Those belong to Layer B.

## Relationship to Layer C

Layer C remains the layer for the `feature_cell` workstream wrapper and `control_profile` records.

Layer D records the current lifecycle status **within** the control regime that Layer C establishes.

This separation should be treated as hard.

## Core mapping rules
### Rule 1 -- Layer C changes how states are entered or exited, not what the states are

Control profiles may tighten preconditions, require evidence packets, or introduce additional review obligations.

They do not create new Layer D state names.

### Rule 2 -- control profiles modify continuation conditions

Reviewed-style control most often affects transitions involving:

- `checkpoint`
- sometimes `awaiting_approval`

Change-controlled or high-assurance control most often affects:

- stronger evidence requirements,
- stricter transition preconditions,
- more frequent use of `checkpoint`, `awaiting_approval`, and `validating`.

### Rule 3 -- containers introduce lifecycle scope, not new states

`feature_cell` introduces a workstream-level wrapper around multiple task slices.

It does not create a new lifecycle vocabulary. Instead, it means Layer D may need to be tracked at two levels:

- task-scope lifecycle,
- workstream-scope lifecycle.

## What Layer D may reference from Layer C

Layer D may reference:

- control-profile identifiers,
- relevant review or approval packets,
- linked decision records,
- workstream container identifiers.

## What Layer D should not own from Layer C

Layer D should not itself define as source-of-truth:

- reviewer role,
- signoff role,
- continuation rule semantics,
- rollback-plan requirement,
- traceability requirement,
- approval-packet requirement,
- workstream artifact expectations.

Those belong to Layer C records and associated policy.

## Relationship to HITL policy

Layer D should align with a minimal HITL model, but not duplicate or replace it.

A practical mapping is:

- **autonomous zone**
- **checkpoint zone**
- **approval zone**

## Mapping from Layer D states to HITL zones
### Autonomous zone

Usually includes:

- `draft` when no active review is required yet,
- `active`,
- `validating` when validation can proceed without a human decision,
- `blocked` when the issue is external or infrastructural rather than reviewer-mediated.

### Checkpoint zone

Usually includes:

- `checkpoint`

### Approval zone

Usually includes:

- `awaiting_approval`

## Why `checkpoint` is pause-and-summarize rather than stop-until-approved

`checkpoint` exists for reviewable interpretation.

The expected behavior is:

- pause,
- summarize,
- present evidence,
- request review or interpretation,
- resume based on the outcome.

A checkpoint may result in:

- return to `active`,
- transition to `awaiting_approval`,
- or a new block.

That is different from a hard approval gate.

## Why `awaiting_approval` is a hard gate

`awaiting_approval` means the next meaningful step cannot proceed until a designated decision authority approves it.

This is the right state for:

- go/no-go boundaries,
- irreversible steps,
- security-sensitive actions,
- contract changes requiring signoff,
- workstream closeout requiring explicit acceptance.

## Why `blocked` is not automatically the same as HITL

A task may be blocked because:

- a dependency is unavailable,
- an environment is broken,
- required data is missing,
- another team has not responded.

None of those inherently imply a checkpoint or approval interaction.

## Why `validating` may or may not involve HITL

`validating` means verification dominates. It does not by itself tell you whether:

- validation is autonomous,
- results require interpretation at checkpoint,
- acceptance requires explicit signoff.

That depends on workflow type, Layer C control context, and applicable policy.

## Role of Layer C control context in HITL

Layer C control profiles often determine whether a lifecycle state remains autonomous or enters a HITL zone.

Examples:

- a reviewed profile may turn a normal review boundary into `checkpoint` with a required review packet.
- a change-controlled or high-assurance profile may turn a risky transition into `awaiting_approval` with stricter evidence expectations.
- `feature_cell` may standardize where workstream-level checkpoint and approval moments occur across time.

## Relationship to routing and reclassification

Layer D is not the routing layer. It should not decide the operating mode by itself.

Routing belongs primarily to Layer A -> Layer B, with Layer C control profiles and `feature_cell` applied as needed.

## How Layer D participates in routing

Layer D matters because certain states naturally constrain what routing may happen next.

Examples:

- `draft` may indicate the slice is not yet ready for execution-heavy modes,
- `checkpoint` may be the moment where reclassification or rerouting is decided,
- `awaiting_approval` may defer rerouting until a decision is recorded,
- `validating` may trigger transition into a different mode only if evidence shows a new need.

## Reclassification should remain explicit

A task may change Layer B mode over time while remaining in the same Layer D state, or vice versa.

Examples:

- a task may reroute from Research Scout to Contract Builder while still `active`,
- a task may stay in Contract Builder but move from `active` to `checkpoint`,
- a migration slice may stay in Migration Operator while moving from `active` to `awaiting_approval` to `validating`.

Layer D should support such changes, not absorb them.

## Relationship to task and workstream artifacts

Layer D is most useful when attached to explicit artifacts.

## Task cards

For task cards, Layer D should make it easy to answer:

- what is the current control status,
- what local phase is active,
- what the next step is,
- whether the task is blocked,
- whether a checkpoint or approval is pending,
- what evidence or decision references matter now.

## Workstream cards

For workstream cards, Layer D should make it easy to answer:

- what is the current workstream-level control status,
- which milestone or phase is active,
- whether the workstream is paused at a checkpoint or approval gate,
- what child tasks are active or blocked,
- what the next coordination step is.

## Decision logs

Layer D should link to decision records when:

- checkpoint interpretation changes direction,
- approval is granted or denied,
- cancellation is decided,
- reopened scope is explicitly authorized.

## Next-step tracking

Every non-terminal Layer D record should usually include `next_step`.

This is critical for resumability and handoff.

## Blocking reasons

`blocked` should always carry:

- a concise `blocking_reason`,
- preferably an `unblock_condition`,
- optionally the owning dependency, team, or artifact reference.

## Task-scope vs workstream-scope lifecycle

This distinction should be explicit, especially when Layer C uses `feature_cell`.

## Task-scope lifecycle

Task-scope Layer D describes the control status of the **current executable slice**.

Examples:

- a bug investigation task is `active`,
- a migration rehearsal task is `validating`,
- a contract draft task is `checkpoint`.

## Workstream-scope lifecycle

Workstream-scope Layer D describes the control status of the **containerized effort as a whole**.

Examples:

- a feature workstream is `active` during coordinated execution,
- the same workstream is `checkpoint` at design acceptance,
- the same workstream is `awaiting_approval` for rollout,
- the same workstream is `complete` when the milestone or scoped feature is accepted.

## Important rules
### Rule 1 -- do not derive workstream state mechanically from child tasks

A `feature_cell` may remain `active` while one child task is `blocked`.

### Rule 2 -- a workstream may hit a checkpoint while child tasks are still active

Example: a feature workstream may be at a design or rollout checkpoint even though implementation subtasks still exist.

### Rule 3 -- approval may exist at workstream level while child tasks are already complete

Example: rollout approval may be pending after implementation tasks are complete.

### Rule 4 -- track both levels when the distinction matters operationally

For simple one-shot work, task-level lifecycle may be enough.

For long-running multi-slice work, record both task-scope and workstream-scope Layer D explicitly.

## Recommended schema and companion fields

Layer D should use a compact schema.

The schema should be thin enough to keep lifecycle status clean, while allowing references to evidence and decisions.

## Core schema

```yaml
layer_d:
  state: draft | active | blocked | checkpoint | awaiting_approval | validating | complete | cancelled
  phase: <workflow-local phase or null>
  next_step: <explicit next action or null>
  entered_at: <timestamp or null>
  updated_at: <timestamp or null>
```

This is the irreducible core.

## Recommended companion fields

```yaml
layer_d_companion:
  blocking_reason: <string or null>
  unblock_condition: <string or null>
  checkpoint_reason: <string or null>
  approval_ref: <artifact or decision ref or null>
  evidence_refs: []
  decision_ref: <string or null>
  lifecycle_scope: task | workstream
```

## Optional adjacent fields

These may be useful, but they should remain clearly adjacent rather than being treated as the essence of Layer D:

```yaml
adjacent_control_fields:
  validation_mode: tests | eval | rollout | human_review | mixed | null
  intent: <optional local intent label>
  requires_hitl: <derived boolean or null>
```

## Schema guidance
### `state`

Required. This is the canonical lifecycle value.

### `phase`

Strongly recommended. Use for workflow-local progression.

### `next_step`

Strongly recommended for every non-terminal state.

### `blocking_reason`

Required when `state = blocked`.

### `checkpoint_reason`

Useful when `state = checkpoint`.

### `approval_ref`

Useful when `state = awaiting_approval`.

### `evidence_refs`

Recommended when `state = checkpoint`, `validating`, `awaiting_approval`, or `complete`.

### `lifecycle_scope`

Recommended when both task-scope and workstream-scope records may coexist.

### `validation_mode`

Useful for operational clarity, but not part of the irreducible lifecycle core.

### `requires_hitl`

Treat this as a **derived convenience field**, not a source-of-truth lifecycle field.

The true source of truth should be:

- the Layer D state,
- the applicable Layer C control context,
- the governing HITL policy.

Do not let a single boolean replace those distinctions.

## Worked examples

Each example below shows the intended composition:

- a brief Layer A / B context,
- optional Layer C control-profile or workstream-wrapper context,
- the correct Layer D representation,
- why that control-plane representation is right.

## Example 1 -- Small local implementation task
### Context

- Layer A: low uncertainty, implementation-ready, local blast radius, strong test confidence
- Layer B: Routine Implementer
- Layer C: none

### Layer D

```yaml
layer_d:
  state: active
  phase: coding
  next_step: implement local change and run tests
```

### Why this is correct

The slice is executable now. No checkpoint or approval gate is active. `active` is the right control-plane status.

## Example 2 -- Research / exploration slice
### Context

- Layer A: exploratory, design-heavy, partial signals only
- Layer B: Research Scout
- Layer C: none initially

### Layer D

```yaml
layer_d:
  state: active
  phase: evidence_gathering
  next_step: collect findings on options and constraints
```

Later, once the findings need interpretation:

```yaml
layer_d:
  state: checkpoint
  phase: findings_review
  next_step: present synthesis and recommendation
```

### Why this is correct

Research itself can remain `active`. The moment requiring reviewable interpretation is what justifies `checkpoint`.

## Example 3 -- Ambiguous feature / contract-definition slice
### Context

- Layer A: implement intent, scoped problem, design-heavy, multi-PR, `handoff_need = high`
- Layer B: Contract Builder
- Layer C: `feature_cell`

### Task-level Layer D

```yaml
layer_d:
  state: active
  phase: contract_drafting
  next_step: define acceptance criteria and boundary assumptions
```

If trade-offs must be reviewed:

```yaml
layer_d:
  state: checkpoint
  phase: contract_review
  next_step: present options and recommend one contract
```

### Workstream-level Layer D

```yaml
layer_d:
  state: active
  phase: shaping
  next_step: finalize contract and create implementation slices
```

### Why this is correct

The container is Layer C, not Layer D. The workstream is long-horizon, but the current task slice may still simply be `active`. `checkpoint` is used only when a real review boundary exists.

## Example 4 -- Bug investigation
### Context

- Layer A: debug intent, expected behavior known, root cause unclear
- Layer B: Debug Investigator
- Layer C: none

### Layer D

```yaml
layer_d:
  state: active
  phase: root_cause_isolation
  next_step: reduce repro and identify failing path
```

If logs are unavailable:

```yaml
layer_d:
  state: blocked
  phase: evidence_missing
  next_step: obtain production logs for failing request family
```

### Why this is correct

The mode is still Debug Investigator in both cases. What changes is the control status: executable vs blocked.

## Example 5 -- Migration / rollout-sensitive slice
### Context

- Layer A: migrate intent, cross-service dependency, explicit gate, production confirmation required, hard reversibility
- Layer B: Migration Operator
- Layer C: non-baseline `control_profile`, usually `change_controlled` or `high_assurance`

### During preparation

```yaml
layer_d:
  state: active
  phase: rehearsal
  next_step: execute migration rehearsal and capture readiness evidence
```

### At review boundary

```yaml
layer_d:
  state: checkpoint
  phase: readiness_review
  next_step: summarize rehearsal evidence and recommend cutover posture
```

### At hard gate

```yaml
layer_d:
  state: awaiting_approval
  phase: cutover_ready
  next_step: request go/no-go approval
```

### During rollout verification

```yaml
layer_d:
  state: validating
  phase: rollout_observation
  next_step: monitor staged rollout and confirm invariants
```

### Why this is correct

The control profile makes control stricter, but Layer D remains the same eight-state vocabulary. Control regime comes from Layer C; current gate comes from Layer D.

## Example 6 -- Evaluation-heavy slice
### Context

- Layer A: optimize intent, offline evaluation required, artifact type is eval report
- Layer B: Quality Evaluator
- Layer C: a reviewed `control_profile` may apply if results need human interpretation

### Normal evaluation run

```yaml
layer_d:
  state: validating
  phase: benchmark_run
  next_step: run benchmark suite and collect deltas
```

### After evidence is collected and needs interpretation

```yaml
layer_d:
  state: checkpoint
  phase: findings_review
  next_step: review eval results and decide whether they justify rollout
```

### Why this is correct

`validating` is correct while evidence generation dominates. `checkpoint` becomes correct when interpretation or acceptance review becomes the controlling activity.

## Example 7 -- Long-running feature workstream
### Context

- Layer A: multi-PR, `handoff_need = high`, mixed uncertainty across slices
- Layer B: changes over time across Contract Builder, Routine Implementer, Quality Evaluator
- Layer C: `feature_cell`

### Workstream-level Layer D during execution

```yaml
layer_d:
  state: active
  phase: coordinated_delivery
  next_step: advance implementation slices and track milestone readiness
```

### Workstream-level Layer D at milestone review

```yaml
layer_d:
  state: checkpoint
  phase: milestone_review
  next_step: review progress, open risks, and milestone acceptance recommendation
```

### Workstream-level Layer D before rollout

```yaml
layer_d:
  state: awaiting_approval
  phase: rollout_ready
  next_step: request rollout approval for scoped release
```

### Why this is correct

The workstream-level control status is not mechanically reducible to child-task states. The container introduces long-horizon coordination, not a new lifecycle vocabulary.

## Adoption and governance guidance

Keep Layer D small:
- start with the canonical eight states,
- use workflow-local `phase` for local progression,
- let Layer C carry control-regime detail,
- and use linked evidence or decisions for richer transition context.

For harness-wide policy on adding universal states, evolving Layer D adoption, and synchronizing other docs when Layer D changes, use `docs/harness/maintainining.md`.

## Final recommendation

Layer D should remain a **minimal shared lifecycle control plane** with these properties:

- small and stable,
- strictly control-plane in meaning,
- independent from Layer A classification,
- independent from Layer B operating mode,
- independent from Layer C control profiles and `feature_cell`,
- implemented as eight canonical states plus workflow-local `phase`,
- usable at both task scope and workstream scope,
- backed by companion fields, evidence references, and decision artifacts.

The canonical Layer D state set should remain:

- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

The core architectural rule is:

> Layer D records the current lifecycle gate or control status. It does not record the classification of the work, the current operating posture, or the governance regime under which that status exists.

That is the right level for a durable control plane.
