---
artifact_kind: workstream
id: WS-002
title: Semantic Lock
work_type: feature
status: active
owner:
created: 2026-03-09
updated: 2026-03-09
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
validation_evidence: []
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
RFC section 13.1 defines the semantic-lock phase, its objective, primary outputs, key activities, and exit criteria. The work is still preliminary in the repo: the key semantic definitions are not yet promoted into evergreen docs, and downstream phases depend on freezing these terms before schema, annotation, and runner work expands.

## Next step
- Extract candidate definitions from the eval-harness RFC and draft the first evergreen semantic docs for vocabulary, support semantics, scenario taxonomy, and failure taxonomy.

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
- Confirm the definitions of sufficient, partial, and insufficient support are explicit and non-overlapping.
- Confirm the main scenario classes are frozen for baseline dataset authoring and assigned to a dedicated evergreen taxonomy doc.
- Confirm major failure categories are named, distinct, and useful for later evaluator outputs.
- Confirm citation expectations are stated for PDF and Markdown evidence.
- Record review evidence showing semantic agreement before downstream implementation begins.

## Linked artifacts
- RFC core: `docs/delivery/eval-harness-rfc-sections-1-10.md`
- RFC implementation plan: `docs/delivery/eval-harness-rfc-sections-11-15.md`
- Related framing work: `docs/workstreams/WS-001-eval-harness/workstream.md`
- Planned evergreen outputs: `docs/evergreen/eval-vocabulary.md`, `docs/evergreen/eval-support-semantics.md`, `docs/evergreen/eval-scenario-taxonomy.md`, `docs/evergreen/eval-failure-taxonomy.md`
