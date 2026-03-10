# Evaluation Vocabulary for MVP Document-Grounded QA

> Archival note: This file is a historical extraction snapshot kept for WS-002 continuity. It is not the live source of truth. Live evaluation semantics now reside in `docs/evergreen/eval-vocabulary.md`, `docs/evergreen/eval-support-semantics.md`, `docs/evergreen/eval-scenario-taxonomy.md`, and `docs/evergreen/eval-failure-taxonomy.md`.

**Status:** Draft  
**Scope:** MVP / Version 1  
**Last updated:** 2026-03-09  
**Derived from:** `mvp.md`, `eval-harness-rfc-sections-1-10.md`, `eval-harness-rfc-sections-11-15.md`  
**Compatibility note:** This file is intended to be compatible with `workflow.md`, but it does not broaden MVP scope.

---

## 1. Purpose

This document extracts and normalizes the **evaluation vocabulary** needed for MVP dataset authoring, rubric design, harness implementation, prototype comparison, and release discussion.

It is an **extractive and reconciling** document. It does not replace the source documents and does not remove content from them. Its role is to give the team one place where evaluation terms, support semantics, citation expectations, and abstention behavior are defined in a consistent way.

---

## 2. Precedence and reconciliation rules

### 2.1 Source-of-truth order

When terms conflict or drift, use the following precedence order:

1. `mvp.md` governs **product scope**, supported inputs, trust guarantees, and explicit deferrals.
2. `eval-harness-rfc-sections-1-10.md` governs **normative evaluation semantics**.
3. `eval-harness-rfc-sections-11-15.md` governs **operationalization** of those semantics.
4. `workflow.md` may generalize internal modeling language, but it may not broaden MVP inputs, provenance guarantees, or evaluation success criteria.

### 2.2 Reconciliation principles

- Evaluation is **contract-first**, not fluency-first.
- Evaluation is **scenario-first**, not metric-first.
- Evaluation is **layered**, not answer-only.
- Evidence support, provenance, citation usefulness, and honest failure behavior are first-class concerns.
- Generic internal terms such as `document`, `anchor`, or `evidence unit` do **not** widen MVP scope beyond text-based PDF and Markdown.

### 2.3 Terminology normalization rules

Use these preferred terms in evaluation documents and discussions:

- Prefer **passage** over generic `chunk` when referring to the evaluable retrieval unit.
- Prefer **anchor** for a recoverable source locator.
- Prefer **citation** for the user-visible mapping from answer to evidence anchors.
- Prefer **support state** over vague labels like `confidence`, `answerability`, or `match quality` when the real issue is evidential sufficiency.
- Prefer **supported answer** / **unsupported answer** over generic `correct` / `incorrect` when support fidelity is the primary question.
- Prefer **abstention** or **scope narrowing** over vague phrases such as `fallback answer` when describing honest failure behavior.

### 2.4 Synonym map

This file treats the following pairs as aligned, with the term on the left preferred for evaluation work:

- **passage** <- chunk, text chunk, embedding chunk
- **anchor** <- source locator, provenance pointer, source location
- **citation** <- source reference, supporting source, provenance link
- **support state** <- evidence sufficiency state, support label
- **supported answer** <- grounded answer, evidence-backed answer
- **unsupported answer** <- unsupported synthesis, overreach, hallucinated grounded answer
- **abstention** <- explicit non-answer, refusal to answer from corpus, supported refusal

---

## 3. Canonical evaluation vocabulary

### 3.1 Corpus

A **corpus** is the bounded collection of source documents the system is allowed to use as evidence for a given evaluation run.

Normative implications:

- corpus boundaries must be explicit;
- no evidence may be attributed outside the active corpus;
- the evaluator must judge support only against the active corpus, not against world knowledge.

### 3.2 Document

A **document** is a source artifact with stable identity inside the corpus.

For MVP, supported document types are limited to:

- text-based PDF;
- Markdown.

A document may carry metadata such as title, source type, source reference, and upload timestamp, but stable document identity is the primary evaluation concern.

### 3.3 Section

A **section** is a structurally meaningful subdivision within a document, usually tied to a heading or recoverable hierarchical boundary.

A section is:

- a semantic container;
- useful for provenance and context assembly;
- not automatically the default retrieval unit.

### 3.4 Passage

A **passage** is the default retrievable text unit used to discover evidence.

A passage should:

- preserve local coherence;
- remain traceable to document identity and anchor information;
- function as an evidence-bearing unit, not merely a storage or embedding artifact.

### 3.5 Anchor

An **anchor** is a recoverable reference to a source location.

For MVP, anchors may be coarse. Acceptable anchor forms include:

- page number;
- section path;
- inferred heading;
- a source-local locator usable for inspection.

Exact span anchoring is not required for MVP.

### 3.6 Evidence unit

An **evidence unit** is any source-linked representation that can legitimately support a user-visible claim.

For MVP, an evidence unit is primarily:

- a passage;
- optionally supplemented by section metadata or nearby context.

### 3.7 Evidence set

An **evidence set** is one or more evidence units jointly sufficient to support a claim, answer fragment, or answer as a whole.

This term is required because many evaluation cases cannot be reduced to a one-claim / one-passage mapping.

### 3.8 Context window

A **context window** is the ordered, budget-constrained set of retrieved evidence units and supporting context presented to generation.

The context window is an assembled artifact. It is therefore distinct from raw retrieval output and must be evaluated separately.

### 3.9 Claim

A **claim** is a user-visible assertion in the generated answer.

For evaluation purposes, a claim may be:

- directly supported;
- partially suggested;
- unsupported.

### 3.10 Citation

A **citation** is a mapping from an answer, answer fragment, or answer-support bundle to one or more evidence anchors.

A citation is valid for MVP only if it is:

- source-linked;
- resolvable at useful granularity;
- materially consistent with the evidence it is meant to expose.

### 3.11 Useful citation

A **useful citation** is a citation a reviewer or user can realistically follow to inspect the relevant support without excessive searching.

Usefulness is judged pragmatically for MVP, not by scholarly citation rules.

### 3.12 Support state

A **support state** is the evaluator’s judgment about whether the available corpus evidence warrants the requested claim or answer shape.

The three canonical support states are:

- **sufficient support**;
- **partial support**;
- **insufficient support**.

These must not be collapsed into a single right/wrong label.

### 3.13 Supported answer

A **supported answer** is an answer whose material claims remain within the bounds of sufficient support or explicitly qualified partial support and whose citations resolve to the relevant evidence.

### 3.14 Unsupported answer

An **unsupported answer** is an answer that states or strongly implies claims not justified by the available corpus evidence, especially when it presents those claims with false confidence or fabricated provenance.

### 3.15 Abstention

**Abstention** is a valid answer mode in which the system declines to answer fully, narrows answer scope, or states that the current corpus does not support the requested claim.

Abstention is not failure when the support state warrants it.

### 3.16 Scenario

A **scenario** is a reusable behavioral template from which one or more evaluation cases are derived.

A scenario defines:

- the type of information need;
- the expected evidence pattern;
- expected trust behavior under success or failure;
- the system layers under pressure.

### 3.17 Eval case

An **eval case** is the atomic unit of harness execution.

At minimum, a case should define:

- the question or prompt;
- the corpus scope;
- the expected support state;
- evidence requirements;
- citation requirements;
- expected answer or failure behavior;
- relevant failure tags.

### 3.18 Gold evidence set

A **gold evidence set** is the evidence set considered sufficient, or one acceptable sufficient set, for a specific evaluation case.

The schema should allow:

- one canonical gold set;
- or a small set of acceptable alternatives.

### 3.19 Retrieved evidence set

A **retrieved evidence set** is the evidence returned by the system prior to context assembly.

It exists to diagnose retrieval success, incompleteness, ranking errors, retrieval noise, and evidence fragmentation.

### 3.20 Final context artifact

A **final context artifact** is the ordered evidence bundle actually provided to generation.

This artifact exists because raw retrieval may be adequate while context assembly still drops or distorts support.

### 3.21 Answer artifact

An **answer artifact** is the user-visible answer output under evaluation.

It may include:

- answer text;
- support metadata if emitted;
- abstention indicators;
- confidence or scope qualifiers if present.

### 3.22 Citation artifact

A **citation artifact** is the set of source references exposed with the answer.

It is evaluated for:

- resolvability;
- relevance;
- support consistency;
- usefulness for inspection.

### 3.23 Judgment result

A **judgment result** is the structured output of one evaluator over one case.

It should capture, conceptually:

- evaluator name;
- pass/fail or score result;
- structured reasons;
- extracted support state where relevant;
- failure classification if applicable.

### 3.24 Failure classification

A **failure classification** names the dominant failure type observed for a case or subsystem stage.

Use the failure taxonomy rather than ad hoc free-text wherever possible.

### 3.25 Scorecard

A **scorecard** is the aggregate summary of harness outputs over a suite or run.

A scorecard must preserve dimensional separation rather than collapsing everything into one opaque metric.

### 3.26 Reproducibility envelope

A **reproducibility envelope** is the minimum run metadata needed for trustworthy comparison and regression analysis.

It includes, conceptually:

- corpus version or fixture reference;
- system-under-evaluation configuration reference;
- evaluator configuration reference;
- run identifier;
- deterministic or semi-deterministic execution notes where relevant.

---

## 4. Layer vocabulary

Evaluation must preserve separate language for the main quality layers.

### 4.1 Representation quality

Whether source parsing and normalization preserve enough structure, identity, and provenance to support later grounding.

### 4.2 Retrieval quality

Whether the system discovers evidence sufficient for the question and scenario.

### 4.3 Context quality

Whether retrieved evidence is assembled into a coherent, support-preserving context.

### 4.4 Answer quality

Whether the answer stays within the bounds of available evidence and remains materially correct relative to the corpus.

### 4.5 Failure quality

Whether the system fails honestly and usefully when support is weak or missing.

### 4.6 Citation quality

Whether source references are resolvable, relevant, materially consistent, and useful for inspection.

---

## 5. Scenario vocabulary

The baseline scenario classes should use the following names consistently:

- **direct factual lookup**
- **section-scoped explanation**
- **one-document synthesis** / **multi-passage synthesis within one document**
- **cross-document synthesis**
- **source navigation** / **citation resolution**
- **insufficient-evidence case**
- **degraded-source edge case**

Preferred normalization rules:

- Use **section-scoped explanation** rather than vague labels such as `summarization` when the key pressure is local structural coherence.
- Use **source navigation** when the user’s primary need is locating supporting material.
- Use **insufficient-evidence case** only when the corpus genuinely cannot support the requested claim at the requested scope.

---

## 6. Support-state criteria

This section makes the three support states operational.

### 6.1 Sufficient support

Use **sufficient support** when the available evidence set justifies the requested claim or answer shape at MVP trust standards.

Criteria:

- the corpus contains an evidence set that materially supports the answer;
- the evidence covers the material claims required by the question at the scope the answer presents;
- no essential step depends on unsupported external inference;
- the answer can remain within the supported scope without speculative gap-filling;
- the cited anchors can take a reviewer to the relevant support.

Implications for answer behavior:

- a direct answer is allowed;
- paraphrase is allowed;
- synthesis is allowed if all material subclaims remain supported;
- uncertainty language is optional, not required.

### 6.2 Partial support

Use **partial support** when the corpus supports only a narrower, incomplete, qualified, or lower-confidence answer.

Criteria:

- some relevant evidence exists, but it does not justify the full requested answer;
- the corpus supports a subset of the requested claim, a narrower scope, or an answer direction rather than a complete conclusion;
- at least one material gap remains if the answer were stated fully;
- a fully confident answer would overstate what the evidence warrants.

Implications for answer behavior:

- the system should qualify the answer;
- the system may narrow scope explicitly;
- the system may answer only the supported subpart;
- the system must not silently fill unsupported gaps from model priors.

### 6.3 Insufficient support

Use **insufficient support** when the corpus does not provide adequate evidence for the requested claim at the requested scope.

Criteria:

- no evidence set in the corpus justifies the claim;
- retrieved text is absent, only weakly related, or too incomplete to support the conclusion;
- the question requires evidence types or external knowledge outside MVP scope;
- sources are too contradictory or too fragmentary to justify a claim without speculative reconciliation.

Implications for answer behavior:

- full abstention is valid and usually preferred;
- a narrower answer is allowed only if it is clearly labeled as narrower than the original request;
- the system must not convert weak relevance into apparent support.

### 6.4 Support-state labeling rules

- Support state is about **evidence sufficiency**, not about answer polish.
- Support state is judged against the **active corpus**, not against what a human happens to know.
- Support state should be evaluated at the level of the **requested answer shape**, not only at the level of topical relevance.
- A plausible answer may still be **unsupported**.
- A non-answer may still be the **correct** behavior for an insufficient-support case.

### 6.5 Additional derived terms

The harness may also use these derived terms in scorecards and rubrics:

- **correct abstention**: the system abstains when support is genuinely insufficient;
- **unnecessary abstention**: the system abstains even though sufficient support exists in the corpus;
- **overreach**: the system answers beyond the actual support state;
- **scope narrowing**: the system explicitly reduces the answer scope to match partial support.

Note: `correct abstention` may still coexist with an upstream retrieval failure if the corpus did contain support but the system failed to retrieve it. In that case, abstention is preferable to fabrication at the answer layer, but the end-to-end case may still fail overall.

---

## 7. Citation expectations by source type

This section resolves one of the main Phase 1 semantic gaps: what counts as an acceptable citation for MVP depends partly on source type.

### 7.1 Common citation requirements

All citations, regardless of source type, must satisfy these baseline conditions:

- they identify the correct contributing document;
- they resolve to a useful inspection point at MVP granularity;
- they are materially consistent with the claim or answer fragment they support;
- they do not imply stronger support than the evidence provides;
- they do not fabricate anchors, sections, or provenance.

### 7.2 PDF citation expectations

For **PDF** sources, citation usefulness is judged against coarse but inspectable provenance.

Minimum acceptable shape:

- document identity or display title;
- page number;
- optionally inferred heading or section path when available.

Preferred shape:

- document identity;
- page number;
- inferred heading, section path, chapter, or other localizing label when recoverable.

Evaluation rule:

A PDF citation is useful if a reviewer can land on the correct page and find the relevant support without excessive searching.

Explicit MVP limits:

- exact paragraph-span citations are **not required**;
- layout-perfect anchors are **not required**;
- coarse provenance is acceptable if it remains inspectable and materially correct.

### 7.3 Markdown citation expectations

For **Markdown** sources, citation usefulness is judged against heading structure and source-local navigation.

Minimum acceptable shape:

- document identity or display title;
- heading, section path, or other stable local locator.

Preferred shape:

- document identity;
- heading path or nested section path;
- optionally a passage identifier or source-local anchor if the product exposes one.

Evaluation rule:

A Markdown citation is useful if a reviewer can navigate to the right file and locate the supported material through stable document structure without excessive searching.

### 7.4 Cross-document synthesis citation expectations

When an answer synthesizes across multiple documents:

- the citation bundle should expose all materially contributing documents;
- the answer should not collapse multi-source support into a single-source citation unless only one source actually supports the material claim;
- when sources differ, the answer should qualify the synthesis rather than present false consensus.

### 7.5 Source-navigation scenario expectations

In **source navigation** cases, citation quality is not secondary. It is part of the primary product behavior.

For these cases, citations should be judged more strictly on:

- localizability;
- inspection value;
- whether the cited location is where the topic is actually discussed.

### 7.6 Citation anti-patterns

The following should be treated as evaluation failures:

- citation to the wrong document;
- citation to the correct document but wrong region;
- citation so broad that inspection becomes impractical;
- citation bundle that omits a necessary contributing source;
- fabricated heading, section, or page reference;
- citation that makes an unsupported claim appear grounded.

---

## 8. Honest abstention for MVP

This section defines what the RFC means by **honest abstention**.

### 8.1 Definition

**Honest abstention** is answer behavior that accurately reflects the limits of corpus support instead of manufacturing a stronger answer than the evidence warrants.

For MVP, honest abstention includes three acceptable modes:

1. **full abstention** — the system states that the corpus does not provide enough support for the requested claim;
2. **scoped abstention** — the system declines the full request but answers a narrower supported subpart;
3. **qualified uncertainty** — the system gives a partial answer while explicitly labeling the evidential limitation.

### 8.2 When honest abstention is required

Honest abstention is required when:

- the support state is insufficient;
- the available evidence is only weakly related or fragmentary;
- the requested scope exceeds what the corpus supports;
- the answer would otherwise rely on unsupported synthesis or external knowledge;
- sources conflict or are incomplete such that a confident answer would overclaim.

### 8.3 What honest abstention should say

An honest abstention should make the boundary visible.

It should communicate one or more of the following:

- that the uploaded corpus does not provide enough support;
- that only a narrower or partial answer is supported;
- what part is supported versus unsupported;
- where the nearest relevant evidence is, if any exists.

A compliant abstention does **not** need a specific fixed phrase, but it must be explicit enough that a user would not mistake it for a supported answer.

### 8.4 What honest abstention must not do

Honest abstention must not:

- give a confident answer after admitting support is weak;
- cite weakly related material as if it were decisive support;
- hide the unsupported portion behind vague language;
- fabricate provenance;
- imply exhaustive absence when the corpus merely lacks enough support to conclude.

### 8.5 Relationship to evaluation outcomes

Honest abstention is a **success mode** when the case genuinely has insufficient support.

However:

- abstention is **not** automatically a full system success if sufficient support existed in the corpus but the system failed to retrieve it;
- in that case, the answer behavior may be safer than fabrication, but the retrieval or end-to-end evaluation may still fail.

### 8.6 Working examples

#### Example A — correct abstention

Question: “Which chapter proves theorem X?”  
Corpus reality: theorem X is never discussed.  
Correct behavior: state that the uploaded documents do not contain enough support and do not invent a chapter citation.

#### Example B — scoped abstention under partial support

Question: “What exact deployment limits does the book prescribe?”  
Corpus reality: the text describes qualitative trade-offs but does not give numeric limits.  
Correct behavior: explain the qualitative guidance and explicitly say the corpus does not provide exact numeric limits.

#### Example C — incorrect non-abstention

Question: “What are the three mandatory prerequisites?”  
Corpus reality: only two are stated; a third is merely implied by unrelated context.  
Incorrect behavior: answer with three prerequisites and cite the unrelated passage as support.

---

## 9. Failure vocabulary

Use the following failure classes consistently in evaluation writeups:

- **representation failure**
- **segmentation failure**
- **retrieval failure**
- **context assembly failure**
- **answering failure**
- **citation failure**
- **failure-quality failure**

Preferred interpretation:

- Use **citation failure** when provenance exists but is not resolvable, useful, or materially consistent.
- Use **failure-quality failure** when the system behaves untrustworthily under weak support, especially through unsupported confidence.
- Use **answering failure** for overreach, incorrect synthesis, or answering when abstention was required.

---

## 10. Terms that should not be used loosely

The following terms should be treated as loaded and should not be used without the corresponding evaluation meaning:

- **grounded** — only when the answer is materially supported by corpus evidence;
- **supported** — only when support state and citation behavior justify the label;
- **citation** — not merely a document mention, but an inspectable evidence mapping;
- **confidence** — not a substitute for support state;
- **hallucination** — avoid as a catch-all when a more precise label such as unsupported answer, fabricated provenance, or retrieval failure is available;
- **chunk** — avoid as the main evaluative term unless the discussion is implementation-specific.

---

## 11. Minimal artifact implications

This vocabulary file implies the following adjacent evergreen artifacts remain separately useful:

- `eval-support-semantics.md` if the team later wants a more rubric-oriented expansion of Section 6;
- `eval-failure-taxonomy.md` if failure classes need fuller examples and release severity;
- `annotation-guide.md` for dataset authoring rules that operationalize these terms in case templates and reviewer instructions.

For now, this document is sufficient as the extracted Phase 1 vocabulary baseline.
