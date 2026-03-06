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

## Entrypoint Bootstrap Procedure
Before any implementation work begins:
1. Open `README.md`.
2. Parse the required sections and required field labels.
3. Fail fast if `State`, `Track`, `Authoritative Files`, or `Current step` is missing.
4. Load files in `Read Order`.
5. Confirm that the listed authoritative files exist.
6. Use `Track` to determine whether `02_design.md`, `03_test_plan.md`, or `04_rollout.md` are required.
7. Refuse execution if the entrypoint and required artifacts disagree on existence or authority.

## Agent Execution Rules
- Implement only the current scoped step for the feature.
- Keep changes small and focused.
- Add/update tests for changed behavior.
- If behavior changes, update the authoritative contract first.
- If design decisions change, update the design file and the feature entrypoint in the same iteration.
- Record current status, evidence, blockers, and next step back into the feature entrypoint before ending the iteration.
- Do not bypass the authoritative contract.

## Entrypoint Update Procedure
At iteration start:
- set `Owner`
- set `Last updated`
- confirm or update `State`
- confirm `Current step`

During iteration:
- keep behavioral requirements out of `README.md`
- update only status, progress, blockers, validation, and latest-decision summary in the entrypoint
- update the contract or design file first when those layers change

At iteration end:
- update `Current step`
- update `Next step`
- append one `Execution Log` entry
- update `Latest Validation`
- update `Latest Decision` if a real contract/design decision was made
- update `Blocked on` or clear it
- set `Last updated`

Use append-only log entries and overwrite-in-place for current status fields.

## Block, Handoff, and Completion Procedures
When blocked:
- set `State: blocked`
- write `Blocked on`
- move unresolved questions into `Open questions`
- set `Next step` to the unblock action
- append an `Execution Log` entry describing partial progress and the blocker

When handing off:
- require `Next step`
- require `Latest Validation`
- require a fresh `Execution Log` entry for the last iteration
- require `Latest Decision` to be updated if contract/design intent changed

When completing:
- set `State: complete`
- clear `Blocked on`
- set `Next step: None`
- append a final validation/result summary

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
- Entrypoint validity: does `README.md` remain parseable and procedurally complete?

## Escalation Conditions
Escalate to humans when:
- contract ambiguity blocks implementation
- invariants conflict across docs
- deterministic behavior cannot be guaranteed with existing interfaces
- no safe next step can be identified from the current feature state
