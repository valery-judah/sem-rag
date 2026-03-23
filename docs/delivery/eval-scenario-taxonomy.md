# Evaluation Scenario Taxonomy for MVP Document-Grounded QA

**Status:** Draft  
**Scope:** MVP / Version 1  
**Last updated:** 2026-03-10  
**Related docs:** `mvp.md`, `eval-vocabulary.md`, `eval-support-semantics.md`  
**Authority note:** This file is the evergreen source of truth for canonical scenario classes and classification rules. For Phase 1 semantic lock, these class definitions are frozen for baseline authoring; later dataset and suite artifacts may apply them but should not rename, split, merge, or redefine them without an explicit semantic-change decision.

---

## 1. Purpose

This document defines the canonical scenario classes used by the MVP evaluation harness.

It governs:

- what each scenario class means;
- how classes should be named;
- how to distinguish similar classes;
- how datasets and suites should apply the taxonomy without redefining it.

---

## 2. Classification rules

- Scenario class names are canonical and should be used consistently across RFCs, datasets, rubrics, reports, and workstreams.
- A scenario class defines the type of information need and the expected evidence pattern, not a specific dataset case.
- Dataset artifacts such as scenario catalogs or case files may apply this taxonomy, but they should not redefine the classes.
- Suites such as smoke, baseline, or release are execution selections built from these classes, not replacements for them.
- All scenario classes remain bounded by MVP scope: text-based PDFs, Markdown, grounded answers, useful citations, and honest abstention.
- For baseline authoring, treat these class definitions as frozen. Add examples or authoring guidance elsewhere rather than changing the canonical class meanings in place.

---

## 3. Canonical scenario classes

### 3.1 Direct factual lookup

Use this class when one passage or one tightly bounded source region should directly support the answer.

Primary pressure:

- passage adequacy;
- top-k precision;
- provenance correctness;
- citation usefulness on narrow support.

### 3.2 Section-scoped explanation

Use this class when the question requires locally coherent reading of one section or one structural neighborhood rather than one isolated sentence.

Primary pressure:

- hierarchy recovery;
- section-path usefulness;
- neighbor expansion;
- context assembly coherence.

Classification note:

Prefer this class over vague labels such as `summarization` when the real pressure is local structural coherence.

### 3.3 One-document synthesis

Use this class when the answer requires combining multiple passages from the same document.

Primary pressure:

- within-document recall;
- evidence-set assembly;
- ordering policy;
- answer scoping.

Preferred alias:

`multi-passage synthesis within one document`

### 3.4 Cross-document synthesis

Use this class when materially supporting evidence is distributed across multiple documents.

Primary pressure:

- corpus-level retrieval;
- document identity discipline;
- citation grouping;
- conflict handling;
- answer qualification when sources differ.

### 3.5 Source navigation

Use this class when the primary user need is locating supporting material, not only receiving answer text.

Primary pressure:

- resolvable provenance;
- anchor usefulness;
- stable linkage from answer to source;
- inspection value.

Preferred alias:

`citation resolution`

### 3.6 Insufficient-evidence case

Use this class when the corpus genuinely does not support the requested claim at the requested scope.

Primary pressure:

- abstention behavior;
- unsupported-claim prevention;
- scope narrowing;
- failure honesty.

Classification note:

Do not use this label for merely hard questions if the case is still `SUPPORTED`.

### 3.7 Degraded-source edge case

Use this class when the source is weaker but still within MVP scope, such as weak sectioning, ambiguous boundaries, malformed tables retained as text, or degraded layout in an otherwise text-based document.

Primary pressure:

- parser robustness;
- representation boundaries;
- provenance stability;
- trust-preserving degradation behavior.

Classification note:

This class stays inside MVP. OCR-heavy scanned documents and table-first reasoning remain out of scope.

---

## 4. Relationship to datasets and suites

- Dataset strategy should ensure baseline coverage across all canonical scenario classes.
- Scenario catalogs may add examples, authoring notes, or suite membership, but they should treat this taxonomy as the authority for the class meanings.
- Release, smoke, and full suites may select different proportions of classes, but they should preserve the class names used here.

---

## 5. Non-goals

This document does not define:

- dataset sizes or suite composition;
- case schema fields;
- scoring policy;
- release thresholds;
- implementation details of runners or judges.
