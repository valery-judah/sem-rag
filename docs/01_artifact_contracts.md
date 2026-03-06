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

## `README.md` Contract
Must include:
- feature summary
- current status and chosen track
- authoritative file list and read order
- boundary/context summary
- current step and next step
- blockers/open questions
- execution log
- latest validation summary

Must not own normative behavior or invariants.

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
