# Contract Builder

## Description
Transform a partly known problem into an implementation-ready contract. This mode is used when the objective is broadly known but the implementation contract is not yet mature enough for execution.

## Responsibilities
- Turn vague requests into a bounded contract.
- Make assumptions explicit.
- Separate goals, non-goals, constraints, and open questions.
- Propose interfaces, acceptance criteria, and task decomposition into slices.
- Identify key decisions that must be made before implementation starts.

## Inputs (Typical Layer A Signals)
- **Specification Maturity**: `scoped_problem` or `draft_contract`.
- **Uncertainty**: `local_ambiguity` or `design_heavy`.
- **Intent**: `implement`, `refactor`, `review`, or `migrate`.
- **Dependency Complexity**: Often `cross_module` or greater.
- **Knowledge Locality**: Often `mostly_local` or `scattered_internal`.

## Outputs
- Scoped contract
- Acceptance criteria
- Interface or schema proposal
- Decomposition into manageable slices
- Risk notes
- Explicit open questions
- Recommendation for next execution mode

## Allowed Autonomy Pattern
Moderate autonomy with strong checkpoint discipline. The agent can shape the contract, but material trade-offs or unclear intended behavior often justify checkpoint review.

## Validation Style
Validation is mostly based on:
- Internal consistency
- Coverage of goals and non-goals
- Decision clarity
- Reviewability
- Readiness for downstream execution

## Reroute Triggers
Reroute to a different mode when:
- The contract is frozen or implementation-ready.
- Behavior-preserving restructuring becomes the main task.
- Migration sequencing becomes dominant.
- The remaining work is direct execution.

## Common Next Modes
- [Routine Implementer](./routine-implementer.md)
- [Refactor Surgeon](./refactor-surgeon.md)
- [Migration Operator](./migration-operator.md)
- [Quality Evaluator](./quality-evaluator.md) (for eval-heavy contract definition)
