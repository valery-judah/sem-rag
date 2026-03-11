# Documentation Map

## Purpose
`docs/` is the repository documentation system for durable product truth, current repo documentation, optional execution records, architecture decisions, and reusable documentation tooling.

Authority note: `docs/evergreen/` holds the canonical product and repo truth. `docs/delivery/` may contain planning, architecture, or workflow drafts retained for reference, but it is not the canonical source of product scope. New durable docs belong in `docs/evergreen/`, and new time-scoped execution records belong in `docs/workstreams/`.

## Quick Routes
Product Scope:
- `docs/evergreen/mvp.md`: Canonical. Product north star and scope boundary.

Implementation Truth:
- `docs/evergreen/architecture.md`: Canonical. Current architecture and implementation gap.

Agent Routing:
- `docs/evergreen/agent-routing.md`: Canonical. Coding-agent routing, implementation map, and edit starting points.

Stable Interfaces:
- `docs/evergreen/api-contracts.md`: Canonical. Stable runtime interfaces that exist today.

Commands And Validation:
- `docs/evergreen/runbook.md`: Canonical. Local operation guidance and standard commands.

Evaluation Docs:
- See `Evaluation Docs Map` below for the detailed route across evergreen, delivery, and workstream material.

Query Work:
- See `Query Docs Map` below for the canonical read order, current implementation truth, and WS-006 stage material.

Context Building:
- `docs/harness-maintain/context-building-playbook.md`: Reference only. Stable method for building context before phase-specific workstream discovery.

## Directory Map
- `evergreen/`: current durable system truth and operational references
- `delivery/`: non-canonical planning, architecture, and workflow drafts kept for reference
- `workstreams/`: optional time-scoped execution records, RFC/proposal material, design notes, and evidence
- `adrs/`: durable architecture decision records promoted out of individual workstreams when needed
- `harness/`: templates, conventions, playbooks, and helper scripts for humans and agents

## Evaluation Docs Map
Use this map when working on evaluation semantics, the eval harness, or related dataset design.

Glossary And Layer Names:
- `docs/evergreen/eval-vocabulary.md`: Canonical. Evaluation glossary, term normalization, and layer names.

Support, Citation, And Abstention:
- `docs/evergreen/eval-support-semantics.md`: Canonical. Support-state criteria, citation expectations, and abstention rules.

Scenario Taxonomy:
- `docs/evergreen/eval-scenario-taxonomy.md`: Canonical. Scenario classes and classification rules.

Failure Taxonomy:
- `docs/evergreen/eval-failure-taxonomy.md`: Canonical. Failure classes and classification rules.

Product And Implementation Framing:
- `docs/evergreen/mvp.md`: Canonical. Product north star and scope boundary.
- `docs/evergreen/architecture.md`: Canonical. Current architecture and implementation gap.
- `docs/evergreen/agent-routing.md`: Canonical. Current code-entry routing and implementation map.

Implementation Guidance:
- `docs/delivery/workflow.md`: Reference only. Workflow and modeling guidance aligned to evergreen semantics.
- `docs/delivery/eval-harness-rfc-sections-1-10.md`: Reference only. Eval-harness rationale, object model, scenario coverage, and scoring philosophy.
- `docs/delivery/eval-harness-rfc-sections-11-15.md`: Reference only. Eval-harness operating model, dataset strategy, judging, phases, and release policy.

Execution History:
- `docs/workstreams/WS-001-eval-harness/`: Execution history. Earlier eval-harness framing material.
- `docs/workstreams/WS-002-semantic-lock/`: Execution history. Semantic-lock history and transition artifacts.

## Query Docs Map
Use this map when working on the query subsystem.

Stable Context-Building Base:
- `docs/evergreen/mvp.md`: Canonical. Product scope and trust boundary.
- `docs/evergreen/architecture.md`: Canonical. Current architecture, earned seams, and implementation gap.
- `docs/evergreen/agent-routing.md`: Canonical. Agent routes, owning files, and proving tests.
- `docs/evergreen/api-contracts.md`: Canonical. Public-contract boundary. Internal query routes do not count as stable APIs.
- `docs/harness-maintain/context-building-playbook.md`: Reference only. Stable navigation and proof-building method.

WS-006 Execution Track:
- `docs/workstreams/WS-006-query-lifecycle/query_subsystem_staged_implementation_plan.md`: Stage sequence and acceptance gates.
- `docs/workstreams/WS-006-query-lifecycle/07_design.md`: Query architecture and runtime semantics.
- `docs/workstreams/WS-006-query-lifecycle/11_stage-1-queryable-corpus-boundary-design.md`: Implemented Stage 1 note, including current routes and evergreen review.
- `docs/workstreams/WS-006-query-lifecycle/12_stage-2-interpretation-foundation-design.md`: Implemented Stage 2 note, including current routes and evergreen review.
- `docs/workstreams/WS-006-query-lifecycle/13_stage-3-retrieval-foundation-design.md`: Stage 3 retrieval design and implementation note for the current repo shape.

Working Rule:
- Start with the evergreen docs for stable context.
- Use `docs/evergreen/architecture.md` for durable system shape and `docs/evergreen/agent-routing.md` for code-entry routing.
- Then open the latest implemented WS-006 stage note before planning the next phase.
- Treat workstream docs as execution history and local design notes unless evergreen docs explicitly promote a seam.

## Where New Work Goes
- Put durable system descriptions and stable operating guidance in `docs/evergreen/`.
- Put new implementation work, RFC/proposal material, decisions, evidence, and handoff notes in the relevant folder under `docs/workstreams/`.
- Promote cross-cutting, long-lived decisions from a workstream into `docs/adrs/` when they become durable.
- Do not create a top-level `docs/rfcs/`; RFC-like proposal material belongs inside workstreams.

## ADRs And Workstreams
Workstreams capture time-scoped execution and local decision-making when a change needs that structure. ADRs capture the smaller set of decisions that outlive a single workstream or affect multiple parts of the system.
