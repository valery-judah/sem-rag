# Evaluation Vocabulary for MVP Document-Grounded QA

**Status:** Draft  
**Scope:** MVP / Version 1  
**Last updated:** 2026-03-23  
**Related docs:** `mvp.md`, `docs/evergreen/retrieval-hierarchy.md`, `eval-support-semantics.md`, `eval-scenario-taxonomy.md`, `eval-failure-taxonomy.md`  
**Authority note:** This file is the evergreen glossary for evaluation-specific terms and terminology normalization. Core retrieval hierarchy and shared structural concepts are owned by `docs/evergreen/retrieval-hierarchy.md`. RFCs may explain or operationalize these terms, but they do not override the owning docs.

---

## 1. Purpose

This document defines the canonical vocabulary used by the MVP evaluation harness.

Its role is to keep the team on a stable, system-specific glossary for:

- evaluation-specific nouns;
- terminology normalization rules;
- evaluation layer names;
- loaded terms that should not be used loosely.

Shared structural concepts such as `Document`, `Section`, `Passage`, and the canonical retrieval hierarchy live in `docs/evergreen/retrieval-hierarchy.md`. Support-state criteria, citation expectations, scenario classes, and detailed failure classes live in adjacent evergreen documents.

---

## 2. Authority and relationship rules

### 2.1 Source-of-truth order

When terms conflict or drift, use the following precedence order:

1. `mvp.md` governs product scope, supported inputs, trust guarantees, and explicit deferrals.
2. `docs/evergreen/retrieval-hierarchy.md` governs the canonical retrieval hierarchy and shared structural concepts used across product, architecture, and evaluation.
3. The evergreen evaluation docs govern live evaluation semantics:
   - `eval-vocabulary.md`
   - `eval-support-semantics.md`
4. `eval-harness-rfc-sections-1-10.md` and `eval-harness-rfc-sections-11-15.md` provide rationale, architecture, and operational history.
5. `workflow.md` may generalize internal modeling language, but it may not broaden MVP inputs, provenance guarantees, or evaluation success criteria.

### 2.2 Reconciliation principles

- Evaluation is contract-first, not fluency-first.
- Evaluation is scenario-first, not metric-first.
- Evaluation is layered, not answer-only.
- Evidence support, provenance, citation usefulness, and honest failure behavior are first-class concerns.
- Generic internal terms such as `document`, `anchor`, or `evidence unit` do not widen MVP scope beyond text-based PDF and Markdown.

---

## 3. Terminology normalization rules

Use these preferred terms in evaluation documents and discussions:

- Prefer **passage** over generic `chunk` when referring to the evaluable retrieval unit.
- Prefer **anchor** for a recoverable source locator.
- Prefer **citation** for the user-visible mapping from answer to evidence anchors.
- Prefer **support state** over vague labels like `confidence`, `answerability`, or `match quality` when the real issue is evidential sufficiency.
- Prefer **supported answer** / **unsupported answer** over generic `correct` / `incorrect` when support fidelity is the primary question.
- Prefer **abstention** or **scope narrowing** over vague phrases such as `fallback answer` when describing honest failure behavior.

### 3.1 Synonym map

This file treats the following pairs as aligned, with the term on the left preferred for evaluation work:

- **passage** <- chunk, text chunk, embedding chunk
- **anchor** <- source locator, provenance pointer, source location
- **citation** <- source reference, supporting source, provenance link
- **support state** <- evidence sufficiency state, support label
- **supported answer** <- grounded answer, evidence-backed answer
- **unsupported answer** <- unsupported synthesis, overreach, hallucinated grounded answer
- **abstention** <- explicit non-answer, refusal to answer from corpus, supported refusal

---

## 4. Canonical evaluation vocabulary

### 4.1 Corpus

A **corpus** is the bounded collection of source documents the system is allowed to use as evidence for a given evaluation run.

### 4.2 Document

A **document** uses the canonical structural meaning from `docs/evergreen/retrieval-hierarchy.md`.

### 4.3 Section

A **section** uses the canonical structural meaning from `docs/evergreen/retrieval-hierarchy.md`.

### 4.4 Passage

A **passage** uses the canonical structural meaning from `docs/evergreen/retrieval-hierarchy.md`.

### 4.5 Anchor

An **anchor** is a recoverable reference to a source location. For canonical structural expectations, including coarse MVP provenance, use `docs/evergreen/retrieval-hierarchy.md`.

### 4.6 Evidence unit

An **evidence unit** is any source-linked representation that can legitimately support a user-visible claim. For MVP evaluation, this is usually a passage plus any needed nearby structural context built on the canonical meanings from `docs/evergreen/retrieval-hierarchy.md`.

### 4.7 Evidence set

An **evidence set** is one or more evidence units jointly sufficient to support a claim, answer fragment, or answer as a whole.

### 4.8 Context window

A **context window** is the ordered, budget-constrained set of retrieved evidence units and supporting context presented to generation.

### 4.9 Claim

A **claim** is a user-visible assertion in the generated answer.

### 4.10 Citation

A **citation** is a mapping from an answer, answer fragment, or answer-support bundle to one or more evidence anchors.

### 4.11 Useful citation

A **useful citation** is a citation a reviewer or user can realistically follow to inspect the relevant support without excessive searching.

### 4.12 Support state

A **support state** is the evaluator's judgment about whether the available corpus evidence warrants the requested claim or answer shape.

The canonical support states are:

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `UNSUPPORTED_IN_CORPUS`
- `UNSUPPORTED_QUESTION_TYPE`
- `AMBIGUOUS_OR_CONFLICTING`

Their criteria and answer-policy rules are governed by `eval-support-semantics.md`.

### 4.13 Supported answer

A **supported answer** is an answer whose material claims remain within the bounds of the applicable support state and whose citations resolve to the relevant evidence.

### 4.14 Unsupported answer

An **unsupported answer** is an answer that states or strongly implies claims not justified by the available corpus evidence, especially when it presents those claims with false confidence or fabricated provenance.

### 4.15 Abstention

**Abstention** is a valid answer mode in which the system declines to answer fully, narrows answer scope, or states that the current corpus does not support the requested claim.

The operational rules for abstention are governed by `eval-support-semantics.md`.

### 4.16 Scenario

A **scenario** is a reusable behavioral template from which one or more evaluation cases are derived.

The canonical scenario classes are governed by `eval-scenario-taxonomy.md`.

### 4.17 Eval case

An **eval case** is the atomic unit of harness execution.

### 4.18 Gold evidence set

A **gold evidence set** is the evidence set considered sufficient, or one acceptable sufficient set, for a specific evaluation case.

### 4.19 Retrieved evidence set

A **retrieved evidence set** is the evidence returned by the system prior to context assembly.

### 4.20 Final context artifact

A **final context artifact** is the ordered evidence bundle actually provided to generation.

### 4.21 Answer artifact

An **answer artifact** is the user-visible answer output under evaluation.

### 4.22 Citation artifact

A **citation artifact** is the set of source references exposed with the answer.

### 4.23 Judgment result

A **judgment result** is the structured output of one evaluator over one case.

### 4.24 Failure classification

A **failure classification** names the dominant failure type observed for a case or subsystem stage.

The canonical failure classes are governed by `eval-failure-taxonomy.md`.

### 4.25 Scorecard

A **scorecard** is the aggregate summary of harness outputs over a suite or run.

### 4.26 Reproducibility envelope

A **reproducibility envelope** is the minimum run metadata needed for trustworthy comparison and regression analysis.

---

## 5. Evaluation layer names

Evaluation must preserve separate language for the main quality layers.

### 5.1 Representation quality

Whether source parsing and normalization preserve enough structure, identity, and provenance to support later grounding.

### 5.2 Retrieval quality

Whether the system discovers evidence sufficient to support the question and scenario.

### 5.3 Context quality

Whether retrieved evidence is assembled into a coherent, support-preserving context.

### 5.4 Answer quality

Whether the answer stays within the bounds of available evidence and remains materially correct relative to the corpus.

### 5.5 Failure quality

Whether the system fails honestly and usefully when support is weak or missing.

### 5.6 Citation quality

Whether source references are resolvable, relevant, materially consistent, and useful for inspection.

---

## 6. Terms that should not be used loosely

The following terms should be treated as loaded and should not be used without the corresponding evaluation meaning:

- **grounded**: only when the answer is materially supported by corpus evidence.
- **supported**: only when support state and citation behavior justify the label.
- **citation**: not merely a document mention, but an inspectable evidence mapping.
- **confidence**: not a substitute for support state.
- **hallucination**: avoid as a catch-all when a more precise label such as unsupported answer, fabricated provenance, or retrieval failure is available.
- **chunk**: avoid as the main evaluative term unless the discussion is implementation-specific.

---

## 7. Adjacent evergreen docs

Use these documents for the semantic areas intentionally split out of this glossary:

- `docs/evergreen/retrieval-hierarchy.md`: canonical retrieval hierarchy, shared structural concepts, and concept-to-implementation mapping.
- `eval-support-semantics.md`: canonical support states, answer-policy rules, and minimum provenance contract.
- `eval-scenario-taxonomy.md`: canonical scenario classes and classification rules.
- `eval-failure-taxonomy.md`: failure classes, examples, and release-relevant severity framing.
