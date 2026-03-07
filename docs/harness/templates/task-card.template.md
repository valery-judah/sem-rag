
# Task Card Template

Use this template for every non-trivial task slice in the harness.

A task card is the authoritative operational record for a single current slice of work. It should be small enough that one current Layer B mode makes sense and explicit enough that another agent can resume from it without replaying the whole history.

The frontmatter is the authoritative structured control surface for the task. The markdown body provides narrative context, references, and history. Do not duplicate the Layer A-D fields in prose unless a short rationale is operationally useful.

Task cards now use canonical Layer C fields directly. If a task belongs to a workstream, link it through `layer_c.feature_cell_ref`. Workstream cards use their own canonical `layer_c.feature_cell`, `layer_c.control_profiles`, `layer_d`, and `layer_d_companion` structures.

## Usage notes

- Create one file per task in `docs/harness/active/tasks/`.
- Use the task card as the primary source of truth for the slice.
- After meaningful progress, update the card before reporting, pausing, handing off, rerouting, or closing the cycle.
- Refresh the card whenever the slice, mode, Layer C context, state, next step, or linked evidence or decision refs change materially.
- Treat these as the default maintenance surfaces during write-back: `updated_at`, `layer_b.*`, `layer_d.*`, relevant `layer_d_companion.*` fields, and the work log.
- Keep detailed execution notes in the work log, but keep the frontmatter clean enough to function as a control surface.
- Make it easy for the next reader to jump from `layer_b.current_mode` to the matching mode file and from `layer_d.state` to the correct workflow or control doc.
- If the task grows beyond one coherent slice, reslice it or promote the larger effort to a workstream rather than turning this card into a catch-all.

## Copyable template

```md
---
id: T-YYYY-MM-DD-XXX
title: <short title for the current slice>
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
owner: agent
layer_a:
  intent:
  problem_uncertainty:
  dependency_complexity:
  knowledge_locality:
  specification_maturity:
  validation_burden:
  blast_radius:
  execution_horizon:
layer_b:
  current_mode:
  reason:
  reroute_triggers: []
layer_c:
  feature_cell_ref: null
  control_profiles: []
layer_d:
  state: draft
  phase:
  next_step:
  entered_at:
  updated_at:
layer_d_companion:
  blocking_reason:
  unblock_condition:
  checkpoint_reason:
  approval_ref:
  evidence_refs: []
  decision_ref:
  lifecycle_scope: task
---

# Summary

## Request / problem

<What is being asked or what problem this slice addresses.>

## Current slice boundary

<What this task covers now. Keep this narrow and explicit.>

## Out of scope for this slice

<What is intentionally excluded from this task.>

## Operator navigation

- Mode guide: <mode file path or short pointer>
- Workflow / boundary guide: <workflow path or short pointer based on current state>
- Optional local routing note: <only when the next read is not obvious from mode and state alone>

# Inputs / References

- <repo path, issue, PR, doc, note, or other relevant artifact>
- <...>

# Notes

## Classification notes

<Record any uncertainty or short classification rationale if useful.>

## Layer C rationale

<Why the current feature-cell link or control profiles do or do not apply.>

## Current control condition

<Describe the current control status in plain language if useful.>

# Work Log

## YYYY-MM-DD

- <What was done>
- <What was observed>
- <What changed>
- <What should happen next>

# Open Questions / Risks

- <open question>
- <risk or trap>

# Closure

## Acceptance basis

<How this slice will be considered complete: tests, eval, explicit review, approval, implementation done, etc.>

## Closure notes

<Record final completion or cancellation context when the task ends.>
```

## Field guidance

### Frontmatter is authoritative

The frontmatter is the canonical task record.

Use it for:
- Layer A classification,
- Layer B routing,
- Layer C task-local control context,
- Layer D lifecycle state,
- and the Layer D companion fields.

Use the body for:
- the task summary,
- supporting rationale,
- references,
- work log history,
- open questions,
- and closure context.

Do not mirror the frontmatter values into body bullet lists just to keep them visible twice.
Do not let the work log or final response become more current than the frontmatter control surface.

### Optional `Operator navigation` section

Use this short body section only to reduce document hops for the next operator.

Good uses:
- point from `layer_b.current_mode` to the matching mode file,
- point from `layer_d.state` to the next workflow or boundary doc,
- add one local routing note when the correct next read would otherwise be easy to miss.

Do not use it to duplicate the full frontmatter or restate general harness rules.

### `id`

Use a stable unique task identifier.

Recommended pattern:
- `T-YYYY-MM-DD-XXX`

Example:
- `T-2026-03-06-001`

### `title`

The title should describe the current slice, not the whole initiative.

Good:
- `Investigate parser regression in block normalization`
- `Draft RFC structure for hierarchical segmentation`
- `Define intermediate schema acceptance contract`

Bad:
- `Improve parser`
- `Fix RAG`
- `Build segmentation feature`

### Top-level timestamps

Use:
- `created_at` for card creation date,
- `updated_at` for latest card update date.

These are card-level timestamps.
Refresh `updated_at` whenever a meaningful write-back changes the card.

### `layer_a`

Fill at least the required Layer A core fields:

- `intent`
- `problem_uncertainty`
- `dependency_complexity`
- `knowledge_locality`
- `specification_maturity`
- `validation_burden`
- `blast_radius`
- `execution_horizon`

Use Layer A to capture the current problem shape, not long-term identity.

Preferred starter values for commonly improvised Layer A fields:
- `intent`: `implement`, `refactor`, `debug`, `research`, `review`, `migrate`, `optimize`
- `dependency_complexity`: `self_contained`, `few_local_dependencies`, `cross_module`, `cross_service`, `external_or_multi_party`
- `knowledge_locality`: `fully_local`, `mostly_local`, `scattered_internal`, `external_research_required`, `tacit_human_required`

Use the closest canonical value and explain nuance in notes rather than inventing local variants such as task-specific synonyms or ad hoc severity bands.

### `layer_b.current_mode`

Use exactly one current Layer B operating mode.

Expected values:
- `research_scout`
- `contract_builder`
- `routine_implementer`
- `refactor_surgeon`
- `debug_investigator`
- `migration_operator`
- `optimization_tuner`
- `quality_evaluator`

### `layer_b.reason`

Explain why this mode is dominant now.

Keep it short and operational.

### `layer_b.reroute_triggers`

Capture the conditions that would justify changing posture.

Examples:
- `If root cause is identified and implementation path becomes clear, reroute to routine_implementer.`
- `If issue is actually undefined contract behavior, reroute to contract_builder.`

### `layer_c.feature_cell_ref`

Use a workstream identifier or file ref when this task belongs to a `feature_cell`.

Use `null` when the task is not part of a workstream.

This is the repository-local task-card representation of workstream membership. Do not copy the full `feature_cell` object into the task card.

### `layer_c.control_profiles`

Keep this list empty unless non-baseline control is materially active for the task.

Use `[]` when baseline control is implied.

Each item should use the canonical Layer C `control_profile` fields. For task cards, profiles should usually be slice-scoped.

For early contract-definition work, keep baseline control while the contract is still being drafted. Add a reviewed-style `control_profile` only when the slice has reached a real review or interpretation boundary and progress should pause there before implementation-aligned continuation.

Minimal reviewed-profile example:

```yaml
layer_c:
  feature_cell_ref: W-2026-03-segmentation
  control_profiles:
    - scope: slice
      reason: contract acceptance requires human interpretation before implementation
      entered_at: 2026-03-06
      preset_refs: [reviewed]
      review:
        required: true
        trigger_classes: [acceptance_interpretation]
      approval:
        required: false
        trigger_classes: []
      evidence:
        level: elevated
      traceability:
        level: standard
        decision_log_required: false
      rollback:
        required: false
        rollback_ref: null
      policy_refs:
        policy_profile_ref: null
        packet_template_ref: templates/review-packet.template.md
        review_protocol_ref: null
        approval_protocol_ref: null
      notes: null
```

### `layer_d`

`layer_d` is the control surface for the task.

Use it to answer:
- can work continue,
- is the task blocked,
- is it paused for review,
- is approval pending,
- is validation now dominant,
- is the slice done.

#### `layer_d.state`

Use only the Layer D lifecycle states defined by the harness.

Expected values:
- `draft`
- `active`
- `blocked`
- `checkpoint`
- `awaiting_approval`
- `validating`
- `complete`
- `cancelled`

#### `layer_d.phase`

Use a short freeform description of the current local phase if helpful.

Examples:
- `reproduction`
- `contract drafting`
- `implementation`
- `evaluation pass`
- `review packet preparation`

Do not turn `phase` into a second state machine.

#### `layer_d.next_step`

This is mandatory for every non-terminal task.

A good `next_step` is:
- concrete,
- local to the current slice,
- executable by another agent,
- consistent with the current mode and state.

#### `layer_d.entered_at`

Record when the task entered the current Layer D state.

#### `layer_d.updated_at`

Record the last time the Layer D record itself changed.
Refresh this whenever `layer_d.state`, `phase`, or `next_step` is rewritten to match current reality.

### `layer_d_companion`

Companion field guidance:
- state changes are incomplete until the required companion fields are updated
- `blocked` requires `blocking_reason` and a useful `unblock_condition`
- `checkpoint` requires `checkpoint_reason` and linked review material when present
- `awaiting_approval` requires `approval_ref` or an explicit approval dependency
- `validating` should accumulate `evidence_refs`
- `complete` should leave a concrete acceptance basis in closure context and any supporting refs
- fill `evidence_refs` when validation, checkpoint, or completion depends on evidence
- fill `decision_ref` when a meaningful decision changed the route or closed the task
- keep `lifecycle_scope: task`

### Summary section

This section should tell another agent:
- what the task is,
- what the current slice is,
- what is intentionally out of scope.

If this section becomes vague, the task likely needs reslicing.

### Inputs / References

Include only the references that materially help execution or review.

Typical items:
- repo files,
- issues,
- PRs,
- docs,
- RFCs,
- benchmark outputs,
- review packets,
- evidence bundles,
- related task/workstream links.

### Notes

Use the notes section for concise rationale that does not belong inside the structured fields.

Good uses:
- explaining uncertainty in the Layer A classification,
- explaining why no `feature_cell` or `control_profile` is active,
- describing the current control condition in plain language.

Bad uses:
- restating `layer_b.current_mode`,
- copying `layer_d.state`,
- listing `layer_c.control_profiles` again in prose.

### Work Log

Append short entries at meaningful boundaries.

A good work log entry records:
- action taken,
- observation,
- effect on understanding or routing,
- resulting next move.

Do not let the work log replace the summary or the frontmatter control fields.
Refresh the work log in the same write-back pass that refreshes mode, state, `next_step`, and companion refs.

### Open Questions / Risks

Use this section for the few unresolved issues or traps that matter operationally.

Examples:
- missing acceptance criteria,
- likely hidden dependency,
- risk of crossing a review boundary accidentally,
- known fragile assumption.

### Closure

Record both the expected acceptance basis and final closure notes.

Examples of acceptance basis:
- regression reproduced and fixed with passing test,
- RFC section reviewed and accepted,
- evaluation evidence produced and accepted,
- migration readiness approved,
- task superseded and cancelled with replacement reference.

## Minimal examples

### Example 1: debugging slice

```md
---
id: T-2026-03-06-001
title: Investigate parser regression in block normalization
created_at: 2026-03-06
updated_at: 2026-03-06
owner: agent
layer_a:
  intent: debug
  problem_uncertainty: local_ambiguity
  dependency_complexity: few_local_dependencies
  knowledge_locality: mostly_local
  specification_maturity: frozen_contract
  validation_burden: tests_strong_confidence
  blast_radius: subsystem
  execution_horizon: atomic
layer_b:
  current_mode: debug_investigator
  reason: Root-cause isolation is the dominant current work.
  reroute_triggers:
    - If the failing transformation is isolated and the fix is obvious, reroute to routine_implementer.
layer_c:
  feature_cell_ref: null
  control_profiles: []
layer_d:
  state: active
  phase: reproduction
  next_step: Isolate the first normalization stage where nested list structure is lost.
  entered_at: 2026-03-06
  updated_at: 2026-03-06
layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs: []
  decision_ref: null
  lifecycle_scope: task
---
```

### Example 2: contract drafting slice with review boundary

```md
---
id: T-2026-03-06-002
title: Define intermediate schema acceptance contract
created_at: 2026-03-06
updated_at: 2026-03-06
owner: agent
layer_a:
  intent: research
  problem_uncertainty: design_heavy
  dependency_complexity: cross_module
  knowledge_locality: scattered_internal
  specification_maturity: scoped_problem
  validation_burden: partial_signals_only
  blast_radius: subsystem
  execution_horizon: multi_pr
layer_b:
  current_mode: contract_builder
  reason: The dominant work is defining the contract and preparing it for review.
  reroute_triggers:
    - If the contract is accepted and implementation becomes clear, reroute to routine_implementer.
layer_c:
  feature_cell_ref: W-2026-03-segmentation
  control_profiles:
    - scope: slice
      reason: Contract acceptance requires human interpretation before implementation.
      entered_at: 2026-03-06
      preset_refs: [reviewed]
      review:
        required: true
        trigger_classes: [acceptance_interpretation]
      approval:
        required: false
        trigger_classes: []
      evidence:
        level: elevated
      traceability:
        level: standard
        decision_log_required: false
      rollback:
        required: false
        rollback_ref: null
      policy_refs:
        policy_profile_ref: null
        packet_template_ref: templates/review-packet.template.md
        review_protocol_ref: null
        approval_protocol_ref: null
      notes: null
layer_d:
  state: checkpoint
  phase: contract draft ready for review
  next_step: Review the linked contract packet and decide whether stage-1 schema can be locked.
  entered_at: 2026-03-06
  updated_at: 2026-03-06
layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: Contract draft is complete enough for acceptance review.
  approval_ref: null
  evidence_refs:
    - docs/harness/reviews/stage-1-schema-contract.md
  decision_ref: null
  lifecycle_scope: task
---
```

## Maintenance rules

- Every non-terminal task must have a concrete `layer_d.next_step`.
- Every task must have exactly one current `layer_b.current_mode`.
- Do not keep stale `layer_c.feature_cell_ref`, stale `layer_c.control_profiles`, stale blockers, or stale checkpoint reasons.
- If the title or summary no longer describes the current slice, reslice the task.
- If the work clearly spans multiple slices over time, link it to a workstream or promote the larger effort.
- When a task ends, record closure context rather than silently abandoning it.
