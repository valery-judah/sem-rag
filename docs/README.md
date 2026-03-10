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

## Evaluation Docs Map
Use this map when working on evaluation semantics, the eval harness, or related dataset design.

Canonical evergreen evaluation docs:
- `docs/evergreen/eval-vocabulary.md`: glossary, term normalization, and evaluation layer names
- `docs/evergreen/eval-support-semantics.md`: support-state criteria, citation expectations, and abstention rules
- `docs/evergreen/eval-scenario-taxonomy.md`: canonical scenario classes and classification rules
- `docs/evergreen/eval-failure-taxonomy.md`: canonical failure classes and classification rules

Related durable framing:
- `docs/evergreen/mvp.md`: product-scope and trust-contract authority
- `docs/evergreen/architecture.md`: current repo shape and implementation gap

Reference-only delivery docs:
- `docs/delivery/workflow.md`: non-canonical workflow and modeling guidance aligned to evergreen semantics
- `docs/delivery/eval-harness-rfc-sections-1-10.md`: eval-harness rationale, object model, scenario coverage, and scoring philosophy
- `docs/delivery/eval-harness-rfc-sections-11-15.md`: eval-harness operating model, dataset strategy, judging, phases, and release policy

Execution history:
- `docs/workstreams/WS-001-eval-harness/`: earlier eval-harness framing material
- `docs/workstreams/WS-002-semantic-lock/`: semantic-lock history and transition artifacts

Authority note:
- Treat the evergreen evaluation docs as the semantic source of truth.
- Use `docs/delivery/` for rationale, implementation guidance, and historical reference without treating it as canonical authority.
- Use workstreams for time-scoped decisions, evidence, and archival transition material.

## Where New Work Goes
- Put durable system descriptions and stable operating guidance in `docs/evergreen/`.
- Do not treat `docs/delivery/` as the source of truth for product scope or durable repo contracts.
- Put new implementation work, RFC/proposal material, decisions, evidence, and handoff notes in the relevant folder under `docs/workstreams/`.
- Promote cross-cutting, long-lived decisions from a workstream into `docs/adrs/` when they become durable.
- Do not create a top-level `docs/rfcs/`; RFC-like proposal material belongs inside workstreams.

## ADRs And Workstreams
Workstreams capture time-scoped execution and local decision-making when a change needs that structure. ADRs capture the smaller set of decisions that outlive a single workstream or affect multiple parts of the system.
