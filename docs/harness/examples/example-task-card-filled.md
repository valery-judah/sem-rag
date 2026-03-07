
# Example Filled Task Card

This example shows what a filled task card can look like for one bounded active slice.

It is intentionally concrete and moderately detailed. The goal is to show:
- how a single task stays scoped to one current slice,
- how canonical Layer A-D frontmatter appears together in one operational artifact,
- how the current mode, current state, and current next step remain explicit,
- how the work log supports resumability without replacing the control fields.

```md
---
id: T-2026-03-06-001
title: Investigate parser regression in block normalization
created_at: 2026-03-06
updated_at: 2026-03-06
owner: agent
layer_a:
  intent: debug
  problem_uncertainty: medium
  dependency_complexity: medium
  knowledge_locality: mostly_local
  specification_maturity: high
  validation_burden: medium
  blast_radius: medium
  execution_horizon: short
layer_b:
  current_mode: debug_investigator
  reason: The dominant work is reproduction, isolation, and root-cause identification for the regression.
  reroute_triggers:
    - If the first failing transformation is isolated and the corrective change is obvious, reroute to routine_implementer.
    - If the regression is caused by undefined expected block-shape behavior, reroute to contract_builder.
layer_c:
  feature_cell_ref: null
  control_profiles: []
layer_d:
  state: active
  phase: reproduction
  next_step: Isolate the first normalization stage where nested list structure is lost.
  entered_at: 2026-03-06
  updated_at: 2026-03-06
layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs:
    - failing fixture output comparison to expected nested-list structure
  decision_ref: null
  lifecycle_scope: task
---

# Summary

## Request / problem

Parser output is breaking nested list blocks after a recent refactor. The immediate task is to investigate the regression and identify where the structure is first lost.

## Current slice boundary

This task covers reproduction and causal isolation of the regression in block normalization. It does not yet include the final fix implementation unless the cause becomes obvious and bounded.

## Out of scope for this slice

- broad parser redesign
- unrelated normalization cleanup
- full migration of parser architecture
- downstream retrieval-quality evaluation

# Inputs / References

- `src/parsing/normalization.py`
- `tests/parsing/test_block_normalization.py`
- reproduced failing input fixture: `tests/fixtures/nested_list_regression.md`
- recent refactor PR touching normalization path

# Notes

## Classification notes

The expected behavior is mostly known because the task is framed as a regression, but the cause is not yet established. The likely code path is local to normalization, though shared parser behavior raises moderate blast-radius concern.

## Layer C rationale

No non-baseline control profile is active. The slice can proceed under baseline control, and there is no current need for workstream coordination, mandatory review pause, or stronger approval or evidence obligations.

## Current control condition

The task is active and ready for continued investigation. No blocker, review pause, or approval gate is currently present.

# Work Log

## 2026-03-06

- Reproduced the regression using the nested-list fixture.
- Confirmed that the parser no longer preserves expected nesting shape after normalization.
- Narrowed the likely failure surface to the normalization path rather than upstream raw parsing.
- Left the next step as causal isolation of the first failing transformation stage.

# Open Questions / Risks

- Is the regression caused by one recent transformation change or by an interaction across multiple normalization passes?
- Is the expected nested-list representation fully stable, or does the refactor expose an older undocumented ambiguity?
- Risk: accidental scope expansion into broader parser cleanup before the regression cause is isolated.

# Closure

## Acceptance basis

This slice will be considered complete when the regression has been causally isolated and either:
- the task can be cleanly rerouted into a bounded implementation fix, or
- the investigation shows that expected behavior must be clarified in a separate contract-definition slice.

## Closure notes

Not yet complete.
```

## Why this example is shaped this way

A few things are deliberate here:

- The frontmatter is the authoritative control surface, so Layer A-D fields are not repeated as body checklists.
- The title describes the current slice, not the whole parser problem space.
- Layer B is one mode only: `debug_investigator`.
- Layer C is empty because no special control profile or workstream wrapper is needed yet.
- Layer D makes the task executable by exposing `state`, `phase`, and one concrete `next_step`.
- The work log records progress, but the control fields at the top still carry the operational truth.

## What to notice

This example is a good reference when:
- the task is active and bounded,
- the expected behavior is mostly known but the cause is not,
- the task does not yet justify a workstream,
- the next agent should be able to resume directly from the card.

## Possible evolution from this example

A task like this might later evolve in one of several ways:

- reroute to `routine_implementer` if the causal fix becomes clear,
- reroute to `contract_builder` if expected block behavior turns out to be underspecified,
- move to `checkpoint` if investigation findings need review before a risky fix,
- remain local and complete without any Layer C changes,
- or become a child task in a larger workstream if the issue reveals broader parser migration work.
