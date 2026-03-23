# Documentation Map

## Purpose
`docs/` is the repository documentation system for durable product truth, current repo documentation, optional execution records, architecture decisions, and reusable documentation tooling.

Authority note: `docs/evergreen/` holds the canonical product and repo truth. `docs/delivery/` may contain planning, architecture, or workflow drafts retained for reference, but it is not the canonical source of product scope. 

## Quick Routes

Product Scope:
- `docs/evergreen/mvp.md`: Canonical. Product north star and scope boundary.

Implementation Truth:
- `docs/evergreen/architecture.md`: Canonical. Current architecture and implementation gap.

Stable Interfaces:
- `docs/evergreen/api-contracts.md`: Canonical. Stable localhost FastAPI and OpenAPI interfaces that exist today.

Commands And Validation:
- `docs/evergreen/runbook.md`: Canonical. Local operation guidance and standard commands.
- `docs/evergreen/manual-e2e.md`: Canonical. Step-by-step manual end-to-end ingestion test.

Local LLM / Docker Defaults:
- `docs/workstreams/WS-008-local-llm/01_local_llm_runtime_note.md`: Execution history for optional MLX/Ollama generation, Apple Silicon host-Ollama defaults for Docker-backed local flows, and the comparison smoke harness.

Evaluation Docs:
- See `Evaluation Docs Map` below for the detailed route across evergreen, delivery, and workstream material.

## Directory Map
- `evergreen/`: current durable system truth and operational references
- `conventions/`: coding standards, observability rules, and implementation patterns
- `delivery/`: non-canonical planning, architecture, and workflow drafts kept for reference
- `workstreams/`: optional time-scoped execution records, RFC/proposal material, design notes, and evidence
- `adrs/`: durable architecture decision records promoted out of individual workstreams when needed
- `harness/`: templates, conventions, playbooks, and helper scripts for humans and agents

## Where New Work Goes
- Put new implementation work, RFC/proposal material, decisions, evidence, and handoff notes in the relevant folder under `docs/workstreams/WS-XXX-{slug}` folders. Choose a `work_type` from `docs/harness/taxonomy/workstream-taxonomy.md`, then prefer `make workstream-new type=feature slug=my-feature` to create the scaffold. `WS-XXX-workstream.md` is the canonical lightweight workstream card, and `WS-XXX-framing.md` is the scaffold for the framing stage. The underlying script is `docs/harness/scripts/new-workstream.sh <work_type> <slug>`.
