# Examples

This document provides **worked Layer C examples** for the refactored model.

The goal is not to cover every possible case. The goal is to show how to apply:

- `feature_cell`
- `control_profile`
- preset aliases
- scope and inheritance rules
- separation from Layer B modes
- separation from Layer D lifecycle state

Each example is intentionally small enough to reason about, but concrete enough to reuse as a pattern.

## How to read these examples

In each case, separate four questions:

1. **What is the shape of the work?** -> Layer A
2. **How should the agent work now?** -> Layer B
3. **What control regime or workstream wrapper applies?** -> Layer C
4. **What is the current status or gate?** -> Layer D

The examples focus on Layer C while keeping the other layers visible enough to prevent boundary collapse.

Representation decisions used throughout:

- `feature_cell: null` means no workstream wrapper is active
- `control_profiles: []` means baseline control is implied
- explicit `baseline` profiles are omitted by default
- `null` is used for absent scalar refs
- `[]` is used for empty collections

---

## Example 1: local implementation slice with no extra control burden

### Situation

A small parser refactor is needed to simplify block normalization logic. The change is local, reversible, and can be completed in one slice with ordinary validation.

### Why this is not a feature cell

The work:

- is single-slice,
- has low handoff risk,
- does not need workstream-level visibility,
- and does not require a persistent wrapper.

### Why this is baseline control

There is no unusual need for:

- checkpoint review,
- explicit approval,
- elevated evidence,
- elevated traceability,
- or rollback planning.

### Layer sketch

- **Layer B** might be `routine_implementer`
- **Layer C** is baseline only
- **Layer D** might move `ready -> in_progress -> validating -> done`

### Layer C record

```yaml
layer_c:
  feature_cell: null
  control_profiles: []
```

### Why this is the right pattern

This keeps Layer C minimal. There is no reason to create either a `feature_cell` or a stronger `control_profile` merely because the change is useful or non-trivial.

---

## Example 2: reviewed design slice without a feature cell

### Situation

A slice is focused on clarifying a segmentation contract and proposing the normalized schema. The main risk is not rollout or reversibility. The main issue is that the resulting design requires human interpretation before implementation proceeds.

### Why this is not a feature cell

Even if the topic is important, the current unit of work is still a single design slice. It does not yet require long-horizon workstream wrapping.

### Why this is `reviewed`

The main additional burden is human interpretation at a boundary:

- tradeoff review,
- architecture review,
- or acceptance interpretation.

There is no separate approval-controlled transition yet.

### Layer sketch

- **Layer B** might be `contract_builder`
- **Layer C** is a slice-level reviewed `control_profile`
- **Layer D** may later enter `checkpoint` when review is actually needed

### Layer C record

```yaml
layer_c:
  feature_cell: null
  control_profiles:
    - scope: slice
      reason: proposed schema requires architecture review before implementation
      entered_at: 2026-03-06
      preset_refs: [reviewed]
      review:
        required: true
        trigger_classes: [architecture_review]
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
        policy_profile_ref: policies/design-review-v1
        packet_template_ref: templates/design-review-packet-v1
        review_protocol_ref: protocols/design-review-v1
        approval_protocol_ref: null
      notes: null
```

### Important boundary note

`reviewed` does not mean the slice is already in a review checkpoint. It means the slice is operating under a regime where defined review triggers exist. The actual current gate belongs in Layer D.

---

## Example 3: multi-slice feature build wrapped as a feature cell

### Situation

A feature requires:

- contract clarification,
- staged implementation,
- evaluation,
- documentation,
- and a final integration pass.

The work will likely span multiple sessions and multiple slices, and it should remain resumable.

### Why this is a feature cell

The work:

- clearly exceeds one slice,
- has a shared user-visible outcome,
- needs continuity across sessions,
- and benefits from workstream-level visibility.

### Why control can still be baseline

A `feature_cell` is about the workstream wrapper, not necessarily about extra control burden. A workstream can need continuity without needing review or approval escalation.

### Layer sketch

- **Layer B** varies by slice over time
- **Layer C** includes a `feature_cell`
- **Layer D** may be tracked both at workstream level and per slice

### Layer C record

```yaml
layer_c:
  feature_cell:
    scope: workstream
    slug: hierarchical-segmentation-phase-1
    title: Hierarchical segmentation phase 1
    goal: define and deliver the initial hierarchical segmentation capability with testable boundaries and evaluation hooks
    reason: multi-slice feature with high continuity and handoff needs
    entered_at: 2026-03-06
    status_ref: lifecycle/workstreams/hierarchical-segmentation-phase-1
    operating_package_ref: workstreams/hierarchical-segmentation-phase-1/README.md
    slices_ref:
      - tasks/specify-boundaries.md
      - tasks/write-tests.md
      - tasks/implement-initial-segmentation.md
      - tasks/run-evaluation.md
    milestones:
      - contract agreed
      - initial implementation merged
      - first evaluation reviewed
    decision_log_ref: workstreams/hierarchical-segmentation-phase-1/decision-log.md
    handoff_ref: workstreams/hierarchical-segmentation-phase-1/handoff.md
    evidence_refs:
      - docs/rfcs/hierarchical-segmentation.md
      - reports/hierarchical-segmentation-eval-v1.md
    control_profile_refs: []
    notes: null
  control_profiles: []
```

### Important boundary note

Do not infer stronger control semantics from the mere presence of a `feature_cell`. The workstream wrapper exists because the work spans time and slices, not because it is blocked or high-assurance.

---

## Example 4: workstream-level change-controlled migration

### Situation

A parser migration changes a shared output contract and requires staged rollout. The work spans multiple slices and needs explicit release discipline, rollback visibility, and approval at specific transitions.

### Why this is a feature cell

The migration is multi-slice and long-horizon.

### Why this is `change_controlled`

The main additional burden is not design interpretation. It is transition safety:

- rollout,
- cutover,
- rollback readiness,
- contract sensitivity.

### Layer sketch

- **Layer B** may shift among `contract_builder`, `migration_operator`, and `quality_evaluator`
- **Layer C** includes both `feature_cell` and a workstream-level `change_controlled` profile
- **Layer D** may place specific slices into `awaiting_approval` at rollout boundaries

### Layer C record

```yaml
layer_c:
  feature_cell:
    scope: workstream
    slug: parser-block-schema-migration
    title: Parser migration to structured block schema
    goal: migrate parser outputs to the new block schema with validation and safe rollout support
    reason: staged multi-slice migration with cross-slice dependency, rollout sensitivity, and high handoff risk
    entered_at: 2026-03-06
    status_ref: lifecycle/workstreams/parser-block-schema-migration
    operating_package_ref: workstreams/parser-block-schema-migration/README.md
    slices_ref:
      - tasks/define-block-schema.md
      - tasks/refactor-parser-model.md
      - tasks/write-migration-tests.md
      - tasks/run-validation.md
      - tasks/prepare-rollout.md
    milestones:
      - target schema finalized
      - parser model refactored
      - migration test suite passing
      - rollout packet prepared
    decision_log_ref: workstreams/parser-block-schema-migration/decision-log.md
    handoff_ref: workstreams/parser-block-schema-migration/handoff.md
    evidence_refs:
      - docs/rfcs/parser-schema-migration.md
      - reports/parser-migration-validation.md
    control_profile_refs:
      - layer-c/control-profiles/parser-migration-change-controlled.yaml
    notes: null
  control_profiles:
    - scope: workstream
      reason: rollout and cutover require explicit approval with visible rollback support
      entered_at: 2026-03-06
      preset_refs: [change_controlled]
      review:
        required: false
        trigger_classes: []
      approval:
        required: true
        trigger_classes: [rollout, cutover]
      evidence:
        level: elevated
      traceability:
        level: elevated
        decision_log_required: true
      rollback:
        required: true
        rollback_ref: docs/runbooks/parser-rollback.md
      inherits_to_children: true
      applies_to: selected_slices
      policy_refs:
        policy_profile_ref: policies/release-control-v1
        packet_template_ref: templates/release-packet-v1
        review_protocol_ref: null
        approval_protocol_ref: protocols/release-approval-v1
      notes: null
```

### Important boundary note

`change_controlled` does not mean the workstream is always waiting for approval. It means approval is required at defined trigger classes. The actual current status still belongs in Layer D.

---

## Example 5: feature cell with stronger slice-local reviewed control

### Situation

A workstream is generally change-controlled because it includes rollout-sensitive transitions. However, one specific evaluation slice also requires human interpretation because the acceptance evidence is ambiguous.

### Why this matters

This example shows two things:

1. workstream-level control does not eliminate the need for slice-local strengthening
2. composition is preferable to inventing another special Layer C construct

### Layer sketch

- **Layer B** varies by slice
- **Layer C** includes:
  - one `feature_cell`
  - one workstream-level `change_controlled` profile
  - one slice-level `reviewed` profile
- **Layer D** may separately track rollout approval and evaluation checkpoints

### Layer C record

```yaml
layer_c:
  feature_cell:
    scope: workstream
    slug: parser-block-schema-migration
    title: Parser migration to structured block schema
    goal: migrate parser outputs to the new block schema with validation and safe rollout support
    reason: staged multi-slice migration with cross-slice dependency and rollout sensitivity
    entered_at: 2026-03-06
    status_ref: lifecycle/workstreams/parser-block-schema-migration
    operating_package_ref: workstreams/parser-block-schema-migration/README.md
    slices_ref:
      - tasks/run-validation.md
      - tasks/prepare-rollout.md
    milestones:
      - validation evidence assembled
      - rollout packet prepared
    decision_log_ref: workstreams/parser-block-schema-migration/decision-log.md
    handoff_ref: workstreams/parser-block-schema-migration/handoff.md
    evidence_refs:
      - reports/parser-migration-validation.md
    control_profile_refs:
      - layer-c/control-profiles/parser-migration-change-controlled.yaml
      - layer-c/control-profiles/parser-validation-reviewed.yaml
    notes: null
  control_profiles:
    - scope: workstream
      reason: rollout and cutover require explicit approval and rollback readiness
      entered_at: 2026-03-06
      preset_refs: [change_controlled]
      review:
        required: false
        trigger_classes: []
      approval:
        required: true
        trigger_classes: [rollout, cutover]
      evidence:
        level: elevated
      traceability:
        level: elevated
        decision_log_required: true
      rollback:
        required: true
        rollback_ref: docs/runbooks/parser-rollback.md
      inherits_to_children: true
      applies_to: selected_slices
      policy_refs:
        policy_profile_ref: policies/release-control-v1
        packet_template_ref: templates/release-packet-v1
        review_protocol_ref: null
        approval_protocol_ref: protocols/release-approval-v1
      notes: null
    - scope: slice
      reason: validation results are ambiguous and require human interpretation before rollout proceeds
      entered_at: 2026-03-06
      preset_refs: [reviewed]
      review:
        required: true
        trigger_classes: [acceptance_interpretation, ambiguous_eval]
      approval:
        required: false
        trigger_classes: []
      evidence:
        level: elevated
      traceability:
        level: elevated
        decision_log_required: true
      rollback:
        required: false
        rollback_ref: null
      policy_refs:
        policy_profile_ref: policies/reviewed-eval-v1
        packet_template_ref: templates/review-packet-v1
        review_protocol_ref: protocols/eval-review-v1
        approval_protocol_ref: null
      notes: null
```

### Why this is better than inventing a new construct

You do not need a special construct like `evaluation_supervision` or `migration_review_gate`. The combined semantics are already captured by:

- one `feature_cell` workstream wrapper
- one workstream-level control profile
- one slice-level strengthening profile

---

## Example 6: high-assurance work without a feature cell

### Situation

A single security-sensitive change is relatively self-contained, but it requires strong evidence, strong traceability, explicit approval, and visible rollback planning.

### Why this is not a feature cell

The work is still essentially one slice. It does not need a long-horizon workstream wrapper.

### Why this is `high_assurance`

The control burden is stronger than ordinary review or ordinary change control:

- strict evidence,
- strict traceability,
- explicit approval,
- rollback visibility,
- security-sensitive transition class.

### Layer sketch

- **Layer B** might be `routine_implementer` or `migration_operator`, depending on the slice
- **Layer C** is a slice-level `high_assurance` profile
- **Layer D** may enter `awaiting_approval` before execution or closure

### Layer C record

```yaml
layer_c:
  feature_cell: null
  control_profiles:
    - scope: slice
      reason: security-sensitive change requires strict evidence, approval, and rollback discipline
      entered_at: 2026-03-06
      preset_refs: [high_assurance]
      review:
        required: true
        trigger_classes: [architecture_review]
      approval:
        required: true
        trigger_classes: [security_sensitive_change]
      evidence:
        level: strict
      traceability:
        level: strict
        decision_log_required: true
      rollback:
        required: true
        rollback_ref: docs/runbooks/security-change-rollback.md
      policy_refs:
        policy_profile_ref: policies/high-assurance-security-v1
        packet_template_ref: templates/high-assurance-review-packet-v1
        review_protocol_ref: protocols/security-review-v1
        approval_protocol_ref: protocols/security-approval-v1
      notes: null
```

### Important boundary note

Do not create a `feature_cell` merely because the control burden is strong. A `feature_cell` is about workstream continuity, not about seriousness.

---

## Example 7: when not to invent a new preset

### Situation

A team is tempted to introduce a new preset such as `migration_reviewed` because migrations often need review and approval.

### Better approach

Check whether the actual semantics are already expressible with:

- `change_controlled`
- `reviewed`
- `high_assurance`
- or explicit normalized fields

In most cases, the answer is yes.

### Example explicit profile

```yaml
layer_c:
  feature_cell: null
  control_profiles:
    - scope: workstream
      reason: migration requires both architecture review and explicit rollout approval
      entered_at: 2026-03-06
      preset_refs: []
      review:
        required: true
        trigger_classes: [architecture_review]
      approval:
        required: true
        trigger_classes: [rollout, cutover]
      evidence:
        level: elevated
      traceability:
        level: elevated
        decision_log_required: true
      rollback:
        required: true
        rollback_ref: docs/runbooks/migration-rollback.md
      inherits_to_children: true
      applies_to: selected_slices
      policy_refs:
        policy_profile_ref: policies/migration-control-v1
        packet_template_ref: templates/migration-packet-v1
        review_protocol_ref: protocols/migration-review-v1
        approval_protocol_ref: protocols/migration-approval-v1
      notes: null
```

### Why this is preferable

This avoids ontology sprawl. The semantics remain explicit and the preset vocabulary stays small.

---

## Common mistakes highlighted by the examples

### Mistake 1: assuming feature cell implies stricter control

It does not. A `feature_cell` is about continuity across slices and time.

### Mistake 2: assuming reviewed implies current checkpoint

It does not. It defines the control regime. Current status belongs in Layer D.

### Mistake 3: assuming change-controlled means permanent approval blocking

It does not. It means approval is required at defined trigger classes.

### Mistake 4: creating new named constructs for mixed cases

Usually unnecessary. Compose:

- one `feature_cell` if needed
- one or more `control_profile` records
- Layer B mode per slice
- Layer D state per tracked item

### Mistake 5: using high-assurance as a badge

Use `high_assurance` only when the actual discipline is materially stronger.

---

## Summary

These examples show the main Layer C patterns:

- no `feature_cell` wrapper + baseline control
- no `feature_cell` wrapper + reviewed slice
- feature cell + implicit baseline
- feature cell + workstream-level change control
- feature cell + workstream control + slice-local strengthening
- no `feature_cell` wrapper + high-assurance slice
- explicit mixed profiles without preset proliferation

The general rule is:

- add `feature_cell` for continuity across time and slices
- add `control_profile` for explicit control burden
- prefer composition over new ontology
- keep Layer C cleanly separated from both Layer B modes and Layer D states
