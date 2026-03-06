# Debug Investigator

## Description
Diagnose known failing behavior when the root cause is not yet isolated. This mode is diagnosis-first and focuses on narrowing down causal factors rather than prematurely executing direct repairs.

## Responsibilities
- Reproduce or sharpen the failing behavior.
- Narrow the causal search space.
- Test hypotheses effectively.
- Isolate the actual root cause.
- Distinguish symptom from cause.
- Avoid premature fixes before the issue is deeply understood.

## Inputs (Typical Layer A Signals)
- **Intent**: `debug`.
- **Uncertainty**: Often `local_ambiguity` or `design_heavy` at the causal level.
- **Specification Maturity**: May be clear about expected behavior but not about the defect source.
- **Validation Burden**: May be `tests_strong_confidence` (if repro exists) or `partial_signals_only` (if repro is weak).
- **Knowledge Locality**: Often `scattered_internal`.

## Outputs
- Repro notes
- Causal hypotheses
- Narrowed suspect set
- Root-cause explanation
- Recommended or implemented fix (after reroute)

## Allowed Autonomy Pattern
Moderate autonomy with iterative loops. Production-adjacent or incident-like debugging may need stricter control overlays.

## Validation Style
Validation is usually based on:
- Reproduction quality
- Hypothesis elimination
- Fix confirmation against repro
- Regression checks

## Reroute Triggers
Reroute away from this mode when:
- The issue is isolated and only the fix remains.
- The real issue turns out to be contract ambiguity rather than a defect.
- Wide-scale evaluation evidence is required.
- Migration/rollback risks dominate the repair path.

## Common Next Modes
- [Routine Implementer](./routine-implementer.md)
- [Contract Builder](./contract-builder.md)
- [Quality Evaluator](./quality-evaluator.md)
- [Migration Operator](./migration-operator.md)
