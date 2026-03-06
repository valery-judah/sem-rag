# Documentation Index

This repository uses a two-layer documentation model:

- control-plane docs explain what the repo is, how the semantic pipeline is organized, and where to look next
- implementation-spec docs in `docs/features/` define feature-local contracts, designs, and workplans

## MVP North Star

- [`mvp-1.md`](./mvp-1.md): semantic-pipeline MVP contract, component boundaries, invariants, and milestones
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md): current code map and dependency directions
- [`PIPELINE.md`](./PIPELINE.md): crosswalk from `mvp-1.md` components to current code and feature folders

## Control-Plane Docs

- [`PLANS.md`](./PLANS.md): where execution plans and workplans live
- [`context-management/backend-related-schema.md`](./context-management/backend-related-schema.md): rationale for the current docs structure
- [`runbooks/local-dev.md`](./runbooks/local-dev.md): scaffold for future runtime and `docker-compose` bring-up docs
- [`generated/README.md`](./generated/README.md): placeholder for future generated references

## Implementation-Spec Layer

### Shared workflow docs
- [`00_playbook.md`](./00_playbook.md): reusable feature-doc workflow
- [`01_artifact_contracts.md`](./01_artifact_contracts.md): authority rules for feature artifacts
- [`02_quality_gates.md`](./02_quality_gates.md): reusable quality-gate guidance
- [`03_agent_protocol.md`](./03_agent_protocol.md): coding-agent execution protocol for planned feature work

### Feature folders
- [`features/source-connectors/`](./features/source-connectors/): raw-document ingestion contracts
- [`features/parsers/`](./features/parsers/): canonical parser contracts
- [`features/hybrid-parsers/`](./features/hybrid-parsers/): PDF-hybrid parser pipeline
- [`features/pdf-pipeline/`](./features/pdf-pipeline/): production-path PDF wiring and runner design
- [`features/e2e/`](./features/e2e/): local PDF harness docs
- [`features/chunking/`](./features/chunking/): hierarchical segmentation design work
- [`features/layout-processing/`](./features/layout-processing/): supporting research notes

## Templates

Create new feature docs from [`templates/`](./templates/):

1. Create `docs/features/<feature-name>/`
2. Copy the needed files from `docs/templates/`
3. Rename files by removing `.template`
4. Fill `01_rfc.md` first, then align the rest of the artifact set to it

Required files:

- `00_context.md`
- `01_rfc.md`
- `02_user_stories.md`
- `03_design.md`
- `04_workplan.md`

Optional files:

- `05_test_plan.md`
- `06_rollout.md`

## Future Runtime And Deployment Docs

The repo is still MVP- and pipeline-first. Runtime/deployment docs are intentionally scaffolded, not fictionalized.

- no `docker-compose.yml` exists yet
- no generated schema/API references exist yet
- when those surfaces land, they should be linked from this index and from `AGENTS.md`
