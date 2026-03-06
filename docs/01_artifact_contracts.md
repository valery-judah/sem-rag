# Artifact Contracts

## Contract Authority
For new features using the slim playbook, `01_contract.md` is the single normative source of truth for:
- behavior and scope
- touched interfaces
- required fields
- invariants
- acceptance semantics
- change-control rules

Other artifacts may summarize this information, but must not silently redefine it.

## Authority By Concern
Use concern ownership, not just filename precedence.

| Concern | Authoritative artifact | Supporting artifacts | Non-authority rule |
|---|---|---|---|
| Feature status and execution state | `README.md` | `02_design.md`, `03_test_plan.md`, `04_rollout.md` | Supporting docs may reference status, but must not become the source of current execution truth. |
| Behavior, scope, invariants, and acceptance semantics | `01_contract.md` | `README.md`, `02_design.md`, `03_test_plan.md` | `README.md` may summarize behavior, but cannot redefine it. |
| Implementation strategy, decomposition, and tie-breakers | `02_design.md` | `README.md`, `01_contract.md` | `02_design.md` may explain behavior, but cannot override the contract. |
| Deep test strategy and CI thresholds | `03_test_plan.md` | `README.md`, `02_design.md` | Optional validation docs may refine testing, but cannot change contract semantics. |
| Rollout stages, evidence, and abort rules | `04_rollout.md` | `README.md`, `03_test_plan.md` | Rollout summaries may restate status, but rollout policy lives here. |

## Conflict Resolution
When docs disagree:
1. Identify the conflicting concern, not just the files.
2. Resolve authority using the concern matrix.
3. Treat the authoritative artifact as correct until deliberately amended.
4. Update downstream summary/supporting docs in the same iteration if they drift.
5. Record a dated decision note when the authoritative meaning actually changes.

## Drift Classes
- `summary drift`: summary surfaces lag behind an authoritative file.
- `design drift`: `02_design.md` no longer matches the contract or chosen implementation approach.
- `execution drift`: `README.md` no longer matches actual repo execution state.
- `contract drift`: code or design no longer matches `01_contract.md`.

Required response:
- `summary drift` -> update the summary surface only.
- `design drift` -> update `02_design.md`, or escalate if behavior is changing.
- `execution drift` -> update `README.md`.
- `contract drift` -> stop implementation and amend `01_contract.md` first, or escalate.

## `README.md` Contract
Must include:
- feature summary
- current status and chosen track
- authoritative file list and read order
- boundary/context summary
- current step and next step
- latest decision summary
- blockers/open questions with an explicit `Blocked on` field
- execution log
- latest validation summary
- fixed section names and fixed field labels for machine parsing

Must not own normative behavior or invariants.

`README.md` is the orchestration entrypoint. It is authoritative for:
- current status
- current step and next step
- blockers and open questions
- execution history
- latest validation
- latest decision summary

It must use these required sections:
- `Summary`
- `Status`
- `Authoritative Files`
- `Read Order`
- `Boundary / Context Summary`
- `Current Plan`
- `Latest Decision`
- `Execution Log`
- `Blockers and Open Questions`
- `Latest Validation`

It must use these required field labels:
- `State`
- `Track`
- `Owner`
- `Last updated`
- `Current step`
- `Next step`
- `Commands/checks`
- `Decision ID`
- `Date`
- `Summary`
- `Affected files`
- `Blocked on`
- `Open questions`
- `Last run`
- `Checks`
- `Result`

Allowed `State` values:
- `draft`
- `active`
- `blocked`
- `validating`
- `rollout`
- `complete`
- `obsolete`

Allowed state transitions:
- `draft -> active`
- `active -> blocked | validating | complete`
- `blocked -> active | obsolete`
- `validating -> active | rollout | complete | blocked`
- `rollout -> complete | blocked`
- `complete -> active` only when intentionally reopened
- `obsolete` is terminal

## `01_contract.md` Contract
Must include:
- problem and scope
- explicit out-of-scope or non-goals
- inputs/outputs or touched interfaces
- required behavior and invariants
- acceptance checks
- failure and edge scenarios
- success criteria
- change-control policy

## `02_design.md` Contract
Must include:
- design goals linked to the contract
- data flow or decomposition
- key decisions and tie-breakers
- change triggers for contract/readme updates
- observability
- limitations and deferred items

Must not redefine normative behavior already owned by the contract.

## Amendment Triggers By Concern
- behavior/invariant/interface/acceptance change -> amend `01_contract.md` first
- implementation-only change with same behavior -> amend `02_design.md`
- sequencing/status/blocker/validation change -> amend `README.md`
- test-governance change -> amend `03_test_plan.md`
- rollout-policy change -> amend `04_rollout.md`

Require a short dated decision note whenever:
- authority changes meaning
- a conflict is resolved by amendment
- an intentional override or reopen occurs

## Future Enforcement Hook
Future doc-lint or validation could check:
- required authority sections exist
- forbidden restatement of contract semantics in `README.md`
- missing decision note after authoritative amendments
- disagreement between track-required artifacts and entrypoint claims

This is a future enforcement direction, not a current required check.

## Optional Contracts
### `03_test_plan.md`
- test matrix
- fixture/corpus and snapshot policy
- CI gates and thresholds
- reporting expectations

### `04_rollout.md`
- rollout stage gates
- evidence and success metrics per stage
- abort/rollback triggers
- ownership and communication plan
