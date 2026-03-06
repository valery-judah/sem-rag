# Pipeline Map

**Status:** Verified
**Last verified:** 2026-03-05

This document maps the Phase 1 semantic pipeline in [`mvp-1.md`](./mvp-1.md) to the current repository. It is a navigation aid, not a normative schema source.

## Component Crosswalk

| Phase 1 component | Current code | Current docs | Status |
|---|---|---|---|
| Source Connectors | `src/docforge/connectors/` | `docs/features/source-connectors/` | Implemented as a repo subsystem with feature-spec coverage |
| Structural Parser & Distiller | `src/docforge/parsers/` | `docs/features/parsers/` | Implemented as a repo subsystem with feature-spec coverage |
| Hierarchical Segmenter | No dedicated package yet | `docs/features/chunking/` | Planned/documented; not a stable package yet |
| LLM Augmentor | No dedicated package yet | `docs/mvp-1.md` | Phase-level concept only |
| Graph Extractor | No dedicated package yet | `docs/mvp-1.md` | Phase-level concept only |
| Semantic & Relational Encoder | `src/docforge/retrieval.py` only covers a small demo slice | `docs/mvp-1.md` | Partial demo only; no production embedding layer |
| Index Publisher | No dedicated package yet | `docs/mvp-1.md` | Planned/documented only |

## PDF-Oriented Subpipeline

The current repo has a significant PDF-specific track that cuts across the broader Phase 1 map:

- intermediate PDF-hybrid schema and orchestration docs: `docs/features/hybrid-parsers/`
- production-path runner and wiring docs: `docs/features/pdf-pipeline/`
- local evaluation harness docs: `docs/features/e2e/`
- implementation code: `src/docforge/parsers/pdf_hybrid/`

Treat these as parser-adjacent work, not as a separate top-level system from Phase 1.

## Authority Rules

Use the following authority order when reading or changing the pipeline:

1. `docs/mvp-1.md` for MVP pipeline purpose, components, invariants, and milestones
2. `docs/features/<feature>/01_rfc.md` for feature-local normative behavior
3. `docs/features/<feature>/03_design.md` for implementation design
4. `docs/features/<feature>/04_workplan.md` for execution slicing and acceptance checks

Control-plane docs like this file and [`PLANS.md`](./PLANS.md) summarize and route. They should not redefine schemas from `mvp-1.md` or the feature RFCs.

## Reading Paths

For connector work:

- start with `docs/mvp-1.md` section 3.1
- then read `docs/features/source-connectors/00_context.md`
- then use `docs/features/source-connectors/01_rfc.md` and `04_workplan.md`

For canonical parser work:

- start with `docs/mvp-1.md` section 3.2
- then read `docs/features/parsers/00_context.md`
- then use `docs/features/parsers/01_rfc.md` and `04_workplan.md`

For PDF-hybrid work:

- start with parser and hybrid RFCs in `docs/features/parsers/` and `docs/features/hybrid-parsers/`
- use `docs/features/pdf-pipeline/` for production-path wiring details
- use `docs/features/e2e/` for local harness and artifact validation
