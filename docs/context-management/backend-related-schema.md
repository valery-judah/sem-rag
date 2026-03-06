# Documentation Structure Rationale For `sem-rag`

This note explains the docs refactor for the current semantic-pipeline repository. It translates the useful control-plane ideas from a backend-oriented schema into repo-specific, pipeline-first terms.

## Why The Repo Needs A Control Plane

The repo already has strong feature-level design artifacts in `docs/features/`, but those files assume the reader already knows:

- what the repo currently implements
- how the code maps to the Phase 1 semantic pipeline
- which docs are normative versus supportive
- where future runtime and deployment docs should live

That gap is what the control-plane docs solve.

## The Chosen Shape

The repository now uses a two-layer documentation model:

### 1. Control-plane docs

These are small routing docs that help an agent or engineer orient quickly:

- `AGENTS.md`
- `ARCHITECTURE.md`
- `docs/README.md`
- `docs/PIPELINE.md`
- `docs/PLANS.md`

These files summarize and route. They should stay compact and should not restate full schemas from feature RFCs.

### 2. Implementation-spec docs

These remain the detailed design and execution layer:

- `docs/phase1.md` for the MVP north star
- `docs/00_playbook.md`
- `docs/01_artifact_contracts.md`
- `docs/02_quality_gates.md`
- `docs/03_agent_protocol.md`
- `docs/features/*`
- `docs/templates/*`

This layer is where feature-specific contracts, design choices, and workplans live.

## Authority Model

The docs structure is intentionally explicit about who owns what:

- `docs/phase1.md` owns the MVP system shape, major components, invariants, and milestone sequencing.
- `docs/features/*/01_rfc.md` owns feature-local normative behavior.
- `docs/features/*/00_context.md`, `03_design.md`, and `04_workplan.md` support the RFC with context, implementation detail, and execution slicing.
- control-plane docs route to those sources; they do not redefine them.

This keeps the repo legible without creating a second, conflicting contract layer.

## Why The Language Stays Pipeline-First

The repo is not yet a deployable backend service with:

- `docker-compose.yml`
- migrations
- a database runtime surface
- API contracts as the main public interface

So the docs should not pretend it already is one.

Instead, the control plane is framed around:

- ingestion and connectors
- parsing and PDF-hybrid extraction
- retrieval preparation
- feature planning and implementation workflow
- future deployment readiness

## Future-Facing Runtime Scaffolds

Even though runtime docs are not implemented yet, the structure should make room for them now. That is why the repo adds:

- `docs/runbooks/local-dev.md`
- `docs/generated/README.md`

These are explicit scaffolds for future local orchestration, generated schema/API references, and deployment-supporting documentation. They are placeholders with guardrails, not invented operational docs.

## What `AGENTS.md` Should Do Here

For this repo, `AGENTS.md` should stay short and cover only:

- repo purpose
- command and validation rules
- canonical doc entry points
- hard constraints about documentation authority and workflow

Architecture prose, pipeline mapping, and plan navigation belong in the new control-plane docs instead.

## Non-Goals Of This Refactor

This change does not:

- move or rename `docs/features/*`
- decompose `docs/phase1.md` into many smaller canonical docs
- invent runtime, database, or `docker-compose` instructions before those surfaces exist
- replace feature RFCs with summary docs

## Bottom Line

The repo keeps its detailed feature-doc workflow, but now adds a thin control plane on top of it. That makes the current semantic-pipeline MVP easier to navigate today and gives future deployment/runtime work a clear place to land without forcing a premature backend-service structure.
