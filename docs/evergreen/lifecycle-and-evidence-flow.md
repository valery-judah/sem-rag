# Lifecycle And Evidence Flow

**Status:** Draft  
**Scope:** MVP / Version 1  
**Last updated:** 2026-03-23  
**Related docs:** `docs/evergreen/mvp.md`, `docs/evergreen/retrieval-hierarchy.md`, `docs/evergreen/architecture.md`, `docs/delivery/eval-support-semantics.md`, `docs/evergreen/first-tier-failures.md`

## Purpose

This document defines the MVP’s conceptual lifecycles and the evidence flow that connects them.

Its purpose is not just to describe “what happens in order.” Its purpose is to make explicit how source documents become trustworthy answer inputs, and where the system must make control decisions to preserve the MVP trust contract.

This document owns:

- the conceptual evidence-preparation lifecycle;
- the conceptual question-answering lifecycle;
- the handoff between them;
- the control points that protect grounded answering, inspectable provenance, and honest failure behavior.

This document does **not** own:

- product scope or capability boundaries;
- the canonical retrieval hierarchy;
- detailed parser, chunker, or retriever contracts;
- the full failure taxonomy;
- current repo topology or service boundaries.

Authority boundaries are:

- `docs/evergreen/mvp.md` owns product scope, MVP guarantees, and explicit deferrals;
- `docs/evergreen/retrieval-hierarchy.md` owns the canonical `DOCUMENT -> SECTION -> PASSAGE` model;
- `docs/evergreen/architecture.md` owns current implementation truth;
- `docs/delivery/eval-support-semantics.md` owns support-state semantics and answer behavior policy;
- this document owns the conceptual lifecycles and evidence-flow control surface across them.

---

## 1. Why Lifecycle Design Matters

This MVP is not defined by answer fluency alone.

It is defined by whether uploaded source artifacts can be transformed into stable, retrievable, provenance-bearing evidence and then consumed by the query path in a way that keeps answers constrained by what the corpus actually supports.

A lifecycle view is therefore necessary because the MVP contract is end-to-end:

- source identity must survive ingestion;
- structure must survive normalization;
- retrieval units must remain traceable;
- answer behavior must stay inside support;
- provenance must remain inspectable rather than fabricated.

This document makes that end-to-end control flow explicit.

---

## 2. The Two Primary Lifecycles

The MVP has two primary conceptual lifecycles:

1. **Evidence-preparation lifecycle**
2. **Question-answering lifecycle**

The first produces evidence-bearing representations.  
The second consumes those representations to answer, narrow, surface ambiguity, or abstain.

The boundary between them is important: the question path should not have to reconstruct structure or provenance that the document path failed to preserve.

---

## 3. Evidence-Preparation Lifecycle

The conceptual evidence-preparation lifecycle for MVP is:

`Acquire -> Normalize -> Recover Structure -> Produce Passages -> Validate Traceability -> Make Queryable`

### 3.1 Acquire

The system accepts user-uploaded text-based PDF and Markdown files and registers them as part of a bounded corpus.

This stage establishes document identity and source metadata.

### 3.2 Normalize

The system extracts or normalizes source text into a workable internal form.

For MVP, normalization is intentionally lightweight. It is meant to preserve recoverable text structure and provenance, not exact layout reproduction or rich visual understanding.

### 3.3 Recover Structure

The system recovers section/header structure where possible.

This stage is responsible for producing a valid document hierarchy when source structure is present or reasonably inferable.

### 3.4 Produce Passages

The system derives retrieval-addressable passages inside recovered sections.

For the canonical structural model used here, see `docs/evergreen/retrieval-hierarchy.md`.

At this stage, the system should preserve:

- document identity;
- source type;
- section/path linkage when recoverable;
- page or source location when recoverable;
- enough local text context for later inspection.

### 3.5 Validate Traceability

Before a document becomes queryable, the system should verify that its retrieval units remain traceable enough for MVP use.

This is a conceptual readiness gate, not merely an indexing detail.

A representation that cannot point back to its document, section/path, or coarse location should not be treated as fully ready evidence.

### 3.6 Make Queryable

Once evidence-bearing units are structurally usable and traceable, they become part of the active queryable corpus.

This is the endpoint of the MVP document-side lifecycle.

The lifecycle does **not** imply a full publication, version-history, or mutation-management system.

---

## 4. Question-Answering Lifecycle

The conceptual question-answering lifecycle for MVP is:

`Interpret -> Retrieve -> Build Evidence Set -> Decide Support -> Answer or Abstain -> Render Provenance`

This lifecycle is intentionally written as a control sequence, not just a language-model sequence.

### 4.1 Interpret

The system interprets the user’s question relative to MVP scope and the active corpus.

This includes recognizing the difference between:
- a likely supported corpus question,
- a partially supported or ambiguous request,
- and a question that is outside MVP scope.

### 4.2 Retrieve

The system retrieves candidate passages from the active corpus.

In the current model, retrieval is passage-first but section-aware.

### 4.3 Build Evidence Set

The system organizes retrieved material into the evidence actually considered for answering.

This stage may involve selection, grouping, local expansion, or context assembly, but its conceptual purpose is simple: define the support bundle the system is about to reason over.

### 4.4 Decide Support

Before final answer emission, the system should make or approximate four decisions:

1. Is the question in scope for MVP?
2. What is the likely support state of the available evidence?
3. Is a direct answer justified, or should the system narrow, qualify, surface ambiguity, or abstain?
4. Does the available provenance meet the minimum inspectability floor for this question and source type?

This is the key trust-control stage in the lifecycle.

### 4.5 Answer or Abstain

The system should then either:

- produce a direct answer,
- produce a narrowed or qualified answer,
- surface ambiguity or conflict,
- or abstain honestly.

The system should not treat “related evidence exists” as equivalent to “the requested answer is supportable.”

### 4.6 Render Provenance

If the system answers, it should return provenance that remains useful for inspection.

Returned provenance should reflect what the system actually used and should not fabricate stronger precision than the pipeline preserved.

---

## 5. Evidence Flow Across The Boundary

The evidence-preparation lifecycle creates the objects that the question-answering lifecycle depends on.

At a high level:

- uploaded sources become normalized, structured, traceable evidence-bearing units;
- the query path retrieves and assembles those units into a candidate evidence set;
- the answer path decides whether the evidence supports answering;
- answer output includes provenance derived from the same evidence path rather than reconstructed after the fact.

This means evidence must survive the boundary between the two lifecycles with enough integrity to support:

- answerability decisions,
- support-state-aware behavior,
- inspectable source navigation,
- and provenance rendering.

---

## 6. Handoff Contract Between Lifecycles

The document-side lifecycle hands the query-side lifecycle a queryable corpus of retrieval units.

Conceptually, that handoff must preserve at least:

- stable document identity;
- source type;
- section/path linkage when recoverable;
- page or source location when recoverable;
- enough text context to verify what was actually retrieved.

If these properties are not preserved, the query lifecycle is forced to guess, reconstruct, or overclaim.

That leads directly to structural, provenance, and trust failures.

---

## 7. Control Points That Protect The MVP Contract

This document exists to make the trust-critical control points explicit.

### 7.1 Structure-preservation control point

The evidence-preparation lifecycle must preserve enough hierarchy and boundaries that retrieval units are still meaningful and inspectable.

### 7.2 Traceability control point

The system must preserve stable unit-to-source mappings throughout the pipeline.

### 7.3 Support-decision control point

Before final answer emission, the system must decide whether the available evidence justifies a direct answer, a narrowed answer, ambiguity handling, or abstention.

### 7.4 Provenance-sufficiency control point

The system must check whether the provenance it can return is inspectable enough for the question and source type.

### 7.5 Scope-honesty control point

The system must not answer out-of-scope question types as though they were supported by the corpus.

These control points are the conceptual bridge from the MVP contract to the failure model.

---

## 8. How This Connects To The Retrieval Hierarchy

This document does not redefine the retrieval hierarchy.

It assumes the canonical structure from `docs/evergreen/retrieval-hierarchy.md`:

`DOCUMENT -> SECTION -> PASSAGE`

Within that model:

- the evidence-preparation lifecycle is responsible for creating passages that remain linked to their document and section context;
- the question-answering lifecycle is responsible for retrieving and reasoning over those passages without breaking that linkage.

For the current implementation truth — including passage-first retrieval, section-aware provenance, and the use of `Chunk` / `RetrievedCandidate` — see `docs/evergreen/retrieval-hierarchy.md` and implementation-level docs.

---

## 9. Failure Prevention Intent

This lifecycle framing exists partly to prevent the most important trust failures.

If structure and traceability are lost in the document-side lifecycle, the result is not just a “data quality issue.” It creates visible answer failures such as malformed retrieval, weak provenance, or impossible anchors.

If support-state and provenance sufficiency are not treated as explicit query-side decisions, the system is likely to:

- answer too strongly on partial or unsupported evidence,
- fail to surface ambiguity,
- or return provenance that is too weak or incorrect.

In other words, lifecycle design is part of failure prevention, not just documentation.

---

## 10. Observability Hooks

This document does not define a full observability or metrics plan, but the lifecycle should imply a minimum trace surface.

At minimum, the system should make it possible to inspect or log:

- query text;
- retrieved units and scores;
- answer text;
- returned provenance payload;
- answer vs abstain decision;
- source-type slice (`pdf`, `markdown`, `mixed`);
- whether the request likely crossed an unsupported scope boundary.

Without that trace surface, several trust-critical failures are difficult to diagnose reliably.

---

## 11. Deferred Publication And Mutation Lifecycle

A later hardening pass may define a separate publication and mutation lifecycle such as:

`Admit -> Re-ingest/Supersede -> Rebuild Queryable State -> Withdraw from Active Retrieval`

This lifecycle is deferred.

It is not an MVP product commitment, and it should not be read as a promise that the current runtime fully implements version-history, supersession, or withdrawal policy.

It exists here only to record the likely future direction if the product later needs stronger mutation, audit, or active-retrieval controls.

---

## 12. What This Document Does Not Define

This document does not define:

- public APIs or compatibility guarantees;
- current implementation topology or service boundaries;
- support-state definitions in detail;
- the full evaluation taxonomy;
- parser-level or retrieval-level algorithm choices;
- advanced indexing, reranking, or production-hardening plans.

Those belong in adjacent docs.

---

## 13. Summary

The MVP has two primary conceptual lifecycles:

- an **evidence-preparation lifecycle** that turns uploaded sources into traceable, queryable evidence-bearing units;
- a **question-answering lifecycle** that retrieves those units, decides whether they support answering, and then answers or abstains with inspectable provenance.

The key architectural point is that the question path must not invent what the document path failed to preserve.

This is how the lifecycle framing supports the MVP guarantees of structural integrity, traceability, grounded answering, inspectable provenance, and honest failure behavior.

---

## 14. References

- `docs/evergreen/mvp.md`
- `docs/evergreen/retrieval-hierarchy.md`
- `docs/evergreen/architecture.md`
- `docs/delivery/eval-support-semantics.md`
- `docs/evergreen/first-tier-failures.md`