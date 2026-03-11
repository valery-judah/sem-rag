---
artifact_kind: decision
id: WS-006-D1
title: Query Lifecycle Open-Question Decisions Baseline
status: accepted
created: 2026-03-11
updated: 2026-03-11
---

# Purpose
Record the resolved positions for the open questions in `00_requirements-v0.md` so later requirement variants can be checked against one stable decision baseline.

This document is a workstream decision record. It does not create a public API contract.

## Authority And Inputs
This baseline is derived from:

- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/evergreen/eval-support-semantics.md`
- `docs/workstreams/WS-006-query-lifecycle/00_requirements-v0.md`
- `docs/workstreams/WS-006-query-lifecycle/01_requirements-critique.md`
- `src/parity/_contracts/models.py`

When a future requirement draft conflicts with this document, treat that as an intentional design change that must be argued explicitly rather than as a silent wording difference.

## Decision Summary
The selected variants are:

1. Query execution scope: `B` corpus-wide immediately
2. Intent handling: `B` lightweight explicit intent handling
3. Support sufficiency decision point: `C` hybrid pre-generation assessment plus render-time enforcement
4. Citation minimum: `B` common citation core plus format-appropriate locator

## Decision 1: Corpus-Wide Query Execution Immediately
### Decision
MVP query execution operates corpus-wide from the start.

The runtime query boundary is the workspace or equivalent corpus boundary, not an individual document. The implementation may still use document-local helpers internally, but the query path should not be temporarily defined as document-scoped while the broader path is under construction.

### Why This Decision Was Chosen
- The MVP product scope is explicitly corpus-bounded and supports retrieval from one or more documents.
- Cross-document retrieval is not an optional enhancement; it is part of the target query behavior.
- A temporary document-scoped execution model would create the wrong contract pressure and make later broadening look like a semantic shift instead of completion of the intended lifecycle.
- Early corpus-wide behavior forces selection, synthesis, citation, and abstention logic to be designed against the real query boundary.

### Tradeoffs Accepted
- Stage 1 implementation becomes more demanding because ranking, tie handling, and evidence identity need to work across documents immediately.
- Debugging can still use document-scoped inspection seams, but those seams are subordinate to the corpus-wide contract.

### What Future Requirements Should Preserve
- Query intake is against a corpus or workspace boundary.
- Retrieval can return evidence from one or more documents by default.
- No requirement text should imply that users must choose a single document before asking an MVP query.

## Decision 2: Lightweight Explicit Intent Handling
### Decision
MVP preserves explicit query-intent handling, but keeps it lightweight and deterministic rather than introducing a heavyweight classifier or planner.

The lifecycle should normalize query intent into a small set of operational modes that materially affect retrieval and context assembly. A practical MVP set is:

- factual lookup
- explanation
- synthesis
- source navigation

Scope preference may also be represented explicitly as `one-document`, `cross-document`, or `auto`.

Insufficient evidence is not an intent class. It is an outcome of support assessment.

### Why This Decision Was Chosen
- A single generic query path erases distinctions that matter for retrieval depth, neighbor expansion, citation strictness, and synthesis behavior.
- The current requirements already recognize that intent distinctions matter downstream.
- MVP does not need a learned classifier if deterministic rules or prompt-side normalization can produce stable intent hints.
- Keeping intent handling lightweight reduces implementation cost while still improving retrieval and assembly behavior in meaningful ways.

### Tradeoffs Accepted
- Intent handling may be imperfect or coarse in early versions.
- The initial intent set should stay small; adding many categories too early would create classification complexity without clear product value.

### What Future Requirements Should Preserve
- There is an explicit interpretation stage before retrieval.
- Intent influences retrieval and context assembly behavior.
- Requirement text should not treat intent handling as equivalent to a generic prompt wrapper with no downstream effect.

## Decision 3: Hybrid Support Sufficiency Decision
### Decision
Support sufficiency is decided through a hybrid policy:

- first, explicitly assess support after retrieval, selection, and context assembly;
- then, enforce that decision during answer rendering with downgrade-only guards.

The runtime should make support state explicit before generation. That stage should determine whether the available evidence is sufficiently supportive, only partially supportive, or insufficient for the requested answer shape. That assessment then constrains answer mode:

- direct supported answer
- narrowed or qualified answer
- abstention

Rendering may further downgrade the outcome if grounding or citation checks fail, but it must not upgrade an insufficient or partial evidence state into a stronger answer.

### Why This Decision Was Chosen
- Evergreen support semantics define sufficiency as a property of the evidence set, not of the generated prose.
- If generation is the sole judge of sufficiency, support policy becomes opaque and difficult to validate.
- A pre-generation support decision makes abstention and scope narrowing explicit instead of treating them as prompt accidents.
- A render-time guard is still necessary because citation mismatches, unsupported wording, or answer overreach can appear after the support decision.

### Tradeoffs Accepted
- This introduces a distinct support-assessment stage into the lifecycle.
- The current internal `AnswerStatus` shape is binary, so future requirement variants may need a separate support-state field or equivalent answer-mode representation.

### What Future Requirements Should Preserve
- Support state is assessed explicitly before generation.
- Partial support remains visible as a decision concern even if the final external answer surface stays simple.
- Rendering cannot silently convert weak or incomplete evidence into a fully supported answer.

## Decision 4: Minimal Citation Payload With Format-Specific Locator
### Decision
The smallest acceptable MVP citation payload is:

- common citation core:
  - `doc_id`
  - `document_title`
  - `snippet`
- plus at least one format-appropriate locator:
  - Markdown: `heading_path` or `section_id`
  - PDF: `page_label` or equivalent page locator

Additional fields such as `chunk_id` and `passage_anchor` remain preferred, but they are not the minimum required payload.

### Why This Decision Was Chosen
- The common core alone is not enough for source navigation trust across both supported source types.
- Evergreen citation semantics require Markdown citations to be navigable through heading structure or another stable local locator.
- Evergreen citation semantics require PDF citations to land a reviewer on the correct page or equivalent coarse page location.
- The format-specific locator rule is the smallest shape that still satisfies inspectability without requiring span-perfect anchors.

### Tradeoffs Accepted
- The current degraded internal `SourceReference` minimum is weaker than the chosen baseline because it does not require a locator beyond document identity and snippet.
- Requirement variants that adopt this decision may need to strengthen citation contracts or make the distinction between degraded internal storage and user-visible citation payload explicit.

### What Future Requirements Should Preserve
- Supported answers always include inspectable citations.
- Citation minimums differ by source type only at the locator layer, not at the document-identity layer.
- Requirement text should not accept snippet-only citations as sufficient for Markdown or PDF source navigation.

## Comparison Checklist For Future Requirement Drafts
Use this checklist when reviewing another WS-006 requirements variant.

### Query Scope
- Does it make corpus-wide query execution the default MVP behavior?
- Does it avoid redefining MVP query intake as document-scoped?

### Intent Handling
- Does it preserve an explicit interpretation stage?
- Does intent change retrieval or context assembly behavior in concrete ways?
- Does it avoid treating insufficient evidence as an intent class?

### Support Decision
- Does it make support assessment explicit before generation?
- Does it preserve partial support as a real decision state?
- Does it keep render-time checks from upgrading unsupported answers?

### Citation Minimum
- Does every supported answer citation include document identity and snippet?
- Do Markdown citations include a stable local locator?
- Do PDF citations include a page-level locator?
- Does the draft avoid treating overly broad or non-localizable provenance as acceptable?

## Non-Decisions
This baseline does not settle:

- the final external API shape
- the exact internal stage object names
- the exact prompt design
- the full answer schema for partial-support cases
- the exact ranking or reranking algorithm

Those choices should remain open unless and until a later workstream artifact resolves them explicitly.
