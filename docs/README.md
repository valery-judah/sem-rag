# Documentation Map

## Purpose
`docs/` is the repository documentation system for durable product truth, current repo documentation, optional execution records, architecture decisions, and reusable documentation tooling.

Authority note: `docs/evergreen/` holds the canonical product and repo truth. `docs/delivery/` may contain planning, architecture, or workflow drafts retained for reference, but it is not the canonical source of product scope. New durable docs belong in `docs/evergreen/`, and new time-scoped execution records belong in `docs/workstreams/`.

## Directory Map
- `evergreen/`: current durable system truth and operational references
- `delivery/`: non-canonical planning, architecture, and workflow drafts kept for reference
- `workstreams/`: optional time-scoped execution records, RFC/proposal material, design notes, and evidence
- `adrs/`: durable architecture decision records promoted out of individual workstreams when needed
- `harness/`: templates, conventions, playbooks, and helper scripts for humans and agents

## Where New Work Goes
- Put durable system descriptions and stable operating guidance in `docs/evergreen/`.
- Do not treat `docs/delivery/` as the source of truth for product scope or durable repo contracts.
- Put new implementation work, RFC/proposal material, decisions, evidence, and handoff notes in the relevant folder under `docs/workstreams/`.
- Promote cross-cutting, long-lived decisions from a workstream into `docs/adrs/` when they become durable.
- Do not create a top-level `docs/rfcs/`; RFC-like proposal material belongs inside workstreams.

## ADRs And Workstreams
Workstreams capture time-scoped execution and local decision-making when a change needs that structure. ADRs capture the smaller set of decisions that outlive a single workstream or affect multiple parts of the system.
