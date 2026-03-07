# Harness Operator Map

Use this file when you need the shortest answer to:

- what should I open next,
- which workflow applies to the current state,
- which file explains the current mode,
- or where to go when the task card is already known.

This is a jump table, not a replacement for the workflows, routing rules, or layer docs.

## Fast path

1. No task selected yet:
   open `indexes/active-tasks.md`, choose one executable task, then open the authoritative card in `active/tasks/`.
2. Task card already selected:
   use the tables below to jump from `layer_b.current_mode` and `layer_d.state` to the next doc.
3. Before you stop, pause, reroute, or report:
   refresh the authoritative artifact first. Use `AGENTS.md` and `workflows/task-execution-loop.md` for the write-back boundary.

## If you already have the task card

| Need | Open |
|---|---|
| Meaning of the current mode | `concepts/layer-b-modes/<mode>.md` |
| Correct workflow for the current state | state-to-workflow table below |
| Validate or repair mode fit | `policies/routing-rules.md` |
| Detailed meaning of the current state | `concepts/layer-d/states.md` |
| Pause, handoff, or resume handling | `workflows/handoff-resume-loop.md` |
| Review or approval boundary handling | `workflows/checkpoint-review-loop.md` |

## State-to-workflow lookup

| State | Default action | Primary doc |
|---|---|---|
| `draft` | finish shaping the slice into an actionable task | `workflows/intake-loop.md` |
| `active` | execute the current slice | `workflows/task-execution-loop.md` |
| `validating` | run the validation or evidence cycle | `workflows/task-execution-loop.md` |
| `blocked` | preserve blocker truth and do not execute through it | `workflows/handoff-resume-loop.md` |
| `checkpoint` | stop normal execution at the review boundary | `workflows/checkpoint-review-loop.md` |
| `awaiting_approval` | stop normal execution and preserve the approval dependency | `workflows/checkpoint-review-loop.md` |
| `complete` | treat as terminal; do not reopen casually | authoritative task or workstream card |
| `cancelled` | treat as terminal; do not reopen casually | authoritative task or workstream card |

If the current authoritative item is a workstream card rather than a task card, use `workflows/workstream-loop.md` for active workstream-scope coordination and use the same state table to decide when normal coordination must pause.

## Mode-to-file lookup

| `layer_b.current_mode` | Open |
|---|---|
| `research_scout` | `concepts/layer-b-modes/research-scout.md` |
| `contract_builder` | `concepts/layer-b-modes/contract-builder.md` |
| `routine_implementer` | `concepts/layer-b-modes/routine-implementer.md` |
| `refactor_surgeon` | `concepts/layer-b-modes/refactor-surgeon.md` |
| `debug_investigator` | `concepts/layer-b-modes/debug-investigator.md` |
| `migration_operator` | `concepts/layer-b-modes/migration-operator.md` |
| `optimization_tuner` | `concepts/layer-b-modes/optimization-tuner.md` |
| `quality_evaluator` | `concepts/layer-b-modes/quality-evaluator.md` |

## Practical routing rule

- If `current_mode` is already known, open that mode file directly.
- If mode fit is unclear, use `policies/routing-rules.md`.
- If state does not permit normal execution, follow the state-to-workflow table before doing more work.
