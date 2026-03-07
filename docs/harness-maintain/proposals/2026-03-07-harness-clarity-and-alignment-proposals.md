# Harness clarity and alignment follow-up proposals

## Context

The main March 7 alignment pass already landed in the live harness.

That pass made the startup path explicit, tightened `docs/harness/indexes/active-tasks.md` into an executable-task queue, aligned maintainer docs to current Layer C and Layer D canon, retired legacy Layer C shorthand from live operator docs, and added lightweight Layer A starter-value guidance during task authoring.

This note should therefore not pretend that the broad clarity pass is still pending. Its purpose is narrower:

- capture the aligned baseline that now exists,
- identify the remaining places where drift can reappear,
- and propose the next implementation work to harden the harness against that drift.

## Current aligned baseline

The live harness now already assumes the following operating model:

- fresh agents start from `docs/harness/indexes/active-tasks.md`,
- the active-task index is a derivative executable-work queue,
- authoritative task cards in `docs/harness/active/tasks/` win on mismatch,
- live Layer C vocabulary is `feature_cell` plus `control_profile`,
- task authoring uses lightweight canonical starter values for key Layer A fields,
- and early contract work stays baseline until it reaches a real review boundary.

Those decisions should remain stable. The follow-up proposals below are about keeping that baseline trustworthy over time.

## Remaining implementation gaps

### 1. Queue trust still depends on manual discipline

The active-task queue is now correctly defined, but nothing in the harness currently makes queue/card drift especially visible when maintainers forget to update the derivative index.

That leaves the harness vulnerable to regressing into the same trust problem that triggered the original alignment work:

- queue entries that no longer correspond to real task cards,
- real executable task cards missing from the queue,
- or queue state/mode summaries drifting away from the authoritative cards.

### 2. Historical Layer C shorthand still appears in broad maintainer guidance

The main operator-facing docs now use canonical Layer C language, but maintainer-facing docs still mention legacy shorthand in a few places that are broader than a strict historical-pointer role.

That is lower risk than before, but it still leaves room for maintainers to treat the old terms as active comparison vocabulary instead of narrowly historical compatibility language.

### 3. Layer A normalization is guidance-only, not maintained as a live normalization practice

The template and intake guidance now show starter values for `intent`, `knowledge_locality`, and `dependency_complexity`, which is an improvement.

The remaining gap is operational rather than conceptual:

- there is no maintainer-facing check that live task cards continue to use the preferred values,
- examples can drift quietly,
- and future cards can reintroduce ad hoc local variants without a clear repair loop.

### 4. Startup discovery is documented, but not yet maintained as a first-class maintenance scenario

The startup route for fresh agents is now explicit in the operator docs, but the harness does not yet treat "fresh-agent startup discovery" as a recurring maintenance scenario that should be rechecked whenever indexes, prompts, or workflows change.

That makes it possible for future harness edits to reintroduce implicit assumptions that the task is already known.

## Proposed implementation work

### Proposal A. Add an explicit queue-integrity maintenance check

The harness should gain one small, explicit maintenance rule for queue integrity.

Recommended shape:

- add a short "queue integrity check" procedure to `docs/harness-maintain/main.md`,
- require maintainers to verify that every default-queue entry maps to a real task card,
- require maintainers to verify that every executable task card is represented in the queue,
- and make this check part of any edit that changes task-card semantics, active-task index semantics, or fresh-agent startup guidance.

This remains manual prose guidance for now. It does not require machine validation in the same pass.

### Proposal B. Tighten where historical Layer C shorthand is allowed

The harness should narrow legacy terminology to explicit compatibility contexts only.

Recommended shape:

- keep `docs/harness/concepts/layer-c-overlays-containers.md` as the primary historical pointer,
- keep brief historical mapping notes where needed in maintainer docs,
- remove or tighten broader checklist/reference mentions that can make `container` / `overlay` feel like live vocabulary,
- and use canonical Layer C terms everywhere else, including maintainer validation checklists.

The goal is not to erase history. The goal is to make the allowed location of historical terms much more predictable.

### Proposal C. Add a lightweight live-card normalization audit for Layer A values

The harness should treat canonical Layer A starter values as a maintained normalization target, not just authoring advice.

Recommended shape:

- add a short maintainer rule that live task cards should be repaired to canonical values when touched,
- add one small checklist item for examples and templates that use `intent`, `knowledge_locality`, and `dependency_complexity`,
- and explicitly route any future registry or schema work to mirror the live prose guidance rather than redefining it.

This keeps the normalization light and author-friendly while reducing silent drift.

### Proposal D. Add fresh-agent startup discovery to the maintainer regression checklist

The harness should treat startup discovery as a stability contract, not just a one-time docs fix.

Recommended shape:

- add "fresh agent with no preselected task" to maintainer review scenarios,
- require that scenario to route through `README.md` -> `AGENTS.md` -> `indexes/active-tasks.md` -> authoritative task card -> execution or resume workflow,
- and recheck prompts/workflows whenever those surfaces are edited so they do not regress to assuming the task is already known.

This gives the startup flow a durable maintenance home instead of leaving it as an incidental docs improvement.

## Suggested implementation order

1. Add queue-integrity and startup-discovery checks to maintainer guidance.
2. Tighten the remaining maintainer-scope legacy Layer C wording.
3. Add the lightweight live-card normalization audit rule.
4. Re-run a short terminology and startup-routing review across the touched docs.

This order improves trust first, then reduces vocabulary drift, then hardens authoring consistency.

## Non-goals

This follow-up pass should not:

- redesign Layers A through D,
- introduce a new artifact type,
- implement machine-readable schema or registry enforcement,
- replace the active-task queue with automation,
- or expand the harness into a heavier workflow system.

The point is to harden the already-aligned operating model, not replace it.

## Expected outcome

After this follow-up work, the harness should be harder to regress accidentally:

- the executable-task queue remains trustworthy,
- historical Layer C terms stay confined to predictable compatibility contexts,
- live task cards and examples stay closer to canonical Layer A values,
- and future harness edits preserve the fresh-agent startup path instead of silently assuming a preselected task.
