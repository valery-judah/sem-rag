# Evaluation Support Semantics for MVP Document-Grounded QA

**Status:** Draft  
**Scope:** MVP / Version 2  
**Last updated:** 2026-03-23  
**Related docs:** `mvp.md`, `eval-vocabulary.md`, `eval-scenario-taxonomy.md`, `eval-failure-taxonomy.md`  
**Authority note:** This file is the evergreen source of truth for canonical support states, support-state decision procedure, answer behavior by support state, and the minimum inspectable provenance contract. Other evaluation documents should reference this file rather than restating support-state semantics in divergent wording.

---

## 1. Purpose

This document defines the minimum semantic contract that protects the MVP trust promise for document-grounded question answering.

It governs:

- the canonical support states used in evaluation;
- the decision procedure for assigning support state;
- the answer behavior allowed for each support state;
- the minimum provenance floor required for inspectable grounding.

Support state is judged against the **active corpus**, not against external world knowledge, and at the level of the **requested answer shape**, not topical relevance alone.

---

## 2. Scope and relationship to adjacent docs

### 2.1 Scope inheritance

This file inherits MVP scope from `mvp.md`.

For evaluation purposes, the supported corpus remains bounded to:

- user-uploaded **text-based PDFs**;
- user-uploaded **Markdown files**.

Questions that depend on OCR-heavy scans, figure-first interpretation, table-first interpretation, or external-world knowledge outside the active corpus are not upgraded to supported status by evaluator discretion.

### 2.2 Relationship to other evaluation docs

- `eval-vocabulary.md` defines the canonical glossary.
- `eval-scenario-taxonomy.md` defines reusable scenario classes and source-condition slices.
- `eval-failure-taxonomy.md` defines failure labels and severity.

#todo rewrite to first-rear failures. @21_critical_failures

This file sits between those layers. It answers one narrow question:

> What does the corpus actually warrant for the requested answer shape, and what answer behavior is allowed as a result?

### 2.3 What this file does not define

This file does **not** define:

- scenario classes;
- case schema fields;
- failure severity;
- release thresholds;
- implementation details of retrieval or generation.

---

## 3. Core definition

A **support state** is the evaluator's judgment about whether the active corpus warrants the **requested answer shape**.

### 3.1 Active corpus

The **active corpus** is the bounded set of documents the system is allowed to use as evidence for the evaluation run.

### 3.2 Requested answer shape

The **requested answer shape** includes the scope, granularity, and composition implied by the question.

Examples:

- a one-fact lookup;
- a local explanation of one section;
- a synthesis across multiple passages;
- a multi-document answer;
- a navigation request for source location.

A question can be topically related to the corpus and still be unsupported if the corpus does not warrant the answer **as asked**.

### 3.3 Assignment timing

Support state is assigned **before** reviewing the system answer.

It is a property of the corpus-question relation, not a summary of model behavior.

### 3.4 What support state is not

Support state is **not**:

- a confidence score;
- a retrieval-score proxy;
- a fluency judgment;
- a source-quality tag;
- a model self-report about whether it feels uncertain.

---

## 4. Decision procedure

Assign support state in the following order.

### Step 1 — scope check

Ask whether answering the question depends on an MVP-excluded capability.

If yes, assign `UNSUPPORTED_QUESTION_TYPE`.

Typical triggers include:

- external-world completion not present in the active corpus;
- OCR-dependent reading of scanned or image-heavy PDFs;
- questions whose answer depends mainly on tables, figures, charts, diagrams, or pictures;
- answer forms explicitly deferred from MVP, such as exact scholarly citation formatting.

### Step 2 — full-support check

If the question is in scope, ask whether the active corpus contains a sufficient evidence set to justify the answer at the requested scope.

If yes, assign `SUPPORTED`.

### Step 3 — partial-support check

If full support is not present, ask whether the corpus supports only:

- a narrower answer;
- a subset of the request;
- a qualified conclusion;
- an answer to one subpart but not the full composite request.

If yes, assign `PARTIALLY_SUPPORTED`.

### Step 4 — ambiguity/conflict check

If a clean supported answer is still not justified, ask whether the blocker is materially conflicting supported evidence or multiple plausible supported readings that cannot be cleanly collapsed into one answer.

If yes, assign `AMBIGUOUS_OR_CONFLICTING`.

### Step 5 — no-support remainder

If none of the above applies, assign `UNSUPPORTED_IN_CORPUS`.

---

## 5. Canonical support states

### 5.1 Summary table

| Support state | Corpus meaning | Allowed answer behavior | Not allowed |
|---|---|---|---|
| `SUPPORTED` | The corpus contains a sufficient evidence set for the answer at the requested scope. | Direct answer, bounded paraphrase, or synthesis within supported scope, with inspectable provenance. | Unsupported additions, hidden uncertainty, fabricated provenance. |
| `PARTIALLY_SUPPORTED` | The corpus supports only a narrower answer, a subset of the request, or a qualified conclusion. | Answer only the supported portion, narrow scope explicitly, or qualify unsupported parts. | Presenting the full request as fully answered or silently filling gaps from model priors. |
| `UNSUPPORTED_IN_CORPUS` | The corpus does not contain enough evidence to support the requested answer at the requested scope. | Abstain, or explicitly state that the corpus does not provide enough support. | Answering as though support exists or converting weak topical relevance into support. |
| `UNSUPPORTED_QUESTION_TYPE` | The question depends on an MVP-excluded capability or answer form. | State the MVP limitation explicitly and avoid presenting the result as corpus-grounded. | Treating the question as in scope and answering as though the excluded capability were supported. |
| `AMBIGUOUS_OR_CONFLICTING` | The corpus contains materially conflicting supported evidence or multiple plausible supported readings such that one clean answer is not justified. | Surface the ambiguity, qualify by source, or narrow to the uncontested portion if one exists. | Selecting one confident resolution without exposing the conflict or uncertainty. |

### 5.2 State definitions

#### `SUPPORTED`

Use `SUPPORTED` when the active corpus contains a sufficient evidence set to justify the answer **as asked**.

This includes cases where the answer requires:

- one passage;
- one section or local structural neighborhood;
- multiple passages from one document;
- multiple passages across documents;
- navigation to the relevant source location.

The decisive condition is not simplicity. The decisive condition is whether the evidence set is sufficient for the requested answer shape.

#### `PARTIALLY_SUPPORTED`

Use `PARTIALLY_SUPPORTED` when the active corpus supports only a narrower answer, a subset of the request, or a qualified conclusion.

Typical cases include:

- one subquestion is supported but another is not;
- the corpus supports a partial list but not an exhaustive list implied by the wording;
- the corpus supports a qualified conclusion but not a full-strength claim;
- a synthesis is supportable only after narrowing scope.

This state exists to preserve honest usefulness. The system may still provide value, but only if it does not imply completeness.

#### `UNSUPPORTED_IN_CORPUS`

Use `UNSUPPORTED_IN_CORPUS` when the active corpus does not contain a sufficient evidence set for the answer at the requested scope.

The question may still be perfectly valid and in scope for MVP. The issue is simply that the available corpus does not support the requested answer.

Do not use this state merely because the question is hard. Use it when the required evidence is absent or materially insufficient.

#### `UNSUPPORTED_QUESTION_TYPE`

Use `UNSUPPORTED_QUESTION_TYPE` when the question depends on a capability explicitly excluded from MVP.

This is a scope-boundary state, not a retrieval state.

Use it for requests that fundamentally depend on:

- external-world facts outside the active corpus;
- OCR-heavy reading or image-only content;
- table-first, figure-first, or diagram-first reasoning that MVP does not promise;
- excluded output forms that the product does not claim to support.

Do not use this state just because the system missed evidence or the corpus is sparse.

#### `AMBIGUOUS_OR_CONFLICTING`

Use `AMBIGUOUS_OR_CONFLICTING` when the corpus contains materially conflicting supported evidence, or multiple plausible supported readings, such that one clean answer is not justified.

This state should be used when the blocker is **tension in the evidence**, not ordinary incompleteness.

Examples include:

- two documents in the active corpus make different supported claims;
- one source defines a term differently from another;
- the wording in the corpus supports more than one plausible reading and the case does not justify collapsing them into one answer.

Do **not** use this state for simple lack of evidence. Incompleteness alone belongs under `PARTIALLY_SUPPORTED` or `UNSUPPORTED_IN_CORPUS`.

---

## 6. Global answer-policy rules

These rules apply across all support states.

- Do not fill evidential gaps from model priors or external knowledge.
- Do not convert weakly related text into apparent support.
- Do not hide unsupported portions behind fluent or overly complete wording.
- Do not fabricate provenance, anchors, pages, sections, or contributing sources.
- Prefer lower answer coverage over unsupported completion.
- Coarse real support is acceptable for MVP; false precision is not.

---

## 7. Answer behavior by support state

| Support state | Correct behavior |
|---|---|
| `SUPPORTED` | Answer directly and provide inspectable provenance. |
| `PARTIALLY_SUPPORTED` | Answer only the supported portion, narrow the scope explicitly, and qualify the unsupported remainder. |
| `UNSUPPORTED_IN_CORPUS` | Abstain, or explicitly state that the active corpus does not provide enough support. |
| `UNSUPPORTED_QUESTION_TYPE` | State the MVP limitation explicitly and do not present the result as a grounded corpus answer. |
| `AMBIGUOUS_OR_CONFLICTING` | Surface the ambiguity or conflict, qualify by source, or narrow to the uncontested portion if justified. |

### 7.1 Valid abstention modes

For MVP evaluation, the following count as valid honest-failure behavior when appropriate:

- explicit abstention;
- explicit statement that the active corpus does not provide enough support;
- explicit scope narrowing;
- explicit source-qualified answer that surfaces conflict rather than hiding it.

### 7.2 Invalid answer behaviors

The following are invalid regardless of fluency:

- answering unsupported portions as though fully supported;
- omitting known uncertainty that materially changes the answer;
- claiming source support without usable provenance;
- presenting an out-of-scope answer as though it were corpus-grounded.

---

## 8. Boundary rules and disambiguation

### 8.1 `SUPPORTED` vs `PARTIALLY_SUPPORTED`

Use `SUPPORTED` only when the corpus warrants the answer **at the requested scope**.

Use `PARTIALLY_SUPPORTED` when some answer can still be given, but only after narrowing, qualifying, or splitting the request.

The requested answer shape is decisive. A corpus that supports only one part of a compound request does not justify `SUPPORTED` for the whole request.

### 8.2 `PARTIALLY_SUPPORTED` vs `UNSUPPORTED_IN_CORPUS`

Use `PARTIALLY_SUPPORTED` when a narrower, still-useful answer is genuinely supportable.

Use `UNSUPPORTED_IN_CORPUS` when the evidence is too weak to justify even a narrowed substantive answer.

### 8.3 `UNSUPPORTED_IN_CORPUS` vs `AMBIGUOUS_OR_CONFLICTING`

Use `AMBIGUOUS_OR_CONFLICTING` only when the blocker is real supported tension in the evidence.

Use `UNSUPPORTED_IN_CORPUS` when the problem is absence or insufficiency of evidence rather than conflict.

### 8.4 `UNSUPPORTED_QUESTION_TYPE` vs `UNSUPPORTED_IN_CORPUS`

Use `UNSUPPORTED_QUESTION_TYPE` when the question fundamentally depends on an excluded MVP capability.

Use `UNSUPPORTED_IN_CORPUS` when the question is in scope but the active corpus lacks the needed evidence.

### 8.5 Support state vs source-condition tags

Weak structure, degraded extraction, malformed sectioning, noisy PDF conversion, and similar source conditions are **not** support states.

They belong in scenario or source-condition tagging.

Those conditions may pressure provenance, retrieval, or answer quality, and they may contribute to failures such as ingestion or structure defects, but they do not replace the canonical support-state judgment.

---

## 9. Minimum provenance contract

Support state and provenance are related but distinct. A question can be `SUPPORTED` while still failing the provenance floor, and a response with citations can still be unsupported if the citations do not actually justify the answer.

### 9.1 Canonical provenance expectations

The minimum provenance expectation for a case should be one of:

- `document_only`
- `document_and_page`
- `document_and_section`
- `document_page_and_section_if_available`

### 9.2 Source-type defaults for MVP

For MVP, the default provenance floor is:

- **PDF**: `document_and_page` when page-level provenance is recoverable;
- **Markdown**: `document_and_section` when section structure is recoverable;
- **mixed-source answers**: one usable provenance record per materially contributing source;
- **when both page and section are recoverable**: `document_page_and_section_if_available` remains valid.

`document_only` is acceptable only when the case metadata explicitly allows it.

### 9.3 Provenance quality rules

Minimum provenance must:

- identify the correct contributing document;
- identify a usable inspection point at MVP granularity;
- remain materially consistent with the answer actually given.

The provenance contract for MVP does **not** require:

- exact span anchors;
- layout-perfect citations;
- paragraph-level precision in PDFs.

The provenance contract for MVP **does** require inspectability and materially correct source mapping.

---

## 10. Evaluation protocol

Reviewers and harness logic should apply support semantics in the following order.

1. Determine support state from the corpus and case definition.
2. Determine the minimum provenance expectation.
3. Review the final answer against the assigned support state.
4. Review citations and provenance against the provenance floor.
5. Assign failure labels only after the first four steps are clear.

This order is intentional. Support state is not inferred from answer confidence, and failure labels should not replace the prior support-state judgment.

---

## 11. Non-goals

This file does not attempt to:

- encode all source-quality pathologies;
- define the full failure taxonomy;
- specify scoring formulas or pass thresholds;
- prescribe internal retrieval architecture;
- guarantee exhaustive resolution for very large corpora.

---

## 12. Practical summary

The support-state layer should answer one question only:

> What does the active corpus warrant for this requested answer shape?

Everything else—abstention, scope messaging, provenance sufficiency, and failure labeling—should be layered on top of that judgment rather than blended into the definition itself.
