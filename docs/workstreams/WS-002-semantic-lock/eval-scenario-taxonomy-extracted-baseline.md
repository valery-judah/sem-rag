# Evaluation Scenario Taxonomy for MVP Document-Grounded QA

> Archival note: This file is a historical extraction snapshot kept for WS-002 continuity. It is not the live source of truth. Live scenario semantics now reside in `docs/delivery/eval-scenario-taxonomy.md`, with related live authority in `docs/delivery/eval-vocabulary.md` and `docs/delivery/eval-support-semantics.md`.

**Status:** Draft  
**Scope:** MVP / Version 1  
**Last updated:** 2026-03-09  
**Derived from:** `mvp.md`, `eval-harness-rfc-sections-1-10.md`, `eval-harness-rfc-sections-11-15.md`  
**Related artifacts:** `eval-vocabulary-extracted-baseline.md`

---

## 1. Purpose

This document extracts and normalizes the **evaluation scenario taxonomy** for the MVP document-grounded QA system.

Its job is to give the team a stable classification model for:

- authoring evaluation cases;
- organizing suites;
- reasoning about coverage;
- assigning judgment methods;
- interpreting regressions by scenario class rather than by one undifferentiated quality score.

This file is extractive and reconciling. It does not replace the MVP or the RFC. It defines how scenario classes should be named, distinguished, tagged, and used in baseline authoring.

---

## 2. Precedence and scope boundaries

### 2.1 Source-of-truth order

When there is drift, use this precedence order:

1. `mvp.md` governs product scope, supported inputs, trust guarantees, and explicit exclusions.
2. `eval-harness-rfc-sections-1-10.md` governs normative evaluation semantics and the canonical scenario model.
3. `eval-harness-rfc-sections-11-15.md` governs dataset strategy, case distribution, and phased operationalization.
4. `workflow.md` may guide delivery, but it may not broaden MVP scenario scope.

### 2.2 MVP scope boundary for scenario authoring

All scenario classes in this taxonomy remain bounded by MVP constraints:

- supported sources are text-based PDF and Markdown;
- answers must be grounded in the uploaded corpus;
- source inspection and provenance remain first-class;
- honest abstention is a success mode when support is inadequate.

The taxonomy does **not** include first-class scenario families for:

- OCR-heavy scanned PDFs;
- figure-first or image-first reasoning;
- table-centric reasoning as a primary task shape;
- public-web or external-world lookup;
- exhaustive compare-and-contrast across many viewpoints;
- very-large-corpus scale behavior.

---

## 3. Why scenario taxonomy exists

The harness is scenario-first, not metric-first. A scenario is the behavioral unit that pressures the system end to end across:

- representation;
- segmentation;
- retrieval;
- context assembly;
- answer generation;
- citation and inspection behavior;
- abstention and trust behavior.

A flat list of questions is not enough. The taxonomy exists so the team can distinguish whether a regression happened in:

- narrow factual retrieval;
- local section reading;
- multi-passage evidence assembly;
- multi-document grounding;
- provenance and navigation;
- insufficient-evidence handling;
- robustness to degraded but in-scope sources.

---

## 4. Taxonomy design rules

### 4.1 Primary classification rule

Classify a case by the **dominant evidence pattern and trust behavior under evaluation**, not by superficial wording.

Examples:

- A question phrased as “Explain X” may still be a **direct factual lookup** if one bounded passage fully supports it.
- A question phrased as “What is X?” may still be **one-document synthesis** if the answer requires multiple non-adjacent passages from the same document.
- A question phrased as “Where is X discussed?” is usually **source navigation**, even if the answer contains some factual text.
- A question whose key expectation is “say that the corpus does not support this” is **insufficient-evidence**, even if the wording resembles a normal factual question.

### 4.2 One primary class per case

Every eval case must have exactly one `scenario_class`.

This prevents ambiguous score aggregation and makes regression summaries interpretable.

### 4.3 Secondary tags are allowed

A case may also carry secondary tags for orthogonal pressures, such as:

- `pdf`
- `markdown`
- `mixed_format`
- `single_doc`
- `multi_doc`
- `weak_structure`
- `citation_sensitive`
- `requires_scope_narrowing`
- `partial_support_expected`
- `conflicting_sources`
- `local_context_required`

Secondary tags do not replace the primary class.

### 4.4 Scenario class is not suite membership

Scenario classes are conceptual categories. Suites are execution selections such as:

- smoke;
- baseline full;
- release;
- exploratory;
- beta-derived candidate set.

A release suite should contain at least one representative case from every required scenario class, but suite membership is not itself taxonomy.

---

## 5. Top-level scenario taxonomy

The MVP evaluation taxonomy contains seven top-level scenario classes.

1. **Direct factual lookup**
2. **Section-scoped explanation**
3. **One-document synthesis**
4. **Cross-document synthesis**
5. **Source navigation**
6. **Insufficient-evidence**
7. **Degraded-source edge case**

These are the frozen baseline authoring classes for Phase 1 semantic lock and Phase 2 dataset construction.

---

## 6. Canonical scenario classes

### 6.1 Direct factual lookup

#### Definition
A question where one passage, or a very small tightly bounded set of passages, directly supports the answer.

#### Dominant evidence pattern

- single-passage support, or
- one very local support region.

#### Primary trust question
Can the system retrieve the right bounded evidence and answer without adding unsupported material?

#### Primary layers under pressure

- retrieval precision;
- passage adequacy;
- document identity;
- provenance correctness;
- citation usefulness on narrow support.

#### Typical question forms

- “What is X?”
- “How does this book define Y?”
- “What are the requirements for Z?”

#### Typical answer behavior

- concise answer;
- minimal synthesis;
- citation to the supporting passage or local anchor.

#### Typical failure signatures

- wrong passage selected;
- correct document but wrong local anchor;
- answer padded with unsupported extra detail;
- citation points nearby but not to the real support.

#### Distinguish from nearby classes

Use **direct factual lookup** rather than:

- **section-scoped explanation** when a whole section does not need to be read coherently;
- **one-document synthesis** when multiple non-adjacent passages are not required;
- **source navigation** when the main task is answering, not locating.

---

### 6.2 Section-scoped explanation

#### Definition
A question where the answer requires coherent reading of one section or a tight local neighborhood rather than a single isolated sentence.

#### Dominant evidence pattern

- support concentrated within one section;
- local neighboring passages matter for coherence.

#### Primary trust question
Can the system preserve local structure and remain grounded while explaining material that lives in a section-sized region?

#### Primary layers under pressure

- hierarchy recovery;
- section-path usefulness;
- neighborhood expansion;
- context assembly coherence;
- coarse PDF provenance sufficiency.

#### Typical question forms

- “Explain the retry strategy described in these notes.”
- “Summarize the chapter’s explanation of backpropagation.”

#### Typical answer behavior

- locally coherent explanation;
- answer remains scoped to the section rather than drifting corpus-wide;
- citation resolves to section path, heading, page, or equivalent local anchor.

#### Typical failure signatures

- over-expansion into unrelated sections;
- under-contextualized answer built from one sentence fragment;
- broken section boundaries after parsing;
- answer is fluent but loses the section’s actual meaning.

#### Distinguish from nearby classes

Use **section-scoped explanation** rather than:

- **direct factual lookup** when one passage alone is inadequate;
- **one-document synthesis** when support stays within one local region rather than combining distant evidence;
- **cross-document synthesis** when multiple documents are not materially required.

---

### 6.3 One-document synthesis

#### Definition
A question requiring synthesis of multiple passages from the same document, usually across non-adjacent regions.

#### Dominant evidence pattern

- multi-passage support;
- one document is necessary and sufficient;
- evidence may be distributed across chapters, sections, or repeated mentions.

#### Primary trust question
Can the system assemble enough support from one document without fragmenting or overstating what that source actually says?

#### Primary layers under pressure

- within-document recall;
- passage segmentation quality;
- evidence aggregation;
- ordering policy in final context;
- answer scoping to one source.

#### Typical question forms

- “Summarize the author’s guidance on caching across this chapter and appendix.”
- “What constraints does this manual place on retries, backoff, and timeouts?”

#### Typical answer behavior

- synthesized answer spanning multiple passages;
- clear source identity;
- citations that expose the distributed support pattern.

#### Typical failure signatures

- only one fragment retrieved, producing an incomplete answer;
- evidence retrieved but omitted during context assembly;
- answer mixes supported and unsupported connective claims;
- citation set under-represents the passages actually needed.

#### Distinguish from nearby classes

Use **one-document synthesis** rather than:

- **section-scoped explanation** when support is not local to one section;
- **cross-document synthesis** when multiple documents are not required.

---

### 6.4 Cross-document synthesis

#### Definition
A question requiring evidence from more than one document.

#### Dominant evidence pattern

- multi-document support;
- answer may require combination, comparison, qualification, or scope control across sources.

#### Primary trust question
Can the system remain grounded while retrieving, assembling, and citing support distributed across documents?

#### Primary layers under pressure

- corpus-level retrieval;
- document identity discipline;
- multi-document context assembly;
- citation grouping;
- answer qualification when sources differ or only partially overlap.

#### Typical question forms

- “What do these documents say about vector databases?”
- “Synthesize the guidance on caching from Book A and my notes.”

#### Typical answer behavior

- synthesis explicitly tied to more than one document;
- source distinctions preserved rather than blurred;
- uncertainty or narrowing when sources differ or coverage is uneven.

#### Typical failure signatures

- one relevant document omitted;
- answer attributes one document’s claim to the whole corpus;
- citations collapse multiple sources into one vague reference;
- answer implies exhaustive reconciliation when the corpus only partially supports it.

#### Distinguish from nearby classes

Use **cross-document synthesis** rather than:

- **one-document synthesis** when more than one document is genuinely required;
- **source navigation** when the user mainly wants locating, not synthesis.

---

### 6.5 Source navigation

#### Definition
A question where the primary user need is to locate, inspect, or verify where a topic, claim, or concept appears in the corpus.

#### Dominant evidence pattern

- provenance-first;
- answer quality depends materially on citation usability and anchor resolution.

#### Primary trust question
Can the system return source references that a user can actually follow to inspect the relevant support?

#### Primary layers under pressure

- provenance preservation;
- anchor resolution;
- document and section identity;
- citation usefulness;
- stable linkage from answer to source.

#### Typical question forms

- “Where is tokenization discussed?”
- “Which book or section covers distributed transactions?”
- “Show the passages relevant to this question.”

#### Typical answer behavior

- source-forward response;
- locations and anchors are as important as prose;
- citations may be the main product rather than a short narrative answer.

#### Typical failure signatures

- correct answer with unusable citation;
- citation resolves only to document level when section/page was available and needed;
- answer names a topic but does not provide inspectable source location;
- provenance is fabricated, unstable, or misleading.

#### Distinguish from nearby classes

Use **source navigation** rather than:

- **direct factual lookup** when locating support is the primary job;
- **cross-document synthesis** when the user does not primarily want a synthesized claim.

---

### 6.6 Insufficient-evidence

#### Definition
A question where the active corpus does not adequately support the requested answer shape.

#### Dominant evidence pattern

- support is absent, weak, incomplete, or only partially suggestive;
- the correct behavior is abstention, scope narrowing, or explicit uncertainty.

#### Primary trust question
Can the system avoid unsupported synthesis and fail honestly when the corpus does not warrant a full answer?

#### Primary layers under pressure

- support-state judgment;
- abstention behavior;
- unsupported-claim prevention;
- scope narrowing;
- answer honesty.

#### Typical question forms

- corpus-external factual request;
- question whose answer would require evidence not present in uploaded documents;
- overly broad synthesis request not supportable by the current corpus.

#### Typical answer behavior

- explicit statement that support is insufficient or partial;
- narrowed answer if a smaller claim is supported;
- citations only to what is actually supported, not to invented backing.

#### Typical failure signatures

- confident answer despite insufficient evidence;
- fake or irrelevant citations;
- weak evidence inflated into full support;
- unnecessary certainty where only partial support exists.

#### Distinguish from nearby classes

Use **insufficient-evidence** rather than any positive-support class when the test is fundamentally about honest non-answer behavior.

---

### 6.7 Degraded-source edge case

#### Definition
A question against a degraded but still in-scope source, where source quality is weaker than normal yet the input remains nominally within MVP boundaries.

Examples of degraded but still in-scope conditions:

- weak or noisy heading recovery;
- ambiguous section boundaries;
- malformed tables retained as plain text;
- broken layout in an otherwise text-based PDF;
- Markdown converted from PDF with reduced structure fidelity.

#### Dominant evidence pattern

- source-quality stress case;
- evaluation focus is robustness and trust-preserving degradation, not ideal-path performance.

#### Primary trust question
Can the system degrade locally and honestly when source structure is weak, without fabricating confidence or provenance?

#### Primary layers under pressure

- parser robustness;
- representation quality;
- anchor stability under weak structure;
- failure containment;
- trust-preserving degradation behavior.

#### Typical answer behavior

- answer stays within what recoverable structure supports;
- citations may be coarser but still useful enough for inspection;
- uncertainty increases when structure quality is low.

#### Typical failure signatures

- loss of document identity or section path;
- unstable or misleading anchors;
- answer overclaims because local structure was misread;
- degraded source causes silent provenance collapse.

#### Distinguish from nearby classes

Use **degraded-source edge case** when degraded structure is itself part of the test pressure. A case does not become this class merely because it happens to use a PDF.

---

## 7. Orthogonal classification axes

The top-level class is mandatory, but useful case authoring also depends on orthogonal axes. These axes should usually be represented as tags.

### 7.1 Corpus topology axis

Values:

- `single_doc`
- `multi_doc`
- `subset_corpus`
- `full_corpus`

Use this axis to describe how broad the retrieval scope should be.

### 7.2 Source-type axis

Values:

- `pdf`
- `markdown`
- `mixed_format`

This axis matters because citation expectations and provenance quality differ by source type.

### 7.3 Evidence-shape axis

Values:

- `single_passage`
- `local_neighborhood`
- `multi_passage_same_doc`
- `multi_passage_multi_doc`
- `anchor_first`
- `support_absent`
- `support_partial`

This is often the fastest way to determine the right primary class.

### 7.4 Support-state expectation axis

Values:

- `sufficient_support_expected`
- `partial_support_expected`
- `insufficient_support_expected`

Even positive-support classes may contain partial-support cases, but `insufficient_support_expected` usually indicates the primary class should be **insufficient-evidence**.

### 7.5 Provenance pressure axis

Values:

- `citation_sensitive`
- `anchor_sensitive`
- `page_sensitive`
- `section_path_sensitive`
- `document_identity_sensitive`

Use these tags where source inspection quality is central to the case.

### 7.6 Source-quality axis

Values:

- `clean_structure`
- `weak_structure`
- `noisy_pdf_text`
- `converted_markdown`

This helps separate normal-path cases from robustness cases.

### 7.7 Failure-pressure axis

Values:

- `retrieval_precision`
- `retrieval_recall`
- `context_assembly`
- `unsupported_synthesis`
- `citation_resolution`
- `scope_narrowing`
- `abstention`
- `representation_robustness`

These tags help later triage and subsystem ownership.

---

## 8. Decision rules for classifying new cases

Use the following sequence when assigning a primary scenario class.

### 8.1 Step 1 — Check scope validity

Reject or quarantine the case if it depends primarily on:

- OCR;
- figure or image interpretation;
- table-first reasoning;
- public-web knowledge;
- exact scholarly citation format;
- exhaustive many-viewpoint reconciliation.

These are outside MVP scenario taxonomy.

### 8.2 Step 2 — Ask what the case is primarily testing

Choose the dominant question:

- Is it testing narrow retrieval of one bounded support region? -> **Direct factual lookup**
- Is it testing coherent reading of one section/local region? -> **Section-scoped explanation**
- Is it testing synthesis across multiple passages in one document? -> **One-document synthesis**
- Is it testing synthesis across multiple documents? -> **Cross-document synthesis**
- Is it testing inspectable provenance and locating behavior? -> **Source navigation**
- Is it testing honest non-answer behavior because support is inadequate? -> **Insufficient-evidence**
- Is it testing robustness to weak but in-scope source quality? -> **Degraded-source edge case**

### 8.3 Step 3 — Resolve ambiguous cases by dominant evaluation pressure

When more than one class seems plausible, apply these tie-break rules:

1. **Insufficient-evidence wins** if honest failure behavior is the main expectation.
2. **Source navigation wins** if citation usability and locating are the main user job.
3. **Cross-document synthesis wins** over **one-document synthesis** when more than one document is genuinely required.
4. **One-document synthesis wins** over **section-scoped explanation** when support is distributed beyond one local region.
5. **Degraded-source edge case wins** only when degraded structure is a deliberate part of the scenario, not merely an incidental property.
6. Otherwise prefer the class with the smallest adequate support pattern.

### 8.4 Step 4 — Add orthogonal tags

After setting the primary class, attach secondary tags for:

- source type;
- corpus breadth;
- support expectation;
- provenance pressure;
- failure pressure;
- source quality.

---

## 9. Mapping from MVP use cases to scenario taxonomy

### 9.1 Factual lookup

Maps primarily to:

- **Direct factual lookup**

May escalate to:

- **One-document synthesis** if the answer requires multiple passages from one source.

### 9.2 Localized explanation

Maps primarily to:

- **Section-scoped explanation**

May escalate to:

- **One-document synthesis** if support spans distant sections.

### 9.3 Multi-source synthesis

Maps primarily to:

- **Cross-document synthesis**

May downgrade to:

- **Insufficient-evidence** if the corpus does not support the requested synthesis honestly.

### 9.4 Source navigation

Maps directly to:

- **Source navigation**

### 9.5 Honest failure behavior

This is not a separate MVP user-facing use case section, but it is a hard trust requirement and maps directly to:

- **Insufficient-evidence**

### 9.6 Mixed-format robustness

This is not a user intent class; it is an evaluation pressure class and maps directly to:

- **Degraded-source edge case**

---

## 10. Scenario authoring template

Each scenario family should be documented with the following fields.

- `scenario_class`
- `scenario_goal`
- `information_need_shape`
- `dominant_evidence_pattern`
- `expected_support_state`
- `expected_answer_behavior`
- `expected_citation_behavior`
- `primary_layers_under_pressure`
- `dominant_failure_modes`
- `exclusions`
- `recommended_tags`

This template keeps scenario definitions stable while allowing many concrete eval cases to be authored underneath each class.

---

## 11. Recommended tagging schema for eval cases

Every concrete eval case should include at least:

- `case_id`
- `scenario_class`
- `tags`
- `question`
- `corpus_scope`
- `required_documents`
- `expected_support_state`
- `gold_evidence_sets`
- `citation_expectation`
- `expected_answer_behavior`
- `expected_failure_behavior`

### 11.1 Example tags by class

#### Direct factual lookup

Recommended tags:

- `single_passage`
- `retrieval_precision`
- `citation_sensitive`

#### Section-scoped explanation

Recommended tags:

- `local_neighborhood`
- `section_path_sensitive`
- `context_assembly`

#### One-document synthesis

Recommended tags:

- `multi_passage_same_doc`
- `retrieval_recall`
- `context_assembly`

#### Cross-document synthesis

Recommended tags:

- `multi_doc`
- `multi_passage_multi_doc`
- `document_identity_sensitive`

#### Source navigation

Recommended tags:

- `anchor_first`
- `citation_sensitive`
- `anchor_sensitive`

#### Insufficient-evidence

Recommended tags:

- `support_absent` or `support_partial`
- `abstention`
- `scope_narrowing`

#### Degraded-source edge case

Recommended tags:

- `weak_structure`
- `representation_robustness`
- `citation_sensitive`

---

## 12. Baseline dataset coverage target

For the first baseline dataset, the RFC distribution remains the operating target:

- 10 direct factual lookup
- 10 section-scoped explanation
- 8 one-document synthesis
- 8 cross-document synthesis
- 6 source navigation
- 10 insufficient-evidence
- 6 degraded-source edge cases

This distribution should be treated as a starting allocation, not a permanent law. Coverage can evolve later, but the top-level taxonomy should remain stable until there is evidence that a new scenario family is genuinely required.

---

## 13. Relationship to failure taxonomy and judging

Scenario taxonomy and failure taxonomy are not the same.

- **Scenario taxonomy** answers: what kind of user information need and evidence pattern is being tested?
- **Failure taxonomy** answers: what went wrong in representation, retrieval, context assembly, answering, citation, or abstention?

Likewise, scenario taxonomy and judgment mode are not the same.

- A **direct factual lookup** may be judged largely with deterministic checks.
- A **section-scoped explanation** may need rubric-based evaluation.
- A **cross-document synthesis** case may combine deterministic citation checks with rubric-based or model-assisted support judgment.
- An **insufficient-evidence** case may require explicit support-state and abstention judgment.

The taxonomy should therefore drive:

- dataset composition;
- rubric design;
- judge selection;
- reporting breakdowns;
- regression triage.

---

## 14. Exclusions and anti-patterns

Do not introduce new scenario classes merely because:

- wording differs;
- one case uses PDF and another uses Markdown;
- a case belongs to a different suite;
- a failure mode is different.

Do not classify cases by implementation detail such as:

- embedding model used;
- chunk size;
- reranker presence;
- prompt variant.

Those are system variables, not scenario classes.

Do not allow “general QA” or “miscellaneous” as a scenario class. If a case cannot be classified cleanly, either:

- refine the case;
- split it into smaller cases;
- or document why the current taxonomy is insufficient.

---

## 15. Stable decisions from this extraction

The following decisions should be treated as locked for baseline authoring unless a later RFC explicitly changes them:

1. The MVP harness has **seven** top-level scenario classes.
2. Every eval case has **one** primary `scenario_class`.
3. Additional pressures belong in **tags**, not in ad hoc new primary classes.
4. Scenario classification is based on **dominant evidence pattern and trust behavior**, not superficial phrasing.
5. Honest non-answer behavior is represented explicitly through the **insufficient-evidence** class.
6. Weak but still in-scope source quality is represented explicitly through the **degraded-source edge case** class.
7. Suite construction must remain **scenario-driven**.

---

## 16. Recommended artifact path

Recommended path for this document in the eval tree:

`evals/scenarios/scenario-taxonomy.md`

A separate but adjacent artifact may then define the concrete scenario catalog used by the dataset:

`evals/scenarios/scenario-catalog.md`

The taxonomy defines the classes. The catalog enumerates the concrete scenario definitions and case-authoring guidance built on top of those classes.
