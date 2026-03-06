# Merged Feature Workflow Playbook v3

**Purpose:** A reusable, agent-friendly workflow for feature design, implementation, validation, and rollout with less documentation overhead by default.

This version optimizes for:
- risk-proportional documentation
- high-legibility execution
- resumable handoff
- explicit contract authority
- stronger sections instead of more files

The goal is not "more documents." The goal is to keep the minimum structure that still makes agent work safe.

---

# 0) Operating principles

## 0.1 What this playbook optimizes for
This playbook is designed to make feature work:
- understandable from the repository alone
- resumable by another agent or human
- proportional to feature risk and complexity
- deterministic in implementation and validation
- mechanically checkable where possible

## 0.2 Core non-negotiables
These are the default invariants for feature work, especially for backend, pipeline, retrieval, and data-heavy features:

- **Stable identity**: produced artifacts should be stable when inputs, code, and config are unchanged.
- **Determinism**: identical inputs and config must produce reproducible outputs.
- **Traceable provenance**: derived artifacts must map back to source representation when applicable.
- **Hierarchical integrity**: parent/child structures must remain valid and ordered when they exist.
- **Explicit boundaries**: touched interfaces, dependencies, and non-goals must be documented.
- **Small, stable entrypoints**: an agent should be able to start from one compact feature entrypoint.
- **Mechanical enforcement where possible**: important rules should eventually live in tests, CI, structural checks, or lint.

## 0.3 What this playbook is not
This playbook is not:
- a substitute for `AGENTS.md`
- a substitute for architecture docs
- a paperwork ritual for every tiny change
- an excuse to spread one idea across many shallow files

---

# 1) Tracks: start small, escalate only when needed

Do not use a fixed artifact bundle for every feature. Use the smallest track that is still safe.

## 1.1 Track shapes

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
- broad regression-surface work
- features with offline eval, quality gates, or staged deployment

Required artifacts:
- Standard track artifacts
- `03_test_plan.md`
- `04_rollout.md`

## 1.2 Escalation rules
Escalate from **Tiny** to **Standard** if:
- more than one subsystem is touched
- the change introduces or modifies invariants
- implementation needs non-obvious design decisions or tie-breakers
- acceptance cannot be captured cleanly inside the contract alone

Escalate from **Standard** to **High-risk** if:
- rollout needs staged release or rollback criteria
- the feature needs explicit quality thresholds or offline evaluation
- failure could materially harm correctness, reliability, trust, or recoverability
- the change requires migration, dual-path comparison, or backfill

## 1.3 Downgrading is allowed
If a feature later proves smaller than expected, remove unnecessary artifacts. The remaining artifacts must absorb the required sections of any removed file.

---

# 2) Directory and naming conventions

## 2.1 Feature folder
Each feature lives under:

```text
docs/features/<feature-name>/
```

## 2.2 Required files by track

### Tiny
```text
docs/features/<feature-name>/
├── README.md
└── 01_contract.md
```

### Standard
```text
docs/features/<feature-name>/
├── README.md
├── 01_contract.md
└── 02_design.md
```

### High-risk
```text
docs/features/<feature-name>/
├── README.md
├── 01_contract.md
├── 02_design.md
├── 03_test_plan.md
└── 04_rollout.md
```

## 2.3 Naming rules
Prefer functional names over overloaded names:
- `contract` instead of `rfc` when the file owns feature behavior
- `design` instead of a generic plan/design split when one implementation doc is enough
- `test_plan` and `rollout` only when the feature genuinely needs them

If a repo keeps legacy names such as `01_rfc.md`, `02_user_stories.md`, or `04_workplan.md`, the file header must make the slimmer semantics explicit.

---

# 3) Artifact ownership

The safety model depends on clearer authority, not more files.

## 3.1 `README.md`
`README.md` is mandatory for every track and is always the first file an agent should read.

It owns:
- feature summary
- current status
- track
- authoritative file list
- read order
- dependency/context summary
- current next step
- blockers and open questions
- live execution log
- latest validation summary

It does **not** own behavioral requirements or invariants.

## 3.2 `01_contract.md`
`01_contract.md` is the normative source of truth for:
- problem and scope
- explicit non-goals
- touched interfaces, inputs, and outputs
- required behavior
- invariants
- required fields and meanings
- success criteria
- acceptance checks
- failure and edge scenarios
- change-control rules

This file stays separate from status and execution tracking.

## 3.3 `02_design.md`
Required for Standard and High-risk tracks.

It owns:
- implementation strategy
- decomposition
- frozen design decisions
- tie-breakers
- change triggers
- observability
- limitations and deferred items

## 3.4 `03_test_plan.md`
Only for High-risk features, or when Standard work genuinely needs it.

It owns:
- deeper test layers
- fixture/corpus policy
- snapshot policy
- CI gate matrix
- reporting expectations

## 3.5 `04_rollout.md`
Only for High-risk features.

It owns:
- rollout stages
- entry criteria
- success metrics
- observability checks
- abort/rollback triggers
- ownership and comms

---

# 4) Required sections inside the slimmer artifact set

Reducing artifact count only works if the remaining files are stronger.

## 4.1 Required `README.md` structure

```md
# <Feature name>

## Summary
<1-2 paragraphs>

## Status
- State: draft | active | blocked | validating | rollout | complete | obsolete
- Track: tiny | standard | high-risk
- Owner:
- Last updated:

## Authoritative files
- Contract: `01_contract.md`
- Design: `02_design.md`         # omit if Tiny
- Test plan: `03_test_plan.md`   # omit if absent
- Rollout: `04_rollout.md`       # omit if absent

## Read order
1. `README.md`
2. `01_contract.md`
3. `02_design.md`                # omit if Tiny

## Boundary / context summary
- Touched modules:
- Upstream dependencies:
- Downstream consumers:
- Constraints / non-goals:

## Current plan
- Current step:
- Next step:
- Commands/checks:

## Execution log
- YYYY-MM-DD:

## Blockers and open questions
- ...

## Latest validation
- Last run:
- Checks:
- Result:
```

## 4.2 Required `01_contract.md` structure

```md
# Contract: <Feature>

## Problem and scope
- ...

## Out of scope
- ...

## Inputs / outputs or touched interfaces
- ...

## Required behavior and invariants
- REQ-001: ...

## Acceptance checks
- AC-001: ...

## Failure and edge scenarios
- ...

## Success criteria
- ...

## Change control
- ...
```

## 4.3 Required `02_design.md` structure

```md
# Design: <Feature>

## Design goals
- ...

## Data flow
1. ...

## Key decisions and tie-breakers
- DES-001: ...

## Change triggers
- Update contract when:
- Update README when:

## Observability
- ...

## Limitations / deferred items
- ...
```

---

# 5) Precedence and amendment rules

## 5.1 Precedence
If documents conflict, resolve them in this order:

1. `01_contract.md`
2. `02_design.md`
3. `README.md`

This means:
- `01_contract.md` wins for behavior, invariants, and acceptance semantics
- `02_design.md` wins for implementation strategy and tie-breakers
- `README.md` wins for current status, next step, blockers, and execution history

If `README.md` conflicts with `01_contract.md` on behavior, the contract wins until deliberately amended.

## 5.2 Controlled amendment
Contract freeze does not mean "never change." It means "change intentionally."

Use this rule set:
- contract-affecting change -> update `01_contract.md` first
- implementation-strategy change -> update `02_design.md`
- sequencing, status, or blocker change -> update `README.md`
- test-strategy change -> update `03_test_plan.md`
- rollout-policy change -> update `04_rollout.md`

Whenever a meaningful post-freeze change is made, add a short dated decision note in the relevant authoritative file.

---

# 6) Feature lifecycle

## 6.1 Create the feature
1. Create `docs/features/<feature-name>/`
2. Choose the smallest safe track
3. Create `README.md`
4. Create the required files for that track

Do not create optional artifacts "just in case."

## 6.2 Freeze the contract before coding
Before implementation begins, a reviewer should be able to answer:
- what the feature changes
- what it must not change
- what invariants must remain true
- what evidence counts as completion

## 6.3 Design only when the track needs it
Tiny features should not pay for a separate design file if the contract is already sufficient.

Standard and High-risk work should use `02_design.md` when:
- implementation needs decomposition
- tie-breakers matter
- multiple modules must coordinate
- the work needs explicit update triggers

## 6.4 Validate and roll out proportionally
Validation is complete only when the required checks for the chosen track pass. Rollout artifacts exist only when rollout risk requires them.

---

# 7) Agent execution protocol

## 7.1 Inputs per iteration
Every iteration should provide the agent:
- feature `README.md`
- authoritative contract file
- design file if present
- relevant system-level docs as needed
- the current scoped task

## 7.2 Required outputs per iteration
The agent should produce:
- scoped code changes
- tests or validation updates
- status updates in `README.md`
- authoritative doc changes when behavior or design changed

## 7.3 End-of-iteration update protocol
At the end of each iteration:
- update `README.md` status
- update the current/next step
- record validation results
- note blockers and open questions
- record any meaningful design or contract amendment

The next agent should be able to resume from `README.md` alone.

---

# 8) Testing and rollout governance

## 8.1 Default testing model
For non-trivial features, prefer:
- unit tests for components or subroutines
- integration tests for composed behavior
- invariant/property tests for critical rules
- snapshots or golden fixtures when output shape matters

## 8.2 When to use `03_test_plan.md`
Add a separate test plan only when the feature needs:
- a non-trivial test matrix
- special corpora or fixtures
- explicit CI thresholds
- reporting artifacts or quality dashboards

## 8.3 When to use `04_rollout.md`
Add a separate rollout file only when the feature needs:
- shadow mode
- offline evaluation
- staged release
- rollback triggers
- dual-path comparison or backfill policy

---

# 9) Definition of Done

A feature is done only when all required artifacts for its chosen track are current and internally consistent.

## 9.1 Core completion
- [ ] Track choice is still appropriate
- [ ] Contract is explicit and current
- [ ] Status and next step are visible in `README.md`
- [ ] Validation evidence is current

## 9.2 Standard / High-risk completion
- [ ] Design decisions and tie-breakers are recorded when needed
- [ ] Changed behavior matches the contract

## 9.3 High-risk completion
- [ ] Test plan exists and matches current validation strategy
- [ ] Rollout and rollback policy are documented

---

# 10) Minimal templates

## 10.1 Tiny track

```text
docs/features/<feature-name>/
├── README.md
└── 01_contract.md
```

## 10.2 Standard track

```text
docs/features/<feature-name>/
├── README.md
├── 01_contract.md
└── 02_design.md
```

## 10.3 High-risk track

```text
docs/features/<feature-name>/
├── README.md
├── 01_contract.md
├── 02_design.md
├── 03_test_plan.md
└── 04_rollout.md
```

---

# 11) Summary

This playbook uses a simpler operating model:

- Start with the smallest track that is still safe.
- Keep one compact entrypoint in `README.md`.
- Keep the contract separate from live status.
- Add design only when implementation complexity requires it.
- Add test and rollout artifacts only when risk requires them.
- Use clearer authority rules instead of more files.
- Preserve resumability through stronger sections, not heavier process.

This is the balance point between under-specified execution and documentation overload.
