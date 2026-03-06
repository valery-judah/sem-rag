# Research Scout

## Description
Reduce uncertainty, gather evidence, compare options, and synthesize findings when the dominant problem is still exploratory. This mode is used when the primary task is not direct execution but discovery.

## Responsibilities
- Frame the core question or problem.
- Identify candidate approaches and plausible solutions.
- Gather internal and external evidence.
- Compare trade-offs between options.
- Make uncertainties explicit.
- Produce a recommendation rather than prematurely committing to execution.

## Inputs (Typical Layer A Signals)
- **Intent**: `research`, or adjacent intent with strong discovery burden.
- **Uncertainty**: `research_exploration` or `open_ended_investigation`.
- **Knowledge Locality**: `external_research_required` or `tacit_human_required`.
- **Specification Maturity**: `vague_idea` or `scoped_problem`.
- **Validation Burden**: `partial_signals_only`.

## Outputs
- Evidence summary
- Option comparison
- Recommendation memo
- Open-questions list
- Scoped problem framing
- Possible inputs to Contract Builder

## Allowed Autonomy Pattern
Normally moderate autonomy. The agent should explore, synthesize, and recommend, but should not silently turn research into implementation when the problem is still materially uncertain.

## Validation Style
Validation is usually based on:
- Source quality
- Completeness of the option set
- Internal consistency
- Clarity of recommendation
- Human review of findings

## Reroute Triggers
Reroute to a different mode when:
- A clear direction has emerged.
- The intended behavior can now be bounded.
- The main remaining work is to define the contract.
- The work is now implementable.

## Common Next Modes
- [Contract Builder](./contract-builder.md)
- [Quality Evaluator](./quality-evaluator.md)
- [Routine Implementer](./routine-implementer.md) (in rare cases where the solution becomes straightforward)
