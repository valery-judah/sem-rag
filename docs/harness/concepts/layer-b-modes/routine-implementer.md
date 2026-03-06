# Routine Implementer

## Description
Execute a clear, bounded, implementation-ready change with normal engineering discipline. This mode is execution-first and is used when the work is fully ready to be done directly.

## Responsibilities
- Plan only as much as needed for local execution.
- Implement the requested change.
- Add or update relevant tests.
- Run verification and compilation checks.
- Produce a concise implementation summary.

## Inputs (Typical Layer A Signals)
- **Intent**: `implement`.
- **Uncertainty**: `known_pattern` or limited `local_ambiguity`.
- **Specification Maturity**: `frozen_contract` or `implementation_ready`.
- **Validation Burden**: `trivial_local_check` or `tests_strong_confidence`.
- **Blast Radius**: `local` or modest `subsystem`.
- **Execution Horizon**: `one_shot` or bounded `multi_step`.

## Outputs
- Code change
- Added/updated tests
- Short implementation note
- Updated task status
- Validation results

## Allowed Autonomy Pattern
Usually the highest autonomy among the modes, subject to local operating policy and risk bounds.

## Validation Style
Validation is usually:
- Compile/test
- Targeted integration checks
- Localized reasoning over the changed surface

## Reroute Triggers
Reroute away from this mode when:
- Core ambiguity appears during execution.
- The task turns out to be mostly diagnosis.
- Structural refactoring dominates.
- Migration sequencing becomes necessary.
- Tests alone are insufficient to establish confidence.

## Common Next Modes
- [Refactor Surgeon](./refactor-surgeon.md)
- [Debug Investigator](./debug-investigator.md)
- [Migration Operator](./migration-operator.md)
- [Quality Evaluator](./quality-evaluator.md)
- [Contract Builder](./contract-builder.md) (if the spec proves less mature than expected)
