# Control Profiles

This document defines **`control_profile`** as the canonical Layer C control object.

A `control_profile` records the **additional control obligations** under which work proceeds. It does not redefine the work itself, the current operating mode, or the current lifecycle state.

Use this file when you need to answer questions such as:

- Does this slice require human review before continuation?
- Does this transition require explicit approval?
- How much evidence and traceability are required?
- Does rollback planning need to be explicit?
- Do these obligations apply only to one slice or across a workstream?

## Purpose

`control_profile` exists to make control expectations:

- explicit,
- normalized,
- composable,
- machine-legible,
- and separate from both routing and state.

It replaces older high-compression Layer C labels such as:

- `review_gatekeeper`
- `governance_escalation`

Those labels hid multiple distinct obligations inside one name. A normalized control object makes the actual regime visible.

## Boundary

Keep these distinctions strict.

### Not Layer A

Layer A explains **why** a slice has a certain shape: uncertainty, ambiguity, risk, reversibility, blast radius, execution horizon, and related factors.

A `control_profile` is a downstream response to those characteristics. It must not erase them.

### Not Layer B

Layer B defines the current operating posture.

A `control_profile` does not answer:

> What should the agent do now?

It answers:

> Under what control regime may the work proceed?

### Not Layer D

Layer D defines the current execution-control status.

A `control_profile` is not a state.

Examples:

- `review.required = true` may later cause entry into a Layer D checkpoint,
- `approval.required = true` may later cause entry into `awaiting_approval`,
- but the `control_profile` itself is not a checkpoint or approval state.

Do not encode current workflow status in Layer C.

## Core design rules

### 1. Normalize obligations instead of hiding them in labels

The meaning of a `control_profile` should be recoverable from its fields.

Preset aliases are allowed for convenience, but normalized fields remain authoritative.

### 2. Scope is mandatory

Every `control_profile` must declare whether it applies at:

- `slice` scope, or
- `workstream` scope.

Never leave scope implicit.

### 3. Baseline is usually implicit

If no additional Layer C control burden is being added, prefer **no materialized control profile**.

That means a Layer C bundle will usually represent baseline as:

```yaml
layer_c:
  feature_cell: null
  control_profiles: []
```

A repository may still materialize an explicit baseline record when it wants a fully normalized audit trail. In that case:

- `preset_refs: [baseline]` is allowed,
- `reason: null` is allowed,
- and the normalized fields should reflect no additional burden.

### 4. Reason is required for non-baseline control

If a profile adds obligations beyond local defaults, it should record why.

The reason should be concrete and operational, not ceremonial.

Good examples:

- acceptance evidence requires human interpretation
- rollout is difficult to reverse
- migration touches shared contracts
- security-sensitive change requires explicit approval

Bad examples:

- process
- governance
- best practice

### 5. Inheritance is explicit and workstream-only

Workstream-level profiles may affect child slices, but that must be declared. It must never be inferred from scope alone.

Inheritance fields are meaningful only for workstream-scope profiles:

- `inherits_to_children`
- `applies_to`

Do not put those fields on slice-scope profiles.

### 6. Policy mechanics stay referenced

Layer C may reference local policy artifacts, but it should not embed organization-specific reviewer rosters, approval chains, or long procedural narratives.

### 7. Prefer composition over new ontology

If a case can be represented by normalized fields on a `control_profile`, do that instead of inventing a new Layer C construct or preset.

## Canonical object shape

When shown on its own, a `control_profile` object should match one item from `layer_c.control_profiles[]`:

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

Notes on this shape:

- `preset_refs` may be empty
- `inherits_to_children` and `applies_to` are workstream-only
- `policy_refs` is optional and should be present only when local policy linkage matters
- normalized fields remain authoritative even when presets are present

## Field semantics

### `scope`

Declares where the profile applies.

- `slice` means the obligations apply to the current executable unit.
- `workstream` means the obligations apply across multiple slices over time.

### `reason`

Explains why the profile exists.

This should be specific enough that a later reader can understand why the control burden was introduced.

### `entered_at`

Records when the profile was attached.

### `preset_refs`

Optional ergonomic aliases.

These help humans summarize the profile quickly, but the normalized fields remain the source of truth.

Typical values:

- `baseline`
- `reviewed`
- `change_controlled`
- `high_assurance`

### `review`

Models reviewer-mediated interpretation or continuation.

Use this when human judgment is required before a slice proceeds past defined boundaries.

`trigger_classes` should identify the class of event that requires review, not the current status.

Do not encode:

- current reviewer,
- current review outcome,
- current checkpoint state.

### `approval`

Models explicit approval requirements for risky transitions.

Use this when certain transitions cannot proceed autonomously.

`trigger_classes` should identify the class of transition requiring approval.

Do not use `approval` just because a human is casually informed or copied on work.

### `evidence`

Defines the expected burden of supporting evidence.

Recommended levels:

- `standard`
- `elevated`
- `strict`

### `traceability`

Defines how strongly decisions, changes, and evidence must be linked.

Use `decision_log_required` when the regime requires visible decision history rather than ordinary local notes.

### `rollback`

Defines whether rollback planning or rollback evidence must be explicit.

Use this when recovery assumptions must be visible rather than implicit.

### `inherits_to_children`

Workstream-only field.

When `true`, the workstream profile is intended to affect child slices.

When `false`, the profile is a workstream-level record only.

### `applies_to`

Workstream-only field.

Narrows how an inherited workstream profile applies:

- `all_slices`
- `selected_slices`
- `null` when inheritance is false

### `policy_refs`

Optional references to local policy artifacts that define repository-specific mechanics.

### `notes`

Optional freeform clarification.

Use sparingly.

## Preset interpretations

Presets are convenience summaries only. They expand into typical field shapes, but the normalized fields remain authoritative.

### `baseline`

Use when no additional Layer C control burden is being added.

Typical expansion when a repository chooses to materialize it explicitly:

```yaml
preset_refs: [baseline]
review:
  required: false
  trigger_classes: []
approval:
  required: false
  trigger_classes: []
evidence:
  level: standard
traceability:
  level: standard
  decision_log_required: false
rollback:
  required: false
  rollback_ref: null
```

### `reviewed`

Use when human review is required at defined interpretation or continuation boundaries.

Typical expansion:

```yaml
preset_refs: [reviewed]
review:
  required: true
  trigger_classes:
    - architecture_review
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
```

### `change_controlled`

Use when risky transitions require explicit approval and stronger transition discipline.

Typical expansion:

```yaml
preset_refs: [change_controlled]
review:
  required: false
  trigger_classes: []
approval:
  required: true
  trigger_classes:
    - rollout
evidence:
  level: elevated
traceability:
  level: elevated
  decision_log_required: true
rollback:
  required: true
  rollback_ref: null
```

### `high_assurance`

Use when approval, evidence, traceability, and rollback expectations are unusually strong.

Typical expansion:

```yaml
preset_refs: [high_assurance]
review:
  required: true
  trigger_classes:
    - architecture_review
approval:
  required: true
  trigger_classes:
    - security_sensitive_change
evidence:
  level: strict
traceability:
  level: strict
  decision_log_required: true
rollback:
  required: true
  rollback_ref: null
```

## Composition rules

A slice or workstream may be subject to multiple control dimensions at once.

Examples:

- review required but no approval required,
- approval required with explicit rollback evidence,
- elevated traceability without a formal review trigger,
- a workstream-level profile plus an additional slice-level reviewed profile.

This is expected.

Do not create a new named construct merely because two or three control obligations co-occur.

## Inheritance rules

### Workstream to slice inheritance

A workstream-level `control_profile` may propagate to child slices only when declared.

Use:

- `inherits_to_children: true`
- `applies_to: all_slices | selected_slices`

When inheritance is selective, the repository should define how the slice set is identified.

### Local strengthening

A child slice may add stricter controls than the inherited workstream baseline.

Example:

- the workstream is `change_controlled`,
- one specific slice is also `reviewed` because acceptance evidence is ambiguous.

### Local weakening

Avoid weakening inherited controls locally unless the repository has an explicit override convention. If such overrides exist, they should be visible and justified.

## Validation rules

At minimum, repositories using this model should enforce:

1. `scope` must be present.
2. `reason` should be present for non-baseline control.
3. `preset_refs` may be empty, but unknown preset names are invalid.
4. `review.required`, `approval.required`, `evidence.level`, `traceability.level`, and `rollback.required` should be present on every materialized profile.
5. If `review.required = false`, `review.trigger_classes` should usually be empty.
6. If `approval.required = false`, `approval.trigger_classes` should usually be empty.
7. If `scope = workstream`, `inherits_to_children` should be explicit.
8. If `inherits_to_children = true`, `applies_to` should be explicit.
9. If `rollback.required = true`, `rollback_ref` is strongly recommended for higher-risk work.
10. Profiles must not contain Layer D state names or Layer B mode names as substitutes for control semantics.

## Anti-patterns

### 1. Using control profiles as status labels

Bad:

- `reviewed` meaning currently waiting for review
- `change_controlled` meaning currently blocked on approval

Those are Layer D semantics.

### 2. Replacing reasons with labels

Bad:

- `preset_refs: [high_assurance]`
- no concrete explanation of why the burden exists

The preset helps summarize. It does not justify the regime.

### 3. Embedding local workflow manuals

Bad:

- listing named reviewers,
- embedding approval org charts,
- writing a full signoff procedure directly into Layer C records.

Reference local policy artifacts instead.

### 4. Inventing new constructs too early

Bad:

- `security_gatekeeper`
- `research_supervision`
- `migration_council`

If the real need can be expressed through normalized fields plus policy refs, do that.

### 5. Confusing review with approval

Review means human interpretation or continuation control.

Approval means explicit authorization for defined transitions.

These often co-occur, but they are not the same.

## Migration from Layer C v1.1

Map older constructs as follows.

### `review_gatekeeper`

Replace with a `control_profile` that usually includes:

- `preset_refs: [reviewed]`
- `review.required = true`
- relevant `review.trigger_classes`
- usually `evidence.level = elevated`

### `governance_escalation`

Replace with a `control_profile` that usually includes either:

- `preset_refs: [change_controlled]`, or
- `preset_refs: [high_assurance]`

Choose based on the actual burden.

Use `change_controlled` when the main issue is approval and safe transition control.

Use `high_assurance` when the work also needs strict evidence and traceability discipline.

## Example object

```yaml
scope: slice
reason: acceptance evidence is ambiguous and requires human interpretation
entered_at: 2026-03-06

preset_refs: [reviewed]

review:
  required: true
  trigger_classes:
    - acceptance_interpretation
    - ambiguous_eval

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

## Summary

Use `control_profile` to model explicit control obligations in Layer C.

Keep it:

- explicit rather than label-heavy,
- scoped rather than implicit,
- composable rather than ontology-heavy,
- referenced rather than procedural,
- and cleanly separated from both Layer B modes and Layer D states.
