---
id: T-2026-03-07-001
title: Define explicit parser contract for canonical output and degraded behavior
created_at: 2026-03-07
updated_at: 2026-03-07
owner: agent
layer_a:
  intent: research
  problem_uncertainty: design_heavy
  dependency_complexity: cross_module
  knowledge_locality: scattered_internal
  specification_maturity: draft_contract
  validation_burden: partial_signals_only
  blast_radius: subsystem
  execution_horizon: multi_step
layer_b:
  current_mode: contract_builder
  reason: The dominant work is turning the parser's partly specified behavior into an explicit contract that downstream implementation and tests can rely on.
  reroute_triggers:
    - If the remaining uncertainty is mainly about current parser failures rather than contract shape, reroute to debug_investigator.
    - If the parser contract becomes explicit enough to encode directly in models and tests, reroute to routine_implementer.
    - If materially different contract directions remain live and need comparison before drafting, reroute to research_scout.
layer_c:
  feature_cell_ref: null
  control_profiles: []
layer_d:
  state: active
  phase: contract definition
  next_step: Draft the parser contract delta covering anchor completeness, metadata schema, supported content-type behavior, and degraded-output rules.
  entered_at: 2026-03-07
  updated_at: 2026-03-07
layer_d_companion:
  blocking_reason: null
  unblock_condition: null
  checkpoint_reason: null
  approval_ref: null
  evidence_refs:
    - docs/features/parsers/01_rfc.md
    - src/docforge/parsers/models.py
    - src/docforge/parsers/default.py
    - tests/parsers/test_models.py
    - tests/parsers/test_default_parser.py
  decision_ref: null
  lifecycle_scope: task
---

# Summary

## Request / problem

The parser subsystem needs a more explicit and enforceable contract. The current RFC is more specific than the runtime enforcement, especially around anchor completeness, metadata shape, supported content-type behavior, and degraded-output semantics.

## Current slice boundary

This task covers defining the parser contract delta for the canonical parser surface and identifying the minimum runtime and test implications needed to make that contract executable.

## Out of scope for this slice

- broad parser implementation rewrites
- full hybrid PDF pipeline redesign
- downstream chunking contract changes beyond parser-facing implications
- end-to-end retrieval or evaluation work

# Inputs / References

- `docs/features/parsers/01_rfc.md`
- `docs/features/parsers/03_design.md`
- `docs/features/hybrid-parsers/01_rfc.md`
- `src/docforge/parsers/models.py`
- `src/docforge/parsers/default.py`
- `tests/parsers/test_models.py`
- `tests/parsers/test_default_parser.py`
- `docs/mvp-1.md`
- `ARCHITECTURE.md`

# Notes

## Classification notes

The problem is no longer pure exploration. The repo already has an authoritative parser RFC and concrete runtime models, but they are not aligned tightly enough to function as a fully specified contract. The main work is to narrow ambiguity into explicit rules another implementation slice can enforce.

## Layer C rationale

No workstream or non-baseline control profile is needed yet. This is a bounded contract-definition slice. If the RFC delta reaches a real review boundary before code changes, a reviewed-style control profile can be added then.

## Current control condition

The task is active and executable. The immediate next step is to draft the contract delta from the current mismatch between parser docs, runtime models, and parser tests.

# Work Log

## 2026-03-07

- Identified the parser RFC as the authoritative contract surface for tightening parser behavior.
- Confirmed the main mismatch: the RFC describes fuller anchor and output obligations than the default parser currently enforces for normal textual documents.
- Chose a bounded contract-definition slice rather than direct implementation or workstream promotion.
- Set the next step to draft the contract delta before changing runtime models or parser code.

# Open Questions / Risks

- Should empty section and block anchors remain an explicitly allowed transitional state for textual documents, or should the contract now require full anchor emission?
- How much parser metadata should be typed and required versus left extensible?
- Should degraded output be represented as a successful `ParsedDocument` with explicit metadata, or should some cases remain hard parser failures?
- Risk: the contract draft could sprawl into future parser architecture instead of staying focused on the minimum executable boundary.

# Closure

## Acceptance basis

This slice is complete when the parser contract delta is explicit enough that a follow-on implementation task could update models, parser behavior, and tests without inventing missing rules.

## Closure notes

Not yet complete.
