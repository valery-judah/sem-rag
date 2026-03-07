# Layer C v1.1 Historical Note

## Status

Superseded historical reference

## Current reference

Layer C v2 is defined in:

- `docs/harness/concepts/layer-c/README.md`
- `docs/harness/concepts/layer-c/control-profiles.md`
- `docs/harness/concepts/layer-c/feature-cell.md`
- `docs/harness/concepts/layer-c/presets.md`
- `docs/harness/concepts/layer-c/schema.md`
- `docs/harness/concepts/layer-c/examples.md`

## Why this file still exists

This file documented the older v1.1 Layer C framing built around overlay labels such as `review_gatekeeper` and `governance_escalation`.

That framing is no longer the canonical model.

The current Layer C v2 model uses:

- `feature_cell` as the canonical workstream wrapper
- `control_profile` as the canonical control object
- a small preset vocabulary (`baseline`, `reviewed`, `change_controlled`, `high_assurance`) as ergonomic aliases

## Migration summary

Use the v2 docs when reading or editing live harness guidance.

Interpret older v1.1 references as historical shorthand only:

- `review_gatekeeper` -> usually a reviewed-style `control_profile`
- `governance_escalation` -> usually a change-controlled or high-assurance `control_profile`
- `feature_cell` -> remains the canonical workstream wrapper

## Boundary reminder

Layer C defines the workstream wrapper and control regime.

It does not define:

- Layer A problem shape
- Layer B current operating mode
- Layer D current lifecycle state

## Historical note

The older overlay/container framing was useful during early harness iteration, but it has been superseded by the v2 mini-spec because the v2 model is smaller, more explicit, and more mechanically legible.
