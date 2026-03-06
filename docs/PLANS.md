# Plans Index

This repo keeps planning artifacts close to the feature they govern. There is no separate `exec-plans/` tree yet.

## Status Legend

- `Active`: current execution entrypoint
- `Historical`: useful background or completed/mostly-completed plan, but not the default starting point
- `Superseded`: replaced by a newer or more repo-accurate planning artifact

## Planning Hierarchy

- [`mvp-1.md`](./mvp-1.md): MVP north star, system milestones, and cross-feature sequencing
- `docs/features/<feature>/04_workplan.md`: canonical execution plan for a feature
- feature-adjacent design or implementation notes: supporting slices for a specific PR, runner, or refactor

## Current Feature Workplans

- `Active`: [`features/pdf-pipeline/04_workplan.md`](./features/pdf-pipeline/04_workplan.md) for current hybrid PDF production-path execution
- `Active`: [`features/e2e/04_workplan.md`](./features/e2e/04_workplan.md) for the local real-engine evaluation harness
- `Historical`: [`features/parsers/04_workplan.md`](./features/parsers/04_workplan.md) as the foundational parser workplan
- `Historical`: [`features/hybrid-parsers/04_workplan.md`](./features/hybrid-parsers/04_workplan.md) as the foundational hybrid PDF workplan
- `Historical`: [`features/source-connectors/04_workplan.md`](./features/source-connectors/04_workplan.md) as connector background, with drift and contradictions captured in [`features/source-connectors/05_refactor.md`](./features/source-connectors/05_refactor.md)

`docs/features/hybrid-parsers/01_rfc.md` remains contract-authoritative even when [`features/hybrid-parsers/04_workplan.md`](./features/hybrid-parsers/04_workplan.md) is treated as historical.

## Supporting Plan Artifacts

Some features keep narrower planning artifacts next to the main workplan. Current examples include:

- `Historical`: PDF pipeline implementation slices such as [`features/pdf-pipeline/pr2_implementation_plan.md`](./features/pdf-pipeline/pr2_implementation_plan.md)
- `Historical`: PDF pipeline implementation slices such as [`features/pdf-pipeline/pr4_mineru_implementation_plan.md`](./features/pdf-pipeline/pr4_mineru_implementation_plan.md)
- `Historical`: hybrid parser follow-on design notes such as [`features/hybrid-parsers/06_pr4_design.md`](./features/hybrid-parsers/06_pr4_design.md)
- `Superseded`: [`features/pdf-pipeline/proposed_plan_change.md`](./features/pdf-pipeline/proposed_plan_change.md)
- `Superseded`: [`features/hybrid-parsers/08_e2e_evaluation_plan.md`](./features/hybrid-parsers/08_e2e_evaluation_plan.md)

These supporting files are useful only when they clearly point back to the owning RFC and `04_workplan.md`. They are not a replacement for the canonical feature workplan.

## Authority Rules

- `01_rfc.md` is authoritative for feature behavior and contracts.
- `04_workplan.md` is authoritative for execution order, PR slicing, and acceptance checks.
- Supporting plan files should narrow or stage the work, not redefine the feature contract.
- Control-plane docs such as this page should route to plan artifacts, not restate their full content.

## Future Direction

If the repo grows into multi-service runtime work, a dedicated plans directory may become useful. Until then, keep plans near the feature folder they modify.
