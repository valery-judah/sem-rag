# Documentation Map

## Purpose
`docs/` is the repository documentation system for durable system truth, active execution records, architecture decisions, and reusable documentation tooling.

## Directory Map
- `evergreen/`: current durable system truth and operational references
- `workstreams/`: active and historical work execution, including local RFC/proposal material, design notes, and evidence
- `adrs/`: durable architecture decision records promoted out of individual workstreams
- `harness/`: templates, conventions, playbooks, and helper scripts for humans and agents

## Where New Work Goes
- Put durable system descriptions and stable operating guidance in `docs/evergreen/`.
- Put new implementation work, RFC/proposal material, decisions, evidence, and handoff notes in the relevant folder under `docs/workstreams/`.
- Promote cross-cutting, long-lived decisions from a workstream into `docs/adrs/` when they become durable.
- Do not create a top-level `docs/rfcs/`; RFC-like proposal material belongs inside workstreams.

## ADRs And Workstreams
Workstreams capture time-scoped execution and local decision-making. ADRs capture the smaller set of decisions that outlive a single workstream or affect multiple parts of the system.

## Notes On Older Areas
Older references to `docs/features/` or `docs/workflows/` should be treated as historical. Active work has been normalized into `docs/workstreams/`, and the primary structure is `docs/evergreen/`, `docs/workstreams/`, `docs/adrs/`, and `docs/harness/`.
