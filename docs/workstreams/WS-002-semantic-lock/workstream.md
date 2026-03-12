---
artifact_kind: workstream
id: WS-002
title: Semantic Lock
work_type: feature
status: archived
owner:
created: 2026-03-09
updated: 2026-03-10
tags: []
# Optional later note: paths that become relevant once framing work starts.
affected_paths:
  - docs/evergreen/eval-vocabulary.md
  - docs/evergreen/eval-support-semantics.md
  - docs/evergreen/eval-scenario-taxonomy.md
  - docs/evergreen/eval-failure-taxonomy.md
  - docs/delivery/eval-harness-rfc-sections-1-10.md
  - docs/delivery/eval-harness-rfc-sections-11-15.md
  - docs/evergreen/mvp.md
  - docs/delivery/workflow.md
# Optional later note: components or subsystems involved in the work.
affected_components:
  - evaluation semantics
  - support-state definitions
  - scenario taxonomy
  - failure taxonomy
  - citation expectations
blockers: []
depends_on:
  - WS-001
# Optional later note: durable docs that may need review or update.
evergreen_targets:
  - docs/evergreen/eval-vocabulary.md
  - docs/evergreen/eval-support-semantics.md
  - docs/evergreen/eval-scenario-taxonomy.md
  - docs/evergreen/eval-failure-taxonomy.md
adr_links: []
rfc_links:
  - docs/delivery/eval-harness-rfc-sections-1-10.md
  - docs/delivery/eval-harness-rfc-sections-11-15.md
validation_evidence:
  - docs/evergreen/eval-vocabulary.md
  - docs/evergreen/eval-support-semantics.md
  - docs/evergreen/eval-scenario-taxonomy.md
  - docs/evergreen/eval-failure-taxonomy.md
  - docs/delivery/workflow.md
  - docs/delivery/eval-harness-rfc-sections-1-10.md
  - docs/delivery/eval-harness-rfc-sections-11-15.md
gate: none
# Optional later note: docs worth reading first once framing work begins.
context_dependencies:
  - docs/evergreen/mvp.md
  - docs/delivery/workflow.md
  - docs/delivery/eval-harness-rfc-sections-1-10.md
  - docs/delivery/eval-harness-rfc-sections-11-15.md
# Optional later note: useful commands discovered during framing or execution.
commands:
  - sed -n '520,630p' docs/delivery/eval-harness-rfc-sections-11-15.md
  - docs/harness/scripts/lint-docs.sh
# Optional later note: constraints or non-goals to keep visible.
boundaries:
  - Freeze the minimum shared evaluation semantics before building runners or scorecards.
  - Stay within the MVP scope defined in docs/evergreen/mvp.md.
  - Do not broaden supported source types beyond text-based PDFs and Markdown.
  - Do not start dataset authoring, evaluator implementation, or CI gating in this phase.
  - Keep evergreen docs as the semantic source of truth, with the workstream tracking promotion work and later eval artifacts applying the taxonomy operationally.
---

# Summary
Lock the minimum shared evaluation semantics for the eval harness so later dataset and harness work uses stable vocabulary, support criteria, scenario classes, and failure categories from dedicated evergreen artifacts rather than RFC or workstream text.

## Objective
Turn RFC Phase 1 into repo-level working definitions for evaluation vocabulary, support-state semantics, scenario taxonomy, failure taxonomy, representation quality, retrieval quality, context quality, answer quality, failure quality, and citation expectations needed to unblock dataset authoring and harness implementation.

## Non-goals
- Build harness runners, scorecards, or CI integration.
- Author the seed corpus, corpus manifest, or baseline dataset.
- Add model-assisted judging, release gates, or prototype comparison reports.
- Broaden product scope beyond MVP document-grounded QA semantics.

## Current status
RFC section 13.1 defined the semantic-lock phase and its intended outputs. Those outputs have now been promoted into evergreen docs: evaluation vocabulary, support semantics, scenario taxonomy, and failure taxonomy exist as separate draft artifacts, the overlapping RFC sections point at evergreen authority, and the original extracted baselines remain in this workstream as archival transition material. The semantic review pass is complete: workflow and RFC wording now align with the evergreen ownership split, the scenario taxonomy remains frozen for baseline authoring, and Phase 1 semantic lock is complete.

## Next step
- Use the locked semantics in Phase 2 baseline dataset authoring and later harness implementation without redefining scenario classes, support-state labels, or failure classes in downstream artifacts.

## Relevant context
- paths: `docs/delivery/eval-harness-rfc-sections-1-10.md`, `docs/delivery/eval-harness-rfc-sections-11-15.md`, `docs/evergreen/mvp.md`, `docs/delivery/workflow.md`
- components: evaluation semantics, support-state criteria, scenario taxonomy, failure taxonomy, citation expectations
- constraints: freeze semantics early enough to avoid downstream churn, but do not keep semantic questions open once implementation depends on them; evergreen taxonomy should define what scenario classes mean while later dataset/catalog artifacts apply that taxonomy without redefining it
- read first: `docs/evergreen/mvp.md`, `docs/delivery/workflow.md`, `docs/delivery/eval-harness-rfc-sections-1-10.md`, `docs/delivery/eval-harness-rfc-sections-11-15.md`

## Workflow steps
1. Reconcile terminology across MVP, workflow, and eval-harness RFC material.
2. Draft the minimum durable semantic docs for vocabulary, support semantics, scenario taxonomy, failure taxonomy, and citation expectations.
3. Separate stable scenario-class definitions from future operational scenario catalogs, then review and freeze the definitions needed for Phase 2 dataset authoring and Phase 3 harness skeleton work.

## Validation
- Reviewed the four evergreen semantic docs plus `docs/delivery/workflow.md` and the two eval-harness RFC docs for semantic gaps, authority contradictions, and remaining duplicated definitions.
- Normalized workflow and RFC wording to the locked support-state labels: sufficient support, partial support, and insufficient support.
- Confirmed the main scenario classes remain frozen for baseline dataset authoring and are consistently named across evergreen, workflow, and RFC material.
- Confirmed the seven canonical failure classes remain distinct, including citation failure and failure-quality failure as separate categories from answering failure.
- Ran `docs/harness/scripts/lint-docs.sh` successfully after the review pass.

## Worklog
### 2026-03-09
- Initialized WS-002 for the Semantic Lock phase from RFC section 13.1.
- Framed the workstream around Phase 1 outputs, boundaries, and evergreen targets.
- Clarified that scenario taxonomy should live in its own evergreen artifact rather than being folded into the vocabulary doc.

### 2026-03-10
- Promoted Phase 1 semantics into separate evergreen drafts: `eval-vocabulary.md`, `eval-support-semantics.md`, `eval-scenario-taxonomy.md`, and `eval-failure-taxonomy.md`.
- Updated the evergreen vocabulary doc to act as the live glossary instead of a derivative RFC extract.
- Pruned overlapping RFC semantics so the RFCs now point to evergreen authority for vocabulary, support semantics, scenario taxonomy, and failure taxonomy while keeping implementation-facing and operational material.
- Archived the original extracted vocabulary and scenario-taxonomy snapshots in this workstream as `*-extracted-baseline.md` artifacts with explicit non-authoritative notices.
- Decided to freeze the canonical scenario taxonomy for baseline authoring while leaving dataset composition, rubric policy, and suite composition open for later phases.
- Updated the scenario-taxonomy evergreen doc to state the freeze boundary explicitly and to require an explicit semantic-change decision for rename, split, merge, or redefinition changes.
- Aligned the Phase 1 RFC outputs list so `docs/evergreen/eval-scenario-taxonomy.md` is included alongside the other semantic-lock artifacts.
- Reviewed the evergreen semantics docs, `docs/delivery/workflow.md`, and the pruned RFC sections for semantic gaps, authority contradictions, and duplicate definitions.
- Normalized workflow and RFC support-state wording to sufficient support, partial support, and insufficient support.
- Renamed workflow and dataset-authoring headings to the frozen canonical scenario-class names while preserving aliases only as explanatory notes.
- Aligned workflow failure-taxonomy usage to the seven evergreen failure classes, keeping citation failure and failure-quality failure distinct from answering failure.
- Declared Phase 1 semantic lock complete and closed `WS-002`.
- Added an evaluation-docs map to `docs/README.md` so the canonical evergreen eval docs, reference RFCs, and related workstreams have a single routing entrypoint.
- Ran `docs/harness/scripts/lint-docs.sh`; it passes after the review pass.

## Linked artifacts
- RFC core: `docs/delivery/eval-harness-rfc-sections-1-10.md`
- RFC implementation plan: `docs/delivery/eval-harness-rfc-sections-11-15.md`
- Related framing work: `docs/workstreams/WS-001-eval-harness/workstream.md`
- Evergreen semantic outputs: `docs/evergreen/eval-vocabulary.md`, `docs/evergreen/eval-support-semantics.md`, `docs/evergreen/eval-scenario-taxonomy.md`, `docs/evergreen/eval-failure-taxonomy.md`
- Historical transition artifacts retained in this workstream: `eval-vocabulary-extracted-baseline.md`, `eval-scenario-taxonomy-extracted-baseline.md`
