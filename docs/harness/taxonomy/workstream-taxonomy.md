# Workstream Taxonomy

## Purpose
This file defines the naming, classification, and lifecycle vocabulary for workstream folders in this repo.

## When To Use
- Naming a new workstream
- Choosing the primary work type for a new workstream
- Checking lifecycle labels before updating a workstream doc
- Deciding whether a piece of work belongs in a workstream or an ADR

## Workstream Types
- `feature`: net-new capability or material behavior expansion
- `defect`: bug fix, regression investigation, or correctness repair
- `refactor`: internal design change with no intended product behavior change
- `spike`: investigation, feasibility work, or decision-support exploration
- `operations-infrastructure`: runtime, deployment, observability, release, or service-operability foundation work

## Decision Rule
Classify work by its primary deliverable:

- New capability or intended behavior change: `feature`
- Restore incorrect behavior: `defect`
- Internal redesign with stable intended behavior: `refactor`
- Learn, compare options, or de-risk before commitment: `spike`
- Improve runtime, deployment, observability, or service-operability foundations: `operations-infrastructure`

## Suggested Statuses
- `backlog`: defined but not yet active
- `active`: in progress
- `blocked`: waiting on an external dependency or decision
- `done`: implementation and expected evidence complete
- `archived`: retained for history but no longer active or current

## Naming Guidance
Use `WS-<id>-<slug>` for the directory name.

Examples:
- `WS-001-parser-contracts`
- `WS-014-pdf-pipeline-hardening`

Guidelines:
- Keep `<id>` short and stable.
- Keep `<slug>` lowercase and hyphenated.
- Prefer one workstream per coherent outcome, not per commit or per meeting.
- Keep `work_type` and `status` in `workstream.md` metadata, not in the directory path.
