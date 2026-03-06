# Agentic Feature Playbook

## Purpose
Provide one reusable workflow to design, implement, resume, and validate future pipeline features with the minimum documentation surface that still keeps agent execution safe.

## Non-negotiables
- Stable identity for produced artifacts when inputs/config are unchanged.
- Determinism for identical inputs, code version, and config.
- Traceable provenance from derived artifacts back to source representation when applicable.
- Hierarchical integrity where parent/child structures exist.
- Explicit boundaries, ownership, and non-goals.

## Track Model
Start with the smallest track that is still safe.

### Tiny
Use for:
- narrow bug fixes
- low-risk local behavior changes
- follow-up slices on an already-designed feature

Required artifacts:
- `README.md`
- `01_contract.md`

### Standard
Use for:
- normal new features
- changes that cross more than one module or concern
- work that needs explicit implementation strategy beyond the contract

Required artifacts:
- `README.md`
- `01_contract.md`
- `02_design.md`

### High-risk
Use for:
- migrations
- irreversible data effects
- rollout-sensitive changes
- features with broad regression surface or explicit quality gates

Required artifacts:
- Standard track artifacts
- `03_test_plan.md`
- `04_rollout.md`

## Escalation Rules
Escalate from `Tiny` to `Standard` if:
- more than one subsystem is touched
- the change introduces or modifies invariants
- implementation needs non-obvious design decisions or tie-breakers
- acceptance cannot be captured cleanly inside the contract alone

Escalate from `Standard` to `High-risk` if:
- rollout needs stages or rollback criteria
- explicit thresholds, offline eval, or extra reporting are required
- failure could materially harm correctness, reliability, or recoverability
- the change requires migration, dual-path comparison, or backfill

Downgrading is allowed if the feature proves smaller than expected, but the surviving artifacts must absorb the removed artifact's required sections.

## Artifact Responsibilities
- `README.md`: feature entrypoint, current status, read order, boundary/context summary, current next step, blockers, execution log, and latest validation.
- `01_contract.md`: normative feature behavior, scope, non-goals, interfaces, invariants, acceptance checks, edge scenarios, and change control.
- `02_design.md`: implementation strategy, decomposition, frozen decisions, tie-breakers, update triggers, observability, and deferred items.
- `03_test_plan.md`: deeper test matrix, corpora/fixtures, snapshot policy, CI gates, and reporting.
- `04_rollout.md`: rollout stages, success metrics, observability checks, abort triggers, and ownership/comms.

## Workflow
1. Create `docs/features/<feature-name>/`.
2. Choose the smallest safe track.
3. Start with `README.md` and `01_contract.md`.
4. Add `02_design.md` only when implementation complexity requires it.
5. Add `03_test_plan.md` and `04_rollout.md` only when risk requires them.
6. Keep `README.md` current so another agent can resume from it alone.

## Authority Rules
- `01_contract.md` wins for behavior, invariants, and acceptance semantics.
- `02_design.md` wins for implementation strategy and tie-breakers.
- `README.md` wins for current status, next step, blockers, and execution history.
- If `README.md` conflicts with `01_contract.md` on behavior, the contract wins until deliberately amended.

## Directory Convention
- Shared rules live under `docs/`.
- Templates live under `docs/context-management/feature-playbooks/templates/`.
- New feature docs live under `docs/features/<feature-name>/`.

## Definition of Done (Documentation)
- The feature uses a track that matches its actual risk and complexity.
- `README.md` makes status, next step, blockers, and latest validation obvious.
- `01_contract.md` is authoritative and current.
- `02_design.md` exists when implementation complexity requires it.
- Test and rollout artifacts exist only when justified by risk and are current when present.
- Another agent can resume work from the feature entrypoint without reconstructing state from multiple docs.
