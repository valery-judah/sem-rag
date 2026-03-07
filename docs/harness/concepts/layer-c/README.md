# Layer C: Workstream Containers and Control Profiles

This directory is the canonical **Layer C v2** reference for the harness model.

Layer C records the **control regime** and **workstream wrapper** that apply to work without redefining:

- the current slice classification from Layer A,
- the current operating posture from Layer B,
- or the current lifecycle control status from Layer D.

It answers questions such as:

- what explicit review or approval obligations apply,
- what evidence or traceability burden is required,
- whether rollback expectations must be visible,
- whether work should be wrapped as a long-horizon workstream.

The older [`layer-c-overlays-containers.md`](../layer-c-overlays-containers.md) remains as a historical pointer for the v1.1 model. Use this directory as the current reference, and use `docs/harness/maintainining.md` for ongoing compatibility and migration policy.

## What Layer C does

Layer C keeps two concerns explicit and separate:

1. **Workstream wrapper**: whether the work should be carried through time as a coherent container.
2. **Control regime**: what explicit review, approval, evidence, traceability, or rollback obligations constrain that work.

The canonical Layer C constructs are:

- `feature_cell`
- `control_profile`

`feature_cell` is the canonical workstream container.

`control_profile` is the canonical control object.

Preset names such as `baseline` or `change_controlled` are ergonomic summaries only. They are not separate Layer C construct types.

## Layer boundaries

Keep these boundaries sharp.

### Layer C is not Layer A

Layer A records the **shape of the current slice**: uncertainty, validation burden, execution horizon, reversibility, risk, and related descriptors.

Layer C is a downstream decision made from those signals.

Examples:

- high validation ambiguity in Layer A may justify a reviewed `control_profile`,
- low reversibility in Layer A may justify a change-controlled `control_profile`,
- multi-slice execution horizon in Layer A may justify a `feature_cell`.

### Layer C is not Layer B

Layer B answers:

> How should the agent work now?

Layer C does not define the current operating mode. It wraps or constrains work being done in a Layer B mode.

Examples:

- `contract_builder` under a reviewed `control_profile`,
- `migration_operator` under a change-controlled `control_profile`,
- a `feature_cell` containing slices that move through several Layer B modes over time.

### Layer C is not Layer D

Layer D answers:

> What is the current execution-control status?

Layer C defines the **regime** under which work proceeds. Layer D defines the **current gate or status** inside that regime.

Examples:

- a reviewed `control_profile` may later cause a slice to enter `checkpoint`,
- a change-controlled `control_profile` may later cause a slice to enter `awaiting_approval`,
- a `feature_cell` may justify tracking both slice-scope and workstream-scope Layer D records,
- but none of those Layer C constructs is itself a Layer D state.

Do not let Layer C become a hidden state machine.

## Canonical constructs

### `feature_cell`

`feature_cell` is the Layer C workstream wrapper.

Use it when work is:

- multi-slice,
- long-running,
- high-handoff,
- high-continuity,
- or otherwise needs workstream-level visibility and resumability.

`feature_cell` is about continuity across time and slices. It is not:

- a Layer B mode,
- a Layer D state,
- a substitute for slices,
- or a heavyweight PM methodology.

### `control_profile`

`control_profile` is the Layer C control object.

Use it when work carries explicit obligations such as:

- review required,
- approval required,
- elevated evidence,
- elevated traceability,
- visible rollback planning,
- references to local policy mechanics.

`control_profile` records the regime, not the current gate.

## Preset names

The recommended preset set stays small:

- `baseline`
- `reviewed`
- `change_controlled`
- `high_assurance`

Interpret them as shorthand only:

- `baseline`: no additional Layer C control burden beyond local defaults
- `reviewed`: human review is required at defined interpretation or continuation boundaries
- `change_controlled`: explicit approval is required at defined risky transitions
- `high_assurance`: strong review, approval, evidence, traceability, and rollback discipline are required

Important boundary reminders:

- `reviewed` does not mean "currently in review"
- `change_controlled` does not mean "currently awaiting approval"
- `high_assurance` is not a seriousness badge

Current status always belongs in Layer D.

## Canonical bundle shape

When Layer C is serialized as one bundle, use this conceptual shape:

```yaml
layer_c:
  feature_cell: <feature_cell | null>
  control_profiles:
    - <control_profile>
```

Representation rules used throughout this directory:

- `feature_cell: null` means no workstream wrapper is active
- `control_profiles: []` means baseline control is implied and no explicit control profile has been materialized
- `null` is used for absent scalar refs
- `[]` is used for empty collections

Repositories may choose different physical storage, but the semantics should stay aligned with this shape.

## Scope and inheritance

Layer C supports two scope values:

- `slice`
- `workstream`

Use `slice` when the control regime applies only to the current executable unit.

Use `workstream` when the wrapper or control regime applies across multiple slices over time.

Inheritance applies only to **workstream-scope** `control_profile` records. It must be explicit, never inferred.

Use fields such as:

- `inherits_to_children: true | false`
- `applies_to: all_slices | selected_slices | null`

Do not put inheritance fields on `feature_cell`.

## Composition rules

Prefer composition over ontology growth.

A workstream may contain:

- one `feature_cell`,
- zero or more `control_profile` records,
- one current Layer B mode per slice,
- one current Layer D status per tracked item.

If a case can be expressed by:

- Layer A descriptors,
- one current Layer B mode,
- one `feature_cell` if needed,
- one or more `control_profile` records,
- and Layer D state plus workflow-local `phase`,

then do that instead of inventing another Layer C construct or preset.

## File guide

- `feature-cell.md`: container semantics and workstream-wrapper guidance
- `control-profiles.md`: normalized control model and invariants
- `presets.md`: preset aliases and default expansions
- `schema.md`: canonical structure and validation rules
- `examples.md`: worked Layer C compositions

Recommended reading order:

1. Read this file for the Layer C boundary and top-level map.
2. Read `feature-cell.md` for workstream-wrapper questions.
3. Read `control-profiles.md` for control-obligation questions.
4. Read `schema.md` for canonical structure and invariants.
5. Read `presets.md` for ergonomic aliases.
6. Read `examples.md` for concrete patterns.

## Migration note from Layer C v1.1

The older Layer C v1.1 model used overlay-era labels such as `review_gatekeeper` and `governance_escalation`.

In v2, live Layer C guidance should use `feature_cell` plus `control_profile` semantics instead. Use `docs/harness/maintainining.md` for the historical mapping and compatibility policy while the repository still carries legacy card shorthand.
