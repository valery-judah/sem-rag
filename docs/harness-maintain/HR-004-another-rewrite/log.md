# HR-004 Log

## Purpose
This log records the reasoning and completed edits for the repo-wide routing-discourse cleanup carried out under `HR-004-another-rewrite`.

This note is non-canonical execution history. It does not override the authority model in `docs/evergreen/` or the routing docs it describes.

## Reasoning
The main issue was not missing documentation structure. The repo already had the right routing surfaces and authority distinctions. The problem was rhetorical: several high-leverage entry docs were written in task-prompt form such as `If you need ...`, which reads like instructions for a weak agent rather than navigation for an expert reader.

The refactor treated this as a change in reader posture:

- routing sections should behave like compact reference indexes
- headings should expose subject areas directly
- authority should remain visible at the destination bullet
- connective prose should stay minimal
- the information model should remain unchanged

The guiding rule for the rewrite was:

> convert routing prose from task-prompt form to topic-index form while preserving authority semantics and route coverage

## What Was Done
### Repo-wide routing rewrite
The routing blocks in the following files were rewritten from conditional prompt phrasing to topic-led navigation:

- `AGENTS.md`
- `docs/README.md`
- `docs/evergreen/architecture.md`

The change preserved:

- the same destinations
- the same `Canonical`, `Reference only`, and `Execution history` labels
- the same routing coverage
- the same hierarchy between top-level routes and the more detailed evaluation-docs map

### `AGENTS.md` changes
`AGENTS.md` was already close to the desired structure after the initial topic-led rewrite. A later tightening pass addressed two remaining issues:

- renamed `Evaluation Semantics` to `Evaluation Docs` so the heading matches the actual scope of the bullets
- clarified that `## Canonical Docs` is a canonical-doc inventory, not a second routing block
- updated `docs/README.md` references from `task-based routes` to `topic-based routes`

This kept `## Agent Quick Routes` strictly navigational while preserving the later list as an inventory/reference surface.

### `docs/README.md` changes
The docs-system README became the main model for expert-oriented routing:

- rewrote `## Quick Routes` with topic-led headings such as `Product Scope`, `Implementation Truth`, and `Evaluation Docs`
- rewrote the evaluation sub-map with direct semantic headings such as `Glossary And Layer Names`, `Support, Citation, And Abstention`, and `Execution History`
- removed duplicated evaluation-route blocks from the top-level quick routes and pointed readers to the dedicated evaluation map instead
- removed the repeated local authority reminder below the evaluation map once the top-level authority note was deemed sufficient

The result is a denser index with less repetition and stronger information scent.

### `docs/evergreen/architecture.md` changes
The architecture doc kept its local routing function but now presents it in topic-index form:

- replaced `If you need ...` phrasing with headings like `Product Scope`, `Stable Public Package API`, and `Current Implementation Seams`
- preserved local authority labels such as `Canonical`, `Reference only`, `Execution history`, and `Implemented internal`

This kept the architecture doc usable as a local map without reverting to prompt-style scaffolding.

## Review Feedback Incorporated
Two critique passes shaped the later edits:

- `AGENTS.md` critique: accepted the naming fix for `Evaluation Docs` and the need to make `## Canonical Docs` explicitly distinct from quick routes
- `docs/README.md` critique: accepted the density fix to remove the repeated evaluation authority note, but left `Commands And Validation` unchanged to preserve parallel structure across routing docs

## Current Outcome
After the cleanup:

- the main routing docs read as navigation for expert readers
- authority remains explicit at the bullet level
- duplicated routing and background phrasing was reduced
- the repo’s documentation entrypoints are more consistent with each other

## Changed Files
- `AGENTS.md`
- `docs/README.md`
- `docs/evergreen/architecture.md`

## Validation
The completed checks for this cleanup were:

- readback of each rewritten routing block to confirm scanability
- `git diff` review of the edited files
- repo search for `If you need` to confirm removal from the targeted routing sections

No code tests were run because this was a docs-only change.
