# Control-Plane Refinement Plan

## Summary

This document is the execution plan for the next control-plane refinement pass.

It exists to do three jobs at once:

- capture the current docs-control-plane state after the migration cleanup
- lock the minimal trust-metadata convention for high-signal docs
- specify the exact `README.md`, `CLAUDE.md`, and `docs/PLANS.md` changes for the next pass

This is a planning artifact only. It does not redefine feature contracts and it does not replace the existing control-plane docs.

## Current Context

The current docs migration is already past the rescue stage.

- `README.md` and `CLAUDE.md` are partly aligned with the new control plane and already route readers toward `AGENTS.md`, `ARCHITECTURE.md`, `docs/README.md`, and `docs/mvp-1.md`.
- `docs/mvp-1.md`, `ARCHITECTURE.md`, and `docs/PIPELINE.md` are high-signal system/routing docs, but none of them currently expose explicit trust metadata such as status or verification date.
- `docs/PLANS.md` is now a valid routing page, but it still makes the reader inspect feature folders to infer which workplan is the most relevant current entrypoint.

The current authority model remains locked:

- `docs/mvp-1.md` is the MVP north star for system shape, invariants, and milestone sequencing.
- `docs/features/*/01_rfc.md` is normative for feature behavior.
- `docs/features/*/03_design.md` and `04_workplan.md` are design and execution artifacts.
- Control-plane docs summarize and route; they do not redefine feature contracts.

Current repo evidence for workplan-status classification:

- `docs/features/pdf-pipeline/04_workplan.md` is explicitly marked `Partially Implemented`, includes concrete repo-reality notes, and is the clearest current execution entrypoint for hybrid PDF production-path work.
- `docs/features/e2e/04_workplan.md` is explicitly marked `Draft`, but it is still the active planning surface for the local E2E harness work.
- `docs/features/source-connectors/04_workplan.md` contains many completed checklist items, but `docs/features/source-connectors/05_refactor.md` documents contract drift and contradictions around connector responsibilities, so the workplan is useful background rather than the default current entrypoint.
- `docs/features/hybrid-parsers/04_workplan.md` is foundational and still useful, but actual execution sequencing has shifted toward `docs/features/pdf-pipeline/` and `docs/features/e2e/`.
- `docs/features/parsers/04_workplan.md` is a foundational parser workplan rather than the most obvious current execution starting point for ongoing repo work.

## Locked Decisions

- Update both `README.md` and `CLAUDE.md` in the next pass.
- Keep both docs concise and route readers into the control plane instead of adding more internal architecture detail.
- Use inline metadata lines, not YAML frontmatter, for high-signal docs.
- Metadata format for control-plane/system docs is:
  - `**Status:** Verified | Draft | Historical`
  - `**Last verified:** YYYY-MM-DD`
- Apply that metadata in the next pass to:
  - `docs/mvp-1.md`
  - `ARCHITECTURE.md`
  - `docs/PIPELINE.md`
- Do not add metadata to every feature doc in that pass.
- Tighten `docs/PLANS.md` with a short legend and explicit status labels for current feature workplans.
- `docs/PLANS.md` status meanings are locked as:
  - `Active`: current execution entrypoint
  - `Historical`: useful background or completed/mostly-completed plan, but not the default starting point
  - `Superseded`: replaced by a newer or more repo-accurate planning artifact

## Planned Changes

### Workstream A: Entrypoint narrative alignment

Update `README.md` as a short, public-facing entrypoint that:

- keeps pointing to `AGENTS.md`, `ARCHITECTURE.md`, `docs/README.md`, and `docs/mvp-1.md`
- describes the repo as a semantic-pipeline MVP spanning connectors, parsers, PDF-hybrid work, segmentation, retrieval demo, and feature docs
- avoids becoming a second architecture document

Update `CLAUDE.md` as a tool-specific entrypoint that:

- aligns its `Read First` ordering and documentation-authority language with the control plane
- keeps Claude-specific workflow guidance and command examples
- summarizes architecture only enough to route the reader to the right docs
- avoids becoming a parallel architecture source

### Workstream B: Trust metadata

Insert metadata immediately below the top title in:

- `docs/mvp-1.md`
- `ARCHITECTURE.md`
- `docs/PIPELINE.md`

Initial target statuses are:

- `docs/mvp-1.md`: `Verified`
- `ARCHITECTURE.md`: `Verified`
- `docs/PIPELINE.md`: `Verified`

`Last verified` should use the ISO date of the implementation pass that applies the change.

Keep the body text unchanged except for small wording fixes required to keep the new metadata truthful.

### Workstream C: `docs/PLANS.md` decision support

Add a short legend near the top that defines:

- `Active`
- `Historical`
- `Superseded`

Replace the plain feature-workplan list with labeled entries using this default classification:

- `docs/features/pdf-pipeline/04_workplan.md`: `Active`
- `docs/features/e2e/04_workplan.md`: `Active`
- `docs/features/parsers/04_workplan.md`: `Historical`
- `docs/features/hybrid-parsers/04_workplan.md`: `Historical`
- `docs/features/source-connectors/04_workplan.md`: `Historical`

Also add a short note that:

- `docs/features/hybrid-parsers/01_rfc.md` remains contract-authoritative even when `docs/features/hybrid-parsers/04_workplan.md` is treated as historical

In the supporting-plan section, explicitly classify obvious background artifacts:

- `docs/features/pdf-pipeline/proposed_plan_change.md`: `Superseded`
- `docs/features/hybrid-parsers/08_e2e_evaluation_plan.md`: `Superseded`
- implemented PR slice plans such as `docs/features/pdf-pipeline/pr2_implementation_plan.md`: `Historical`

This pass is classification and routing only. It must not delete, move, or reorganize those files.

## Verification

The later implementation pass should verify all of the following:

- `README.md`, `CLAUDE.md`, `AGENTS.md`, and `docs/README.md` point to the same control-plane entry docs and do not contradict one another.
- `docs/mvp-1.md`, `ARCHITECTURE.md`, and `docs/PIPELINE.md` all contain `Status` and `Last verified` lines in the same format.
- `docs/PLANS.md` makes the default current plan entrypoints obvious within one screen, without requiring feature-folder exploration.
- Repo-authored markdown link checks still pass.
- No feature RFC authority is moved into `README.md`, `CLAUDE.md`, or `docs/PLANS.md`.

## Assumptions

- `docs/context-management/doc-refactor-plan.md` is a context-management artifact, not part of the feature-doc workflow under `docs/features/`.
- The `docs/PLANS.md` classification is about where a contributor should start now, not about whether a feature area still matters conceptually.
- `Verified` means reviewed against current repo reality in that pass; it does not mean feature complete.
- This refinement pass will not prune, rename, or archive historical feature-plan files. It only makes their status legible.
