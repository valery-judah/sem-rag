# Architecture

**Status:** Verified
**Last verified:** 2026-03-05

## Purpose
This file captures stable architectural truth for `docforge` and maps the current codebase to the semantic-pipeline MVP described in [`docs/mvp-1.md`](../mvp-1.md). Use it when you need the current high-level system shape, repo boundaries, or dependency directions. It is a repo map, not a replacement for workstream RFCs or schema docs.

## When To Use
- Starting work on a subsystem
- Explaining repo boundaries to a new contributor
- Checking whether a proposed change should become an ADR

## Current System Shape
The repository is organized around a pipeline-oriented core plus a lightweight demo surface:

- `src/docforge/connectors/`: source fetch contracts and connector implementations that produce `RawDocument`
- `src/docforge/parsers/`: canonical parsing contracts, default parser flow, tree construction, and canonicalization
- `src/docforge/parsers/pdf_hybrid/`: PDF-specific engine orchestration, intermediate schema, runner adapters, and distillation logic
- `src/docforge/retrieval.py`: in-memory retrieval demo logic
- `src/docforge/cli.py`: demo entry point
- `src/docforge/devtools/`: repo-local developer utilities such as secret scanning
- `tests/`: unit coverage for connectors, parsers, retrieval, and PDF-hybrid components

## Dependency Directions
Keep the dependency flow aligned to the semantic pipeline:

1. Connectors own source enumeration and raw-byte delivery.
2. Parsers own canonical text, structure trees, anchors, and parser metadata.
3. PDF-hybrid code is a parser subsystem, not a separate product surface.
4. Retrieval code consumes text representations; it does not define parser or connector contracts.
5. Docs in `docs/workstreams/` define workstream-level contracts and execution plans; code should follow those contracts rather than invent parallel behavior.

In practice:

- `connectors` must not parse or normalize content.
- `parsers` must not take ownership of connector sync policy.
- `pdf_hybrid/engines` must stay focused on engine execution and normalization, leaving final canonical output to parser-level contracts.
- demo retrieval code should stay decoupled from parser internals unless a workstream RFC explicitly connects them.

## Phase 1 Coverage Map
`docs/mvp-1.md` describes a broader end-state than the current codebase.

- Present in code today: source connectors, structural parsing, PDF-hybrid parsing work, retrieval demo utilities
- Present mostly in docs today: hierarchical segmentation, augmented views, graph extraction, publishing/index layers
- Planned but not yet represented as stable runtime surfaces: local multi-service orchestration, generated schema references, deploy/runbook material

Use [`docs/PIPELINE.md`](../PIPELINE.md) for the detailed crosswalk from Phase 1 components to current code and workstream folders.

## Documentation Authority
- `docs/mvp-1.md` is the MVP north star for system shape and milestone sequencing.
- `docs/workstreams/*/01_rfc.md` is normative for workstream-local contracts.
- `docs/workstreams/*/03_design.md` and `04_workplan.md` define implementation details and execution slices.
- Control-plane docs such as this file, [`docs/README.md`](../README.md), and [`docs/PLANS.md`](../PLANS.md) summarize and route; they should not duplicate normative schemas.
- Durable architecture belongs here or in ADRs, not in time-scoped workstream notes.
