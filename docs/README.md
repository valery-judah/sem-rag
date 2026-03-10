# Documentation Map

## Purpose
`docs/` is the repository documentation system for durable product truth, current repo documentation, optional execution records, architecture decisions, and reusable documentation tooling.

Authority note: `docs/evergreen/` holds the canonical product and repo truth. `docs/delivery/` may contain planning, architecture, or workflow drafts retained for reference, but it is not the canonical source of product scope. New durable docs belong in `docs/evergreen/`, and new time-scoped execution records belong in `docs/workstreams/`.

## Quick Routes
If you need product scope:
- `docs/evergreen/mvp.md`: Canonical. Product north star and scope boundary.

If you need current implementation truth:
- `docs/evergreen/architecture.md`: Canonical. Current repo shape and implementation gap.

If you need stable interfaces:
- `docs/evergreen/api-contracts.md`: Canonical. Stable runtime interfaces that exist today.

If you need local commands and validation:
- `docs/evergreen/runbook.md`: Canonical. Local operation guidance and standard commands.

If you need evaluation semantics:
- `docs/evergreen/eval-vocabulary.md`: Canonical. Evaluation glossary, term normalization, and layer names.
- `docs/evergreen/eval-support-semantics.md`: Canonical. Support-state criteria, citation expectations, and abstention rules.
- `docs/evergreen/eval-scenario-taxonomy.md`: Canonical. Scenario classes and classification rules.
- `docs/evergreen/eval-failure-taxonomy.md`: Canonical. Failure classes and classification rules.

If you need evaluation implementation guidance:
- `docs/delivery/workflow.md`: Reference only. Workflow and modeling guidance aligned to evergreen semantics.
- `docs/delivery/eval-harness-rfc-sections-1-10.md`: Reference only. Eval-harness rationale, object model, scenario coverage, and scoring philosophy.
- `docs/delivery/eval-harness-rfc-sections-11-15.md`: Reference only. Eval-harness operating model, dataset strategy, judging, phases, and release policy.

If you need execution history:
- `docs/workstreams/WS-001-eval-harness/`: Execution history. Earlier eval-harness framing material.
- `docs/workstreams/WS-002-semantic-lock/`: Execution history. Semantic-lock history and transition artifacts.

## Directory Map
- `evergreen/`: current durable system truth and operational references
- `delivery/`: non-canonical planning, architecture, and workflow drafts kept for reference
- `workstreams/`: optional time-scoped execution records, RFC/proposal material, design notes, and evidence
- `adrs/`: durable architecture decision records promoted out of individual workstreams when needed
- `harness/`: templates, conventions, playbooks, and helper scripts for humans and agents

## Evaluation Docs Map
Use this map when working on evaluation semantics, the eval harness, or related dataset design.

If you need the evaluation glossary and layer names:
- `docs/evergreen/eval-vocabulary.md`: Canonical. Evaluation glossary, term normalization, and layer names.

If you need support-state, citation, or abstention rules:
- `docs/evergreen/eval-support-semantics.md`: Canonical. Support-state criteria, citation expectations, and abstention rules.

If you need scenario-class meanings:
- `docs/evergreen/eval-scenario-taxonomy.md`: Canonical. Scenario classes and classification rules.

If you need failure classification:
- `docs/evergreen/eval-failure-taxonomy.md`: Canonical. Failure classes and classification rules.

If you need product or implementation framing around evaluation:
- `docs/evergreen/mvp.md`: Canonical. Product north star and scope boundary.
- `docs/evergreen/architecture.md`: Canonical. Current repo shape and implementation gap.

If you need evaluation implementation guidance:
- `docs/delivery/workflow.md`: Reference only. Workflow and modeling guidance aligned to evergreen semantics.
- `docs/delivery/eval-harness-rfc-sections-1-10.md`: Reference only. Eval-harness rationale, object model, scenario coverage, and scoring philosophy.
- `docs/delivery/eval-harness-rfc-sections-11-15.md`: Reference only. Eval-harness operating model, dataset strategy, judging, phases, and release policy.

If you need evaluation execution history:
- `docs/workstreams/WS-001-eval-harness/`: Execution history. Earlier eval-harness framing material.
- `docs/workstreams/WS-002-semantic-lock/`: Execution history. Semantic-lock history and transition artifacts.

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
