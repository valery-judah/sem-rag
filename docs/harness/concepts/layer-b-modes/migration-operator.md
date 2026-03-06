# Migration Operator

## Description
Execute or prepare rollout-sensitive transitions where sequencing, compatibility, reversibility, and operational safety matter. This mode is control-first and sequencing-aware, utilized for structural changes that require more than ordinary implementation.

## Responsibilities
- Define ordered stages for the transition.
- Preserve compatibility across components where necessary.
- Plan rehearsal and rollback strategies.
- Surface irreversible points or hard state transitions.
- Specify go/no-go checks.
- Avoid casual execution on inherently risky transitions.

## Inputs (Typical Layer A Signals)
- **Intent**: `migrate`, or another intent with migration-shaped mechanics.
- **Blast Radius**: `subsystem`, `cross_service`, or `platform`.
- **Reversibility**: `hard` or `irreversible`.
- **Sensitivity**: `data_integrity`, `security`, or `compliance`.
- **Validation Burden**: `production_confirmation_required` or rehearsal-heavy testing.
- **Dependency Complexity**: Often `cross_service` or `external_or_multi_party`.

## Outputs
- Migration plan
- Stage or phase breakdown
- Compatibility notes
- Rollback plan
- Cutover checklist
- Rehearsal evidence
- Controlled implementation slices

## Allowed Autonomy Pattern
Usually lower autonomy than ordinary implementation. High-risk migrations should often run inside stronger Layer C governance overlays and may require explicit approval states in Layer D.

## Validation Style
Validation often relies on:
- Migration rehearsal
- Compatibility checks
- Staged rollout signals
- Manual verification
- Explicit go/no-go criteria

## Reroute Triggers
Reroute to a different mode when:
- The risky transition has been fully decomposed into safe local slices (standard implementation).
- The main remaining problem is contract clarification.
- Evidence production becomes the primary task.

## Common Next Modes
- [Routine Implementer](./routine-implementer.md)
- [Contract Builder](./contract-builder.md)
- [Quality Evaluator](./quality-evaluator.md)
