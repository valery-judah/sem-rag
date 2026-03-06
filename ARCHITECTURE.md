# Architecture Map

## Purpose

This file maps the current `docforge` codebase to the semantic-pipeline MVP described in [`docs/phase1.md`](docs/phase1.md). It is a repo map, not a replacement for feature RFCs or schema docs.

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
5. Docs in `docs/features/` define feature-level contracts and execution plans; code should follow those contracts rather than invent parallel behavior.

In practice:

- `connectors` must not parse or normalize content.
- `parsers` must not take ownership of connector sync policy.
- `pdf_hybrid/engines` must stay focused on engine execution and normalization, leaving final canonical output to parser-level contracts.
- demo retrieval code should stay decoupled from parser internals unless a feature RFC explicitly connects them.

## Phase 1 Coverage Map

`docs/phase1.md` describes a broader end-state than the current codebase.

- Present in code today: source connectors, structural parsing, PDF-hybrid parsing work, retrieval demo utilities
- Present mostly in docs today: hierarchical segmentation, augmented views, graph extraction, publishing/index layers
- Planned but not yet represented as stable runtime surfaces: local multi-service orchestration, generated schema references, deploy/runbook material

Use [`docs/PIPELINE.md`](docs/PIPELINE.md) for the detailed crosswalk from Phase 1 components to current code and feature folders.

## Documentation Authority

- `docs/phase1.md` is the MVP north star for system shape and milestone sequencing.
- `docs/features/*/01_rfc.md` is normative for feature-local contracts.
- `docs/features/*/03_design.md` and `04_workplan.md` define implementation details and execution slices.
- Control-plane docs such as this file, [`docs/README.md`](docs/README.md), and [`docs/PLANS.md`](docs/PLANS.md) summarize and route; they should not duplicate normative schemas.
