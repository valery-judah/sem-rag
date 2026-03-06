# Plans Index

This repo keeps planning artifacts close to the feature they govern. There is no separate `exec-plans/` tree yet.

## Planning Hierarchy

- [`phase1.md`](./phase1.md): MVP north star, system milestones, and cross-feature sequencing
- `docs/features/<feature>/04_workplan.md`: canonical execution plan for a feature
- feature-adjacent design or implementation notes: supporting slices for a specific PR, runner, or refactor

## Current Feature Workplans

- [`features/source-connectors/04_workplan.md`](./features/source-connectors/04_workplan.md)
- [`features/parsers/04_workplan.md`](./features/parsers/04_workplan.md)
- [`features/hybrid-parsers/04_workplan.md`](./features/hybrid-parsers/04_workplan.md)
- [`features/pdf-pipeline/04_workplan.md`](./features/pdf-pipeline/04_workplan.md)
- [`features/e2e/04_workplan.md`](./features/e2e/04_workplan.md)

## Supporting Plan Artifacts

Some features keep narrower planning artifacts next to the main workplan. Current examples include:

- PDF pipeline implementation slices in `docs/features/pdf-pipeline/pr*_*.md`
- PDF pipeline scratch/proposal notes such as `docs/features/pdf-pipeline/proposed_plan_change.md`
- hybrid parser follow-on design notes such as `docs/features/hybrid-parsers/06_pr4_design.md`

These supporting files are useful only when they clearly point back to the owning RFC and `04_workplan.md`. They are not a replacement for the canonical feature workplan.

## Authority Rules

- `01_rfc.md` is authoritative for feature behavior and contracts.
- `04_workplan.md` is authoritative for execution order, PR slicing, and acceptance checks.
- Supporting plan files should narrow or stage the work, not redefine the feature contract.
- Control-plane docs such as this page should route to plan artifacts, not restate their full content.

## Future Direction

If the repo grows into multi-service runtime work, a dedicated plans directory may become useful. Until then, keep plans near the feature folder they modify.
