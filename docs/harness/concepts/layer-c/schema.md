# Schema

This document defines the **canonical Layer C schema shape** for the refactored model.

Layer C has two canonical first-class constructs:

- `feature_cell`
- `control_profile`

This file provides:

- the normalized structure,
- field-level validation expectations,
- composition rules,
- migration guidance from Layer C v1.1,
- and implementation notes for repository-local serialization.

It is the schema companion to:

- `README.md`
- `feature-cell.md`
- `control-profiles.md`
- `presets.md`

## Purpose

The schema exists to make Layer C:

- explicit,
- machine-legible,
- mechanically validatable,
- portable across repositories,
- and cleanly separated from Layer A, Layer B, and Layer D.

This is a **semantic schema** first. A repository may choose YAML, JSON, Python dataclasses, Pydantic models, markdown frontmatter, or another representation. The semantic fields and invariants should remain stable even if the physical format differs.

## Canonical top-level model

A Layer C record set may contain:

- zero or one `feature_cell` for a workstream,
- zero or more `control_profile` records.

Canonical conceptual shape:

```yaml
layer_c:
  feature_cell: <feature_cell | null>
  control_profiles:
    - <control_profile>
```

Representation rules:

- use `feature_cell: null` when no workstream wrapper is active
- use `control_profiles: []` when baseline control is implied and no explicit profile is materialized
- use `null` for absent scalar refs
- use `[]` for empty collections

This shape is conceptual. A repository may store the two construct types in separate files or directories.

## Canonical object schemas

## `feature_cell`

The value of `layer_c.feature_cell` is:

```yaml
scope: workstream
slug: <string>
title: <string>
goal: <string>
reason: <string>
entered_at: YYYY-MM-DD

status_ref: <string | null>
operating_package_ref: <string | null>

slices_ref:
  - <string>

milestones:
  - <string>

decision_log_ref: <string | null>
handoff_ref: <string | null>
evidence_refs:
  - <string>

control_profile_refs:
  - <string>

notes: <string | null>
```

## `control_profile`

Each item in `layer_c.control_profiles[]` is:

```yaml
scope: slice | workstream
reason: <string | null>
entered_at: YYYY-MM-DD

preset_refs:
  - baseline | reviewed | change_controlled | high_assurance

review:
  required: true | false
  trigger_classes:
    - tradeoff_review
    - findings_interpretation
    - architecture_review
    - acceptance_interpretation
    - scope_change
    - ambiguous_eval
    - non_local_refactor

approval:
  required: true | false
  trigger_classes:
    - cutover
    - rollout
    - contract_break
    - irreversible_change
    - closure
    - security_sensitive_change

evidence:
  level: standard | elevated | strict

traceability:
  level: standard | elevated | strict
  decision_log_required: true | false

rollback:
  required: true | false
  rollback_ref: <string | null>

inherits_to_children: true | false
applies_to: all_slices | selected_slices | null

policy_refs:
  policy_profile_ref: <string | null>
  packet_template_ref: <string | null>
  review_protocol_ref: <string | null>
  approval_protocol_ref: <string | null>

notes: <string | null>
```

The inheritance fields are meaningful only for workstream-scope profiles.

## Required vs optional fields

## `feature_cell`

### Required

- `scope`
- `slug`
- `title`
- `goal`
- `reason`
- `entered_at`

### Optional but commonly useful

- `status_ref`
- `operating_package_ref`
- `slices_ref`
- `milestones`
- `decision_log_ref`
- `handoff_ref`
- `evidence_refs`
- `control_profile_refs`

### Optional

- `notes`

## `control_profile`

### Required on every materialized profile

- `scope`
- `entered_at`
- `review.required`
- `review.trigger_classes`
- `approval.required`
- `approval.trigger_classes`
- `evidence.level`
- `traceability.level`
- `traceability.decision_log_required`
- `rollback.required`

### Conditionally required

- `reason`
  - required in practice when the profile adds burden beyond baseline defaults
- `preset_refs`
  - optional; may be omitted or empty when the profile is expressed entirely through explicit fields
- `rollback.rollback_ref`
  - strongly recommended when `rollback.required = true` for higher-risk work
- `inherits_to_children`
  - meaningful only when `scope = workstream`
- `applies_to`
  - meaningful only when `scope = workstream`; should be explicit when `inherits_to_children = true`
- `policy_refs`
  - optional; include when local policy linkage matters

### Baseline guidance

Baseline control is usually represented by **no explicit profile**:

```yaml
layer_c:
  feature_cell: null
  control_profiles: []
```

A repository may materialize an explicit baseline profile when it wants a fully normalized audit trail.

## Semantic invariants

The following invariants should hold regardless of serialization format.

## Global Layer C invariants

1. Layer C must not encode Layer A taxonomy values as substitutes for Layer C constructs.
2. Layer C must not encode Layer B mode names as Layer C semantics.
3. Layer C must not encode current Layer D status as Layer C semantics.
4. Layer C should stay compact: use normalized fields and composition before inventing new construct types or presets.

## `feature_cell` invariants

1. `feature_cell.scope` must always be `workstream`.
2. A workstream should have at most one active canonical `feature_cell` record.
3. A `feature_cell` should represent one coherent workstream, not a loose task bucket.
4. `feature_cell` must not directly embed `control_profile` semantics when refs are sufficient.
5. `feature_cell` must not act as a substitute for slice records.

## `control_profile` invariants

1. `control_profile.scope` must be either `slice` or `workstream`.
2. If `review.required = false`, `review.trigger_classes` should usually be empty.
3. If `approval.required = false`, `approval.trigger_classes` should usually be empty.
4. If `scope = workstream`, `inherits_to_children` should be explicit.
5. If `inherits_to_children = false`, `applies_to` should usually be `null`.
6. If `preset_refs` contains a non-`baseline` preset, `reason` should normally be present.
7. If normalized fields materially differ from a preset's default expansion, the normalized fields remain authoritative.
8. `control_profile` must not contain Layer D state names such as current checkpoint or approval-blocked status.

## Stable enums

Repositories may encode enums differently, but the conceptual value sets below should remain stable.

## `control_profile.preset_refs[]`

Allowed values:

- `baseline`
- `reviewed`
- `change_controlled`
- `high_assurance`

## `control_profile.scope`

Allowed values:

- `slice`
- `workstream`

## `control_profile.applies_to`

Allowed values:

- `all_slices`
- `selected_slices`
- `null`

## `control_profile.evidence.level`

Allowed values:

- `standard`
- `elevated`
- `strict`

## `control_profile.traceability.level`

Allowed values:

- `standard`
- `elevated`
- `strict`

## `feature_cell.scope`

Allowed value:

- `workstream`

## Trigger-class registries

The trigger classes listed in this schema are a **shared starter registry**, not a forever-frozen enum set.

Repositories may extend them, but should do so conservatively and document additions.

## Review trigger classes

Shared starter values:

- `tradeoff_review`
- `findings_interpretation`
- `architecture_review`
- `acceptance_interpretation`
- `scope_change`
- `ambiguous_eval`
- `non_local_refactor`

## Approval trigger classes

Shared starter values:

- `cutover`
- `rollout`
- `contract_break`
- `irreversible_change`
- `closure`
- `security_sensitive_change`

Repositories may add local trigger classes when the distinction is genuinely stable and broadly useful.

## Composition patterns

The following composition patterns are normal.

### Pattern 1: single slice, baseline control, no feature cell

```yaml
layer_c:
  feature_cell: null
  control_profiles: []
```

### Pattern 2: single slice, reviewed profile, no feature cell

```yaml
layer_c:
  feature_cell: null
  control_profiles:
    - scope: slice
      reason: acceptance evidence requires human interpretation
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
        level: standard
        decision_log_required: false
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

### Pattern 3: feature cell plus workstream-level change-controlled profile

```yaml
layer_c:
  feature_cell:
    scope: workstream
    slug: parser-block-schema-migration
    title: Parser migration to structured block schema
    goal: migrate parser outputs to the new block schema with validation and safe rollout support
    reason: staged multi-slice migration with high handoff risk and rollout sensitivity
    entered_at: 2026-03-06
    status_ref: lifecycle/workstreams/parser-block-schema-migration
    operating_package_ref: workstreams/parser-block-schema-migration/README.md
    slices_ref:
      - tasks/define-block-schema.md
      - tasks/refactor-parser-model.md
    milestones:
      - target schema finalized
      - rollout packet prepared
    decision_log_ref: workstreams/parser-block-schema-migration/decision-log.md
    handoff_ref: workstreams/parser-block-schema-migration/handoff.md
    evidence_refs:
      - reports/parser-migration-validation.md
    control_profile_refs:
      - layer-c/control-profiles/parser-migration-change-controlled.yaml
    notes: null
  control_profiles:
    - scope: workstream
      reason: rollout and cutover require explicit approval and rollback evidence
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

### Pattern 4: feature cell with stronger slice-local profile

```yaml
layer_c:
  feature_cell: <feature_cell>
  control_profiles:
    - <workstream-level change-controlled profile>
    - scope: slice
      reason: acceptance evidence for this slice is ambiguous and needs review
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

## Validation guidance by implementation style

## YAML / JSON storage

Recommended checks:

- enum validation for stable fields,
- required field presence,
- date format validation,
- no unknown top-level keys unless explicitly allowed,
- no Layer D status strings in control fields,
- no Layer B mode strings used as control semantics.

## Python dataclasses / Pydantic

Recommended checks:

- model-level validation for conditional requirements,
- enum types for preset names and stable value sets,
- collection defaults that avoid accidental mutation,
- explicit validators for inheritance and reason requirements.

## Markdown frontmatter or mixed-doc storage

Recommended checks:

- frontmatter schema validation,
- reference existence checks where possible,
- lints for missing `reason`, invalid preset names, and invalid stable enums.

## Migration from Layer C v1.1

The old canonical set was:

- `review_gatekeeper`
- `governance_escalation`
- `feature_cell`

The refactored schema maps them as follows.

## `review_gatekeeper`

Map to a `control_profile` with:

- `preset_refs: [reviewed]`
- `review.required = true`
- appropriate `review.trigger_classes`
- usually `evidence.level = elevated`

## `governance_escalation`

Map to a `control_profile` with either:

- `preset_refs: [change_controlled]`, or
- `preset_refs: [high_assurance]`

Choose based on actual burden.

- use `change_controlled` when transition approval and rollback control are primary,
- use `high_assurance` when strict evidence and traceability are also central.

## `feature_cell`

`feature_cell` retains its canonical role with no fundamental semantic change. The main difference is that it now composes explicitly with `control_profile` refs rather than being interpreted alongside ad hoc overlay labels.

## Representation options

The schema does **not** require one storage pattern.

Reasonable repository-local representations include:

### Option 1: one Layer C bundle per workstream or slice context

```yaml
layer_c:
  feature_cell: ...
  control_profiles: ...
```

### Option 2: separate directories

```text
layer-c/
  feature-cells/
  control-profiles/
```

### Option 3: embedded frontmatter in task or workstream docs

Store Layer C objects as frontmatter blocks while preserving the same semantic fields.

Choose the representation that best matches the repository's broader control and artifact model.

## Anti-patterns

### 1. Treating schema fields as mere documentation

The point of the schema is operational consistency, not decorative structure.

### 2. Letting preset names replace explicit fields

Presets are useful shorthand, but the normalized fields should always be recoverable and authoritative.

### 3. Hiding Layer D state in freeform fields

If a case is really about current state, record it in Layer D.

### 4. Introducing many local enums too early

Keep extension points available, but avoid unnecessary ontology growth.

## Summary

Use this schema to keep Layer C:

- explicit,
- normalized,
- small in ontology,
- composable with Layer B and Layer D,
- and implementable in whichever storage format the repository prefers.
