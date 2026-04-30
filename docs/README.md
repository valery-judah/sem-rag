# Docs

`evergreen/` is canonical and wins when sources disagree. `delivery/` holds earlier planning
drafts kept for reference. `workstreams/` records the history of past work and isn't kept up to
date.

## Repository and infrastructure
- `evergreen/runbook.md`: commands, local workflows, PDF-to-Markdown conversion, configuration, and troubleshooting
- `evergreen/observability-operations.md`: the observability stack, where logs and query bundles are saved, and eval run flows
- `engineering/`: Python domain modeling, logging, testing, and coding conventions
- `conventions/commit-message-conventions.md`: commit message format and types
- `harness/`: workstream templates, playbooks, taxonomy, and helper scripts

## Product
- `evergreen/mvp.md`: product scope and its boundary
- `evergreen/functional-requirements.md`: MVP acceptance criteria
- `evergreen/first-tier-failures.md`: critical failure model for source-grounded answers
- `evergreen/case-matrix-build.md`: how evaluation cases cover the MVP trust contract
- `../evals/cases/README.md`: authored evaluation cases and their schemas

## Architecture
- `evergreen/architecture.md`: current architecture and the gap to the target
- `evergreen/lifecycle-and-evidence-flow.md`: document and query lifecycles and the evidence flow
- `evergreen/retrieval-hierarchy.md`: retrieval units, provenance structure, and where each is implemented
- `evergreen/api-contracts.md`: MVP HTTP contract and the current local routes
- `adrs/`: architecture decisions

## History
- `workstreams/`: past workstreams, for example `WS-008-local-llm/` for the local Ollama and MLX setup
- `delivery/`: earlier MVP, workflow, and eval harness drafts

## Where new work goes
Create a workstream for new implementation work, proposals, decisions, evidence, and handoff
notes:

```bash
make docs-workstream-new TYPE=feature SLUG=my-feature
```

Pick the type from `harness/taxonomy/workstream-taxonomy.md`. The command creates
`workstreams/WS-XXX-<slug>/` with a `WS-XXX-workstream.md` card and a `WS-XXX-framing.md`
scaffold. Move decisions that should last into `evergreen/` or `adrs/`.
