# Presets

This document defines the recommended **Layer C control-profile presets**.

Presets are ergonomic aliases for common control configurations. They exist to make Layer C easier to read and apply, but they are **not** the source of truth. The authoritative meaning of a control regime lives in the normalized `control_profile` fields.

Use this file when you need to answer questions such as:

- Which preset should be used for a given case?
- What does `reviewed` or `change_controlled` mean by default?
- When should a preset be avoided in favor of explicit fields only?
- How should presets expand into normalized control-profile fields?

## Purpose

Presets provide:

- a small shared vocabulary,
- quick human legibility,
- repeatable default expansions,
- and lightweight shorthand for common control regimes.

They should reduce friction, not hide semantics.

## Design rules

### 1. Presets summarize; normalized fields decide

A preset is an alias for a common shape of explicit fields.

The following remain authoritative:

- `review.required`
- `approval.required`
- `evidence.level`
- `traceability.level`
- `rollback.required`
- other explicit `control_profile` fields

Do not infer more than the normalized fields actually say.

### 2. Keep the preset set small

The recommended preset set is intentionally minimal:

- `baseline`
- `reviewed`
- `change_controlled`
- `high_assurance`

Avoid adding many specialized presets early.

### 3. Use presets for common shapes only

A preset is helpful when it captures a recurring pattern.

If the case is unusual or materially mixed, express it with explicit fields and either:

- omit presets entirely, or
- include a preset only as a rough summary while relying on normalized fields for the actual meaning.

### 4. Baseline is often implied

If a Layer C bundle has no explicit control burden, prefer:

```yaml
layer_c:
  feature_cell: null
  control_profiles: []
```

Repositories may still materialize an explicit baseline profile when they want a fully normalized record. In that case, `preset_refs: [baseline]` is fine.

### 5. Presets do not replace `reason`

A preset name is not a justification.

When a profile adds real control burden, it should still record why that burden exists.

## Recommended preset set

## `baseline`

### Meaning

No additional Layer C control burden beyond local defaults.

### Typical use cases

- local refactor with ordinary validation,
- routine implementation slice,
- documentation update,
- low-risk change with ordinary reversibility.

### Default expansion when materialized explicitly

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

### Notes

`baseline` should not be used as a placeholder for uncertainty about what controls are needed. If additional burden is clearly required, choose a stronger preset or set fields explicitly.

## `reviewed`

### Meaning

Human review is required at defined interpretation or continuation boundaries.

`reviewed` is the preset for work where autonomous progress is allowed up to certain points, but human interpretation is needed before continuing or accepting results.

### Typical use cases

- design tradeoff review,
- architecture review,
- findings interpretation,
- ambiguous evaluation outcomes,
- acceptance evidence that needs human judgment.

### Default expansion

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

### Notes

`reviewed` does **not** mean:

- currently waiting for review,
- blocked on reviewer response,
- or globally high-risk work.

Those meanings belong elsewhere:

- current status belongs in Layer D,
- higher-risk transition control may require `change_controlled` or `high_assurance`.

## `change_controlled`

### Meaning

Explicit approval is required for defined risky transitions, usually with elevated evidence, stronger traceability, and visible rollback expectations.

`change_controlled` is the preset for work where certain steps should not proceed autonomously because the transition is difficult to reverse, broad in impact, or contract-sensitive.

### Typical use cases

- staged migrations,
- rollout-sensitive changes,
- shared contract changes,
- risky cutovers,
- difficult-to-reverse operational changes.

### Default expansion

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

### Notes

`change_controlled` is primarily about **transition control**.

Use it when the key question is:

> Can we safely make this transition now?

Do not use it for ordinary review-oriented cases where interpretation matters but explicit approval is not the main issue.

`change_controlled` does **not** mean the work is always awaiting approval. Current gate or status still belongs in Layer D.

## `high_assurance`

### Meaning

Strict evidence, traceability, review, approval, and rollback discipline are required.

`high_assurance` is the strongest standard preset. Use it when the work has unusually high consequence, unusually strong auditability needs, or unusually strict recovery expectations.

### Typical use cases

- security-sensitive change,
- high-blast-radius migration,
- work with strong audit expectations,
- difficult-to-reverse changes with strong validation burden,
- changes where both review and approval discipline should be explicit and strong.

### Default expansion

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

### Notes

`high_assurance` should be used sparingly. It should signal meaningfully stronger discipline than `change_controlled`, not just general seriousness.

## Choosing among presets

A practical decision rule:

- use `baseline` when ordinary engineering discipline is enough,
- use `reviewed` when human interpretation or continuation control is the main additional burden,
- use `change_controlled` when explicit authorization for risky transitions is the main additional burden,
- use `high_assurance` when the work needs strong review, strong approval, strong evidence, and strong traceability together.

## When to avoid presets

Avoid relying on presets alone when:

- the case is materially mixed,
- the default trigger classes do not fit,
- evidence or traceability expectations differ significantly from the default,
- local rollback expectations are unusually specific,
- or the repository needs a very explicit machine-readable record.

In these cases, use normalized fields directly. A preset may still be included as a rough summary, but the explicit fields should carry the actual meaning.

## Mixed examples

### Example 1: reviewed with stronger traceability

A repository may use `reviewed` as the summary but still tighten fields:

```yaml
preset_refs: [reviewed]
review:
  required: true
  trigger_classes:
    - acceptance_interpretation
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
```

### Example 2: no preset, explicit-only profile

When the case does not fit a standard preset cleanly:

```yaml
preset_refs: []
review:
  required: true
  trigger_classes:
    - findings_interpretation
approval:
  required: true
  trigger_classes:
    - closure
evidence:
  level: elevated
traceability:
  level: elevated
  decision_log_required: true
rollback:
  required: false
  rollback_ref: null
```

This is valid and often preferable to forcing a misleading preset.

## Validation guidance

At minimum, repositories should enforce:

1. Unknown preset names are invalid.
2. Presets must not be treated as the sole semantic record when normalized fields are present.
3. If normalized fields materially differ from a preset's default expansion, the normalized fields win.
4. If `preset_refs` contains a non-`baseline` preset, a concrete `reason` is strongly recommended.
5. Repositories should avoid defining many near-duplicate presets.

## Anti-patterns

### 1. Using presets as states

Bad:

- `reviewed` meaning currently waiting at checkpoint
- `change_controlled` meaning currently blocked on approval

Those are Layer D semantics.

### 2. Using presets as badges of seriousness

Bad:

- applying `high_assurance` because work feels important,
- without corresponding strict evidence and traceability discipline.

### 3. Hiding unusual semantics behind a familiar preset

Bad:

- labeling a case `reviewed` while also requiring multiple approval transitions,
- but not reflecting that in normalized fields.

### 4. Preset proliferation

Bad:

- `security_reviewed`
- `release_reviewed`
- `migration_escalated`
- `research_supervised`

Prefer normalized fields plus policy refs unless a new preset is clearly stable, common, and cross-cutting.

## Summary

Use presets as a **small ergonomic vocabulary** for common `control_profile` shapes.

Keep them:

- small in number,
- secondary to normalized fields,
- easy to expand mechanically,
- and clearly separated from both Layer D state and local process manuals.
