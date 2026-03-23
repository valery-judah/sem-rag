# RFC: Evaluation Harness for MVP Document-Grounded QA

**Status:** Draft  
**Scope:** MVP / Version 1  
**Owner:** TBD  
**Last updated:** 2026-03-09  
**Related documents:** `mvp.md`, `workflow.md`  

---

## 1. Purpose and decision statement

This document defines the **normative core** of the evaluation harness for the MVP document-grounded question-answering system.

The evaluation harness exists to verify that the system preserves the MVP trust contract under realistic use, regression pressure, and prototype iteration. It is not a generic benchmark suite, and it is not primarily an LLM answer-scoring framework. It is the mechanism used to determine whether the product behaves as a bounded-corpus, evidence-grounded system rather than as a free-form generative interface.

This RFC fixes the following decisions for MVP:

- evaluation is **contract-first**, not answer-style-first;
- evaluation is **scenario-first**, not metric-first;
- evaluation must be **layered**, not answer-only;
- evaluation must treat **evidence support**, **provenance**, and **honest failure behavior** as first-class concerns;
- mixed **PDF + Markdown** evaluation remains the target system shape;
- Markdown-only evaluation may be used as a fallback diagnostic track, but it does not redefine the MVP target;
- insufficient-evidence behavior is a success mode when correctly handled;
- the harness must support prototype comparison, regression detection, and release gating.

This RFC does **not** fully specify implementation details for datasets, runner modules, CI wiring, or release thresholds. Those belong in later companion documents and operational artifacts. The goal of this document is to lock the semantic and architectural core strongly enough that subsequent implementation can proceed without semantic drift.


### 1.1 Decision statement

For MVP, the evaluation harness is defined as:

> the system used to verify that a bounded-corpus document-grounded QA service preserves evidence-constrained behavior across representation, retrieval, context assembly, answering, citation, and failure handling.

This definition is binding on downstream design and implementation work.

## 2. Product alignment and governing constraints

The evaluation harness is subordinate to the MVP framing document and must not broaden product scope on its own.

### 2.1 Product alignment

The product under evaluation is a **document question-answering and evidence-inspection service** over a bounded user-provided corpus. The service is successful only if a user can reach a supported answer, inspect the evidence behind it, and recognize when the corpus does not support a confident response.

The harness must therefore evaluate the system as a whole request lifecycle:

1. ingest user-provided documents,
2. normalize and structure them into a queryable representation,
3. retrieve relevant evidence for a question,
4. generate an answer constrained by that evidence,
5. expose source references usable for inspection,
6. abstain or narrow scope when the evidence is insufficient.

### 2.2 Supported inputs for evaluation

The harness must evaluate the MVP against the inputs actually supported by the product:

- text-based PDF files;
- Markdown files.

The harness must assume:

- PDFs are primarily text-based and do not require OCR;
- PDF normalization is lightweight and oriented toward recoverable structure and provenance, not exact layout reproduction;
- Markdown may contain headings, sections, lists, paragraphs, and code blocks;
- some Markdown may originate from PDF-to-Markdown conversion.

### 2.3 Mandatory product constraints reflected in the harness

The harness must preserve and test the following constraints:

- the corpus is bounded to user-provided documents only;
- answers must be grounded in retrieved corpus content;
- source references must be usable for inspection;
- retrieval units must remain traceable to source documents and source locations at MVP-appropriate granularity;
- mixed-format behavior is the target, not an optional extension;
- when evidence is weak or missing, the system must expose uncertainty, narrow scope, or abstain.

### 2.4 Explicit deferrals that constrain evaluation

The harness must not silently redefine success using features explicitly deferred from MVP. In particular, MVP evaluation must not require:

- OCR or scanned-PDF support;
- rich layout reconstruction;
- special handling for tables, diagrams, charts, or figures as first-class evidence types;
- lexical index as a required retrieval layer;
- advanced hybrid retrieval tuning;
- sophisticated reranking pipelines as a precondition of success;
- precomputed summaries, synthetic questions, or graph-based derived knowledge;
- public-web knowledge or any answer behavior depending on external corpora.

### 2.5 Fallback validation path

Markdown-first evaluation may be used as a controlled fallback validation path if PDF normalization underperforms during early prototype pressure. However:

- this fallback is diagnostic only;
- it does not change the MVP target;
- release or architecture decisions must continue to optimize for mixed PDF + Markdown support.

### 2.6 Governing trust contract

The harness exists to test the following trust properties as non-negotiable system behavior:

- stable document identity;
- structural integrity where structure exists or can be inferred;
- traceability from retrieval units back to source;
- grounded answering rather than unsupported synthesis;
- honest failure behavior under insufficient support.

### 2.7 Consequence for downstream implementation

Any later evaluation design that optimizes for impressive answer phrasing while weakening provenance, support boundaries, or abstention behavior is misaligned with the MVP and therefore out of policy.

---

## 3. Evaluation thesis

The evaluation harness should be designed around a single thesis:

> In this MVP, quality is the product of controlled evidence flow, not of answer fluency alone.

This section defines the conceptual stance that governs the harness.

### 3.1 Contract-first evaluation

The harness does not ask only, “Did the model produce a plausible answer?” It asks:

- Was the answer materially supported by retrieved evidence?
- Was that evidence discoverable because the upstream representation was adequate?
- Was the evidence preserved in final context rather than lost or corrupted by assembly?
- Were citations resolvable and useful?
- Did the system abstain or narrow scope appropriately when the corpus did not support the claim?

This is what it means to evaluate the contract rather than the surface output.

### 3.2 Scenario-first evaluation

The harness must derive its tests from realistic end-to-end information-seeking scenarios over a bounded corpus. The system should be pressured by behaviorally meaningful cases such as factual lookup, section explanation, cross-document synthesis, source navigation, and insufficient-evidence queries.

The harness should not begin by enumerating isolated metrics detached from user-visible behavior. Metrics are downstream expressions of scenario pressure, not the primary source of truth.

### 3.3 Layered evaluation

The system must be evaluated across distinct quality layers because a final answer can fail for multiple upstream reasons. The harness must therefore preserve diagnostic separation among at least:

- representation quality;
- retrieval quality;
- context quality;
- answer quality;
- failure quality.

This separation is mandatory for regression analysis and prototype comparison.

### 3.4 Evidence-first evaluation

The harness should treat evidence as the main semantic unit of truth. An answer is not merely “correct” or “incorrect”; it is either:

- within sufficient support,
- only partially supported,
- or unsupported relative to the current corpus.

This distinction is central to safe grounded behavior.

### 3.5 Failure as a first-class outcome

A high-quality grounded system must sometimes refuse to overclaim. The harness must therefore treat the following as valid success behaviors when appropriate:

- explicit abstention;
- explicit scope narrowing;
- explicit uncertainty under partial support.

This is not a concession. It is part of the product contract.

### 3.6 Prototype and release implications

Because the harness evaluates evidence flow rather than answer phrasing alone, it must be available early enough to:

- pressure the first integrated prototype;
- compare prototype variants;
- identify dominant failure classes;
- prevent semantic drift across parsing, segmentation, retrieval, context assembly, citation, and answering;
- support later release gates.

---

## 4. Scope of the harness

This section defines exactly what the harness evaluates during MVP and what remains outside the evaluation boundary.

### 4.1 In-scope behaviors

The harness evaluates the following end-to-end system behaviors:

#### A. Representation behavior
- preservation of document identity;
- recovery of usable hierarchy when present or inferable;
- recoverable provenance for PDFs and Markdown;
- structurally sane segmentation inputs.

#### B. Retrieval behavior
- discovery of relevant evidence units;
- retrieval across document boundaries;
- retrieval of support sufficient to answer or abstain correctly;
- retrieval behavior under multiple scenario classes.

#### C. Context assembly behavior
- coherent ordering of retrieved evidence;
- inclusion of necessary local context or neighbors;
- avoidance of destructive redundancy;
- behavior under token-budget constraints.

#### D. Answer and citation behavior
- materially correct answering relative to available evidence;
- answer scoping consistent with support strength;
- source references that resolve to useful locations;
- avoidance of unsupported claims and fabricated provenance.

#### E. Failure behavior
- abstention under insufficient support;
- explicit uncertainty under partial support;
- local and interpretable failure modes;
- preservation of trust under degraded retrieval or degraded source structure.

### 4.2 In-scope scenario classes

The initial harness must include cases for at least the following scenario families:

- direct factual lookup;
- section-scoped explanation;
- multi-passage synthesis within one document;
- cross-document synthesis;
- source navigation and citation resolution;
- insufficient-evidence queries;
- nearby degraded-source cases that remain within MVP boundaries.

### 4.3 Out-of-scope system behavior for MVP harnessing

The harness does not attempt to validate:

- OCR performance on scanned PDFs;
- figure understanding;
- table-centric question answering as a first-class feature;
- exact scholarly citation formatting;
- external-web reasoning;
- exhaustive compare-and-contrast behavior across many viewpoints;
- very-large-corpus scale optimization;
- production-grade SLO, latency, or infra-hardening concerns beyond minimal reproducibility needs.

### 4.4 Stage-specific exclusions

During the earliest prototype phases, the harness may intentionally postpone:

- broad corpus-scale performance measurement;
- automated large-batch judge orchestration;
- complex benchmark dashboards;
- historical score trending beyond minimal baseline comparison.

However, early-phase simplification must not drop:

- mixed-format coverage,
- provenance checks,
- insufficient-evidence cases,
- or layered diagnostic separation.

### 4.5 Assumptions about corpus and question distribution

For MVP harness purposes, assume:

- a focused, bounded corpus rather than an internet-scale knowledge space;
- small-to-moderate corpus sizes suitable for initial prototype validation;
- users asking focused questions over technical documents, books, manuals, notes, and related material;
- mixed document quality, but not arbitrary corrupt or image-only inputs.

---

## 5. Core vocabulary and shared semantics

Live semantic authority for the evaluation harness now resides in the evergreen evaluation docs:

- `docs/delivery/eval-vocabulary.md`
- `docs/delivery/eval-support-semantics.md`
- `docs/delivery/eval-scenario-taxonomy.md`
- `docs/delivery/eval-failure-taxonomy.md`

This RFC depends on those definitions and should use them consistently rather than restating them.

For the rest of this document:

- Section 6 focuses on schema-facing object-model requirements for harness implementation.
- Section 7 focuses on scenario-driven coverage and authoring implications.
- Section 8 focuses on taxonomy usage and release implications.

---

## 6. Evaluation object model

The harness requires an explicit object model so evaluation remains implementable and reproducible. The semantic meaning of the core terms is governed by the evergreen docs; this section fixes the implementation-facing object and schema expectations.

### 6.1 Eval case

Each eval case record should include, at minimum:

- `case_id`;
- `scenario_class`;
- natural-language `question` or `prompt`;
- target `corpus_scope` or corpus subset;
- expected `support_state`;
- expected `answer_behavior`;
- expected `failure_behavior` when relevant;
- acceptable `evidence_requirements`;
- expected `citation_requirements`;
- relevant `failure_tags`.

### 6.2 Scenario

Scenario definitions or catalogs used by the harness should specify:
- the type of information need;
- the expected evidence pattern;
- the trust behavior under success or failure;
- the subsystem layers under pressure.

### 6.3 Corpus manifest

Each corpus manifest should capture, at minimum:
- document identity;
- source type;
- location or fixture reference;
- any relevant grouping needed by scenario authoring.

### 6.4 Gold evidence set

For each case, the schema should allow:
- one canonical gold set;
- or a small set of acceptable alternatives.

### 6.5 Retrieved evidence set

The harness should capture a pre-assembly retrieved-evidence object so it can distinguish:
- retrieval success,
- retrieval incompleteness,
- ranking errors,
- retrieval noise,
- and evidence fragmentation.

### 6.6 Final context artifact

The harness should capture the ordered evidence bundle actually provided to generation because the generator can fail even after raw retrieval success if context assembly:
- omits key support,
- introduces destructive redundancy,
- or disrupts local coherence.

### 6.7 Answer artifact

The answer artifact captured by the harness may contain:
- answer text;
- structured support metadata if emitted by the system;
- abstention indicators;
- confidence or scope qualifiers if present.

### 6.8 Citation artifact

For harness purposes, the citation artifact should preserve enough information to evaluate:
- resolvability;
- relevance;
- consistency with supporting evidence;
- usefulness for inspection.

### 6.9 Judgment result

Each judgment result should include, conceptually:
- evaluator name;
- pass/fail or score outcome;
- structured reasons;
- extracted support state where relevant;
- failure classification if applicable.

### 6.10 Failure classification

Harness outputs should record the dominant failure classification using the evergreen failure taxonomy rather than ad hoc free-text comments wherever possible.

### 6.11 Scorecard

Scorecards should preserve dimensional separation rather than collapsing everything into one opaque number.

### 6.12 Reproducibility envelope

The harness must also model a reproducibility envelope sufficient for regression work. This includes, conceptually:
- corpus version or fixture reference;
- system-under-evaluation configuration reference;
- evaluator configuration reference;
- run identifier;
- deterministic or semi-deterministic execution notes where relevant.

---

## 7. Scenario model

The scenario model is the primary design pressure for the harness. Scenarios must be derived from the product’s actual information-seeking use cases and from the workflow’s end-to-end evidence model.

### 7.1 Why scenarios come first

Scenarios express full request behavior. They pressure the system across representation, retrieval, context, answering, citation, and failure. Metrics derived without this pressure often optimize local behavior while leaving the end-to-end product unreliable.

### 7.2 Scenario design requirements

Every scenario included in the harness should specify:

- corpus condition;
- information need;
- expected evidence pattern;
- expected answer behavior;
- expected failure behavior if support is degraded or missing;
- the primary layers under pressure.

### 7.3 Required initial scenario classes
The canonical meanings of the scenario classes below are governed by `docs/delivery/eval-scenario-taxonomy.md`. This RFC fixes the minimum required coverage and the design pressure each class must apply.

#### A. Direct factual lookup
This class must pressure:
- passage adequacy,
- top-k precision,
- provenance correctness,
- citation usefulness.

#### B. Section-scoped explanation
This class must pressure:
- hierarchy recovery,
- section-path usefulness,
- neighbor expansion,
- context assembly coherence,
- coarse PDF provenance sufficiency.

#### C. One-document synthesis
This class must pressure:
- recall within a document,
- evidence-set assembly,
- ordering policy,
- answer scoping.

#### D. Cross-document synthesis
This class must pressure:
- corpus-level retrieval,
- document identity discipline,
- citation grouping,
- conflict handling,
- answer qualification when sources differ.

#### E. Source navigation
This class must pressure:
- resolvable provenance,
- anchor usefulness,
- stable linkage from answer to source,
- answer presentation trust.

#### F. Insufficient-evidence case
This class must pressure:
- abstention behavior,
- unsupported-claim prevention,
- scope narrowing,
- failure honesty.

#### G. Degraded-source edge case
This class must pressure:
- parser robustness,
- representation boundaries,
- failure containment,
- trust-preserving degradation behavior.

### 7.4 Scenario authoring principles

The harness should author scenarios that are:

- end-to-end rather than subsystem-isolated;
- compact but representative;
- realistic for the intended user base;
- explicitly bounded by the available corpus;
- interpretable by reviewers without hidden context.

### 7.5 Scenario coverage philosophy

The initial suite should prefer breadth across the core scenario classes over excessive depth within one question family. A narrow suite can overfit one retrieval or answer style and miss failure modes important to the MVP trust contract.

### 7.6 Scenario outcomes

For each scenario, expected outcomes should be expressed in terms of:

- support state;
- evidence pattern sufficiency;
- answer behavior;
- citation behavior;
- acceptable failure behavior.

This allows the harness to remain aligned with trust semantics rather than with exact phrasing.

### 7.7 Relationship between scenarios and suites

Scenarios are conceptual classes. Suites are execution selections.

A later execution document may define:
- smoke suite;
- full regression suite;
- release suite;
- exploratory or beta-derived suite.

This RFC does not freeze suite composition, but it does require that suite construction remain scenario-driven.

---

## 8. Failure taxonomy

Failure must be modeled explicitly. The harness cannot diagnose regressions or compare prototype variants if every bad result is reduced to “quality worse.”

### 8.1 Purpose of the failure taxonomy

The taxonomy exists to:
- derive targeted evaluations;
- classify regressions consistently;
- distinguish upstream and downstream failures;
- identify which design boundaries are under real pressure;
- guide mitigation ownership.

### 8.2 Canonical failure classes

The live definitions and examples for the failure classes are governed by `docs/delivery/eval-failure-taxonomy.md`.

Harness reports and review notes should use the following classes consistently:

- representation failure;
- segmentation failure;
- retrieval failure;
- context assembly failure;
- answering failure;
- citation failure;
- failure-quality failure.

### 8.3 Taxonomy usage rules

The harness should classify failures by dominant cause where possible, while allowing secondary tags when needed. The taxonomy is not intended to eliminate nuance, but to prevent non-diagnostic evaluation results. Severity interpretation should use the evergreen failure taxonomy rather than local redefinition.

### 8.4 Relationship to release policy

Not all failure classes are equally severe, but the following are presumptively release-blocking for MVP:

- fabricated provenance;
- repeated confident unsupported answering on insufficient-evidence cases;
- citation non-resolvability on otherwise “successful” answers;
- loss of mixed-format trust behavior in common cases.

The exact release gate policy belongs in a later document, but the taxonomy must be stable enough now to support such policy.

---

## 9. Evaluation dimensions and scoring philosophy

This section defines how the harness should think about quality and aggregation.

### 9.1 Primary evaluation dimensions

The harness must preserve separate reporting for at least five dimensions:

#### A. Representation quality
Measures whether the source representation preserves enough structure, identity, and provenance to support downstream grounding.

#### B. Retrieval quality
Measures whether the system discovers support sufficient for the question and scenario.

#### C. Context quality
Measures whether the retrieved evidence is assembled into a coherent, support-preserving context.

#### D. Answer quality
Measures whether the answer stays within the bounds of available evidence and remains materially correct relative to the corpus.

#### E. Failure quality
Measures whether the system fails honestly and usefully when support is weak or missing.

### 9.2 Release-facing trust view

In addition to the dimensional view, the harness should expose a compact trust-oriented summary for decision-making. For MVP, this trust view should emphasize metrics or judgments such as:

- grounded-answer rate;
- useful-citation rate;
- insufficient-evidence correctness;
- mixed-format scenario success rate;
- fabricated-provenance incident rate.

### 9.3 Scoring philosophy

The harness should avoid collapsing all evaluation into one composite number during early phases. A single score can hide dangerous regressions, such as higher answer plausibility paired with weaker provenance or worse abstention behavior.

Early-stage scorecards should therefore:
- preserve dimensional separation;
- preserve failure distributions;
- preserve scenario-class breakdowns;
- support side-by-side prototype comparison.

### 9.4 Deterministic vs rubric-based vs model-assisted judgment

Not all evaluation signals need the same judgment method.

Examples:
- citation resolvability may be deterministic;
- evidence hit-at-k may be deterministic or set-based;
- support sufficiency may require rubric-based or model-assisted judgment;
- answer overreach may be rubric-based with targeted review.

This document does not lock one judging mechanism for all dimensions, but it requires that judgment mode be explicit and reproducible.

### 9.5 Support-aware scoring

A case should not be scored as a simple right/wrong answer if the essential issue is support mismatch. The harness should distinguish at least:

- correct and supported;
- plausible but only partially supported;
- materially unsupported;
- correct abstention;
- unnecessary abstention.

### 9.6 Citation-aware scoring

Answer quality without citation quality is not sufficient for this product. A plausible answer with unusable or misleading provenance should not be scored as a clean success.

### 9.7 Failure-aware scoring

Failure handling must influence the overall trust interpretation. Systems that answer more aggressively but violate insufficient-evidence behavior should not appear better simply because they produce more non-empty responses.

### 9.8 Regression philosophy

The harness should be optimized for regression interpretability, not only benchmark ranking. Every aggregate result should be traceable to:

- scenario class,
- evaluator dimension,
- dominant failure type,
- and example failing cases.

---

## 10. Harness architecture

This section defines the conceptual architecture of the evaluation harness itself. It does not prescribe final module packaging, but it does define the functional responsibilities that must exist.

### 10.1 Architectural role of the harness

The harness is a cross-cutting verification system that evaluates the product under fixed corpus and scenario conditions. It must be able to:

- load corpora and eval cases reproducibly;
- execute the system under evaluation against those cases;
- capture intermediate artifacts where required;
- evaluate those artifacts at multiple layers;
- produce structured reports suitable for debugging, comparison, and release decision-making.

### 10.2 Conceptual execution flow

The harness should conceptually operate as follows:

1. load corpus manifest and eval suite;
2. establish run configuration and reproducibility envelope;
3. invoke the system under evaluation for each case;
4. collect intermediate and final artifacts;
5. run layered evaluators over those artifacts;
6. classify failures and aggregate outcomes;
7. emit run reports and comparison-friendly summaries.

### 10.3 Required logical components

The harness should contain, conceptually, at least the following components.

#### A. Corpus loader
Responsible for resolving the corpus manifest and making the intended evaluation corpus explicit.

#### B. Case loader
Responsible for loading eval cases, scenario metadata, and suite selection.

#### C. System-under-evaluation adapter
Responsible for invoking the product or prototype in a consistent way and capturing outputs relevant to evaluation.

#### D. Artifact collector
Responsible for capturing intermediate artifacts needed for layered evaluation, such as retrieved evidence sets, final context windows, answer outputs, and citations.

#### E. Layered evaluators
Responsible for evaluating:
- representation behavior,
- retrieval behavior,
- context behavior,
- answer behavior,
- failure behavior,
- citation behavior where treated separately.

#### F. Failure classifier
Responsible for mapping observed problems to the agreed failure taxonomy.

#### G. Scorecard and report generator
Responsible for emitting:
- per-case results,
- suite summaries,
- scenario breakdowns,
- failure distributions,
- comparison-friendly outputs.

### 10.4 System-under-evaluation interface

The harness should assume an abstract system-under-evaluation interface rather than coupling itself tightly to one codebase shape.

At minimum, the harness must be able to obtain or reconstruct:
- the answer output;
- citation output;
- retrieved evidence or retrieval traces when available;
- final context or sufficient context metadata when available;
- run configuration identity.

This abstraction is important because prototype code may evolve rapidly.

### 10.5 Intermediate artifact policy

Because this is a layered harness, intermediate artifact capture is not optional in principle, though the implementation may stage it gradually.

The harness should aim to preserve enough information to distinguish:
- retrieval miss,
- context loss,
- unsupported answering,
- citation mismatch,
- and insufficient-evidence handling errors.

### 10.6 Reproducibility requirements

The harness must be able to reproduce or at least structurally compare runs across prototype variants. Therefore it should preserve:
- corpus reference,
- suite reference,
- system configuration reference,
- evaluator configuration reference,
- run identifier,
- judgment configuration reference where applicable.

Exact bitwise determinism is not required for every layer, but unexplained evaluative drift is unacceptable.

### 10.7 Reporting requirements

The harness should produce outputs that support three kinds of work:

#### Debugging
Engineers need per-case and per-layer visibility.

#### Comparison
Prototype variants need scorecard and failure-distribution comparison.

#### Governance
Leads need release-facing summaries tied to trust behavior.

### 10.8 Architectural constraints on the harness

The harness should be:
- modular enough to add new evaluators later;
- strict enough to preserve the core semantics fixed in this RFC;
- lightweight enough to operate during prototype iteration;
- explicit enough to remain auditable.

### 10.9 Expected outputs of this architectural core

If implemented correctly, the harness architecture defined here should support:

- a stable scenario-driven evaluation workflow;
- layered diagnostics rather than answer-only scoring;
- trustworthy prototype comparison;
- later release-gate policy;
- extension into richer post-MVP evaluation without rewriting the semantic core.
