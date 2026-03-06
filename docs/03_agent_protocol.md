# Coding Agent Protocol

## Purpose
Standardize how coding agents execute feature work from design docs to reduce drift and scope creep.

## Agent Inputs (Per Iteration)
- `docs/mvp-1.md` (or applicable phase doc)
- `docs/context-management/feature-playbooks/00_playbook.md`
- feature-local entrypoint `README.md`
- normative contract `01_contract.md`
- design file if present `02_design.md`
- any separate test or rollout artifact required by the feature's chosen track

## Agent Execution Rules
- Implement only the current scoped step for the feature.
- Keep changes small and focused.
- Add/update tests for changed behavior.
- If behavior changes, update the authoritative contract first.
- If design decisions change, update the design file and the feature entrypoint in the same iteration.
- Record current status, evidence, blockers, and next step back into the feature entrypoint before ending the iteration.
- Do not bypass the authoritative contract.

## Agent Outputs (Per Iteration)
- code/docs limited to PR scope
- tests and results summary
- updated feature status in the entrypoint
- execution-log or validation update with evidence
- explicit assumptions and blockers recorded when needed

## Review Rubric
- Contract compliance: does implementation match the authoritative contract?
- Behavior coverage: do tests prove acceptance criteria?
- Determinism: is stable output behavior preserved?
- Diff discipline: is scope bounded to planned slice?
- Resume quality: can another agent continue from the feature entrypoint alone?

## Escalation Conditions
Escalate to humans when:
- contract ambiguity blocks implementation
- invariants conflict across docs
- deterministic behavior cannot be guaranteed with existing interfaces
- no safe next step can be identified from the current feature state
