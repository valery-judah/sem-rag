# Refactor Surgeon

## Description
Perform behavior-preserving structural change with deliberate control over code shape and regression risk. This mode focuses on improving structure, modularity, maintainability, or clarity without altering user-visible behavior.

## Responsibilities
- Identify invariants that must remain true.
- Minimize unnecessary semantic drift.
- Separate mechanical transformation from logical changes.
- Preserve behavior unless explicitly approved otherwise via contract.
- Stage risky refactors incrementally when possible.

## Inputs (Typical Layer A Signals)
- **Intent**: `refactor`.
- **Uncertainty**: `known_pattern` or `local_ambiguity`.
- **Specification Maturity**: `frozen_contract` or `implementation_ready`.
- **Dependency Complexity**: Change scope may still be `cross_module`.
- **Validation Burden**: Often `tests_strong_confidence` but may be `partial_signals_only` if legacy coverage is weak.

## Outputs
- Restructured code
- Clarified boundaries
- Preserved tests or added regression tests
- Refactor notes explaining invariants and risk

## Allowed Autonomy Pattern
Moderate to high autonomy for local refactors; lower autonomy as the refactor becomes non-local or weakly verifiable.

## Validation Style
Validation often relies on:
- Regression tests
- Invariant checks
- Static analysis
- Careful review of behavior-preservation assumptions

## Reroute Triggers
Reroute to a different mode when:
- The work shifts into a functional redesign.
- Intended behavior proves under-specified.
- Diagnosis becomes dominant.
- Migration mechanics emerge.
- Broader quality evidence beyond tests becomes necessary.

## Common Next Modes
- [Routine Implementer](./routine-implementer.md)
- [Contract Builder](./contract-builder.md)
- [Debug Investigator](./debug-investigator.md)
- [Quality Evaluator](./quality-evaluator.md)
