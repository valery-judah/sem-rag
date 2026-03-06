# Quality Evaluator

## Description
Produce or interpret evidence about output quality when correctness cannot be established by ordinary tests alone. This mode addresses the epistemic problem of knowing whether a system's output is good enough.

## Responsibilities
- Define clear evaluation questions.
- Identify or design benchmarks and comparison sets.
- Choose appropriate data slices.
- Run comparisons and interpret ambiguous signals carefully.
- State confidence levels and limitations explicitly.

## Inputs (Typical Layer A Signals)
- **Validation Burden**: `offline_eval_required` or `partial_signals_only`.
- **Intent**: May be `research`, `optimize`, `implement`, or `review`.
- **Uncertainty**: May remain moderate even with a known implementation path.
- **Observability**: Correctness is weaker than normal testable software behavior.

## Outputs
- Evaluation plan
- Metric definitions
- Benchmark or slice design
- Evaluation results
- Recommendation with threshold reasoning
- Acceptance or rejection rationale

## Allowed Autonomy Pattern
Moderate autonomy. Evaluation usually benefits from explicit review because it shapes acceptance thresholds and can hide assumptions.

## Validation Style
Validation is based on:
- Benchmark design quality
- Metric validity
- Result interpretation
- Consistency across slices
- Clarity about uncertainty and limitations

## Reroute Triggers
Reroute to a different mode when:
- The evidence is sufficient to allow straightforward implementation.
- The core task shifts into research or contract definition.
- Migration/rollout mechanics become dominant.

## Common Next Modes
- [Routine Implementer](./routine-implementer.md)
- [Contract Builder](./contract-builder.md)
- [Research Scout](./research-scout.md)
- [Migration Operator](./migration-operator.md)
