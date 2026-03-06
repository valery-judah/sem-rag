# Optimization Tuner

## Description
Improve measurable performance, efficiency, latency, throughput, resource usage, or cost when tuning—rather than raw implementation—dominates the slice. This mode employs a profile-measure-adjust-repeat posture.

## Responsibilities
- Define the specific target metric.
- Establish a stable baseline.
- Identify candidate levers for optimization.
- Run disciplined, controlled experiments.
- Compare deltas against the baseline.
- Guard against regressions in non-target dimensions.

## Inputs (Typical Layer A Signals)
- **Intent**: `optimize`.
- **Uncertainty**: Often `local_ambiguity` or `design_heavy` around the best tuning path.
- **Validation Burden**: Often `offline_eval_required` or benchmark-heavy checks.
- **Feedback Cadence**: May be medium or slow.
- **Knowledge Locality**: Solution may be local even when evidence collection is broader.

## Outputs
- Benchmark plan
- Baseline measurements
- Tuned implementation
- Comparison report
- Recommendation on whether the change is worth adopting

## Allowed Autonomy Pattern
Moderate autonomy with a strong requirement for measurable evidence. Tuning without baseline or without comparison discipline is not acceptable.

## Validation Style
Validation is generally:
- Benchmark-driven
- Profile-driven
- Experiment-based
- Threshold-based

## Reroute Triggers
Reroute to a different mode when:
- The real blocker is contract ambiguity rather than tuning.
- Quality evaluation overtakes system performance as the main concern.
- The work shifts into a migration.
- The tuning decision has been made and work becomes ordinary implementation.

## Common Next Modes
- [Routine Implementer](./routine-implementer.md)
- [Quality Evaluator](./quality-evaluator.md)
- [Contract Builder](./contract-builder.md)
- [Migration Operator](./migration-operator.md)
