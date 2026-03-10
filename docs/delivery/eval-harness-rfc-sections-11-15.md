# RFC Companion: Evaluation Harness for MVP Document-Grounded QA — Sections 11-15

**Status:** Draft  
**Scope:** MVP / Version 1  
**Owner:** TBD  
**Last updated:** 2026-03-09  
**Related documents:** `mvp.md`, `workflow.md`, `eval-harness-rfc-sections-1-10.md`  
**Document role:** Operational and implementation-facing companion to the normative core.

---

## Document purpose

This companion document defines the **implementation-facing operating model** for the evaluation harness described in `eval-harness-rfc-sections-1-10.md`.

Sections 1-10 fix the semantic and architectural core of the harness. This document translates that core into dataset strategy, judgment strategy, phased implementation, release policy, and ownership. It is expected to evolve more frequently than the normative core, but it must remain subordinate to the semantics fixed there.

This document is intentionally practical. It is written to support stepwise implementation over a long-running workflow, not to serve as a generic benchmark memo.

---

## 11. Dataset and corpus strategy

The harness is only as useful as the corpus, scenarios, and annotations it is built on. A weak dataset strategy will create misleading confidence, hide failure modes, and distort optimization pressure.

For MVP, the dataset strategy must satisfy five requirements:

1. it must pressure the **actual product contract** rather than generic QA ability;
2. it must include **mixed-format** inputs from the start;
3. it must include **insufficient-evidence** and other honest-failure cases as first-class evaluation objects;
4. it must support **prototype comparison** and **regression analysis**;
5. it must remain small enough initially to be manually understood and curated.

### 11.1 Dataset design principles

#### 11.1.1 Corpus-boundedness
All evaluation cases must be answerable, partially answerable, or explicitly unanswerable **from the uploaded corpus alone**. The harness must never depend on public-web knowledge or latent-world assumptions.

#### 11.1.2 Scenario coverage before scale
The initial dataset should prioritize representational diversity of scenarios over raw volume. Fifty strong cases are more useful than five hundred weakly specified ones.

#### 11.1.3 Mixed-format realism
The seed corpus must contain both:

- text-based PDFs;
- Markdown files.

Markdown-only tracks may be used as diagnostic subsets, but they do not define success for the main harness.

#### 11.1.4 Evidence inspectability
Every gold case must be reviewable by a human annotator who can inspect the source documents and justify the support judgment.

#### 11.1.5 Stability with controlled growth
The initial baseline dataset should remain stable long enough to support meaningful comparison across prototype variants. New cases should be added through a controlled promotion process rather than casual accretion.

### 11.2 Corpus composition strategy

The harness should use a **seed corpus** intentionally constructed to expose the major MVP pressures.

Recommended seed corpus characteristics:

- at least one text-heavy PDF with recoverable headings;
- at least one PDF with weaker or noisier inferred structure;
- several Markdown documents with clear heading hierarchy;
- at least one Markdown document containing lists and code fences;
- some semantic overlap across documents so cross-document synthesis is possible;
- some non-overlap so insufficient-evidence cases are real rather than artificial.

The seed corpus does not need to be large. It does need to be representative enough that the harness can distinguish between:

- representation failure;
- retrieval failure;
- context loss;
- answer overreach;
- honest abstention.

### 11.3 Corpus manifest

Every evaluation dataset must reference a **corpus manifest** that makes the dataset reproducible.

The corpus manifest should record, at minimum:

- `corpus_id`
- `corpus_version`
- document list
- for each document:
  - `document_id`
  - `source_type` (`pdf` or `markdown`)
  - source filename/path
  - checksum or stable content fingerprint
  - optional human-readable title
  - optional notes about structure quality

The harness should treat the corpus manifest as the source of truth for reproducibility. If the corpus changes materially, the dataset version should change as well.

### 11.4 Scenario classes required in the baseline dataset

The baseline dataset must include cases across the canonical scenario classes defined in `docs/evergreen/eval-scenario-taxonomy.md`. This section fixes the required coverage and per-class dataset purpose for the baseline.

#### 11.4.1 Direct factual lookup
Purpose:
- pressure basic retrieval;
- validate passage selection;
- test citation usefulness on narrow support.

#### 11.4.2 Section-scoped explanation
Purpose:
- pressure structure recovery;
- validate neighborhood expansion;
- test whether the system can remain local rather than over-expand.

#### 11.4.3 One-document synthesis
Purpose:
- pressure passage segmentation;
- test evidence aggregation;
- test support completeness rather than fragment retrieval.

#### 11.4.4 Cross-document synthesis
Purpose:
- pressure multi-document retrieval;
- test context assembly under competing evidence;
- validate that the answer remains explicitly grounded.

#### 11.4.5 Source navigation
Purpose:
- pressure provenance preservation;
- test anchor resolution;
- verify inspection value rather than only answer text.

#### 11.4.6 Insufficient-evidence case
Purpose:
- test abstention behavior;
- test scope narrowing;
- test resistance to unsupported synthesis.

#### 11.4.7 Degraded-source edge case
Purpose:
- test robustness at the edge of supported input quality;
- expose representation and provenance failure modes;
- keep the harness honest about realistic PDF variation.

These cases must remain within MVP constraints. OCR-heavy scanned documents and table-first reasoning should not be required in the baseline release suite.

### 11.5 Initial dataset size recommendation

For the first baseline, target approximately **50-60 cases** distributed as follows:

- 10 direct factual lookup
- 10 section-scoped explanation
- 8 one-document synthesis
- 8 cross-document synthesis
- 6 source navigation
- 10 insufficient-evidence
- 6 degraded-source edge cases

This distribution is large enough to surface meaningful patterns while still being small enough for manual review and correction.

### 11.6 Case schema

Every evaluation case should be represented as a structured object with at least the following fields:

- `case_id`
- `dataset_version`
- `scenario_class`
- `question`
- `corpus_id`
- `corpus_subset` or referenced documents
- `expected_support_state`
- `gold_evidence_units` and/or `acceptable_evidence_sets`
- `required_documents`
- `citation_expectation`
- `expected_answer_behavior`
- `expected_failure_behavior`
- `tags`
- optional `notes`

The schema should be designed so it can evolve without invalidating earlier runs. Backward-compatible extension is strongly preferred over repeated schema churn.

### 11.7 Gold evidence specification

Gold evidence is often the most important and most difficult part of the dataset.

The harness should distinguish between:

- **required evidence units**: evidence that must appear for the answer to be considered properly supported;
- **acceptable evidence alternatives**: alternate passages or anchors that also legitimately support the answer;
- **context-neighbor allowances**: passages that may not be directly cited but are useful for local coherence.

This distinction avoids over-constraining the retrieval evaluator when multiple equivalent support paths exist.

### 11.8 Annotation workflow

The initial dataset should be **human-authored and human-reviewed**.

Recommended annotation workflow:

1. select a scenario class;
2. choose the question;
3. inspect the corpus manually;
4. mark the expected support state;
5. mark the gold evidence set or acceptable alternatives;
6. specify answer constraints and citation expectations;
7. perform peer review;
8. accept the case into the baseline dataset.

The initial authoring workflow should optimize for clarity and auditability, not throughput.

### 11.9 Annotation guide

The dataset must be paired with an annotation guide defining at minimum:

- how to determine support state;
- how to mark acceptable evidence alternatives;
- how to judge insufficient support;
- how to specify citation expectations for PDFs vs Markdown;
- how to tag likely failure classes;
- when to reject a proposed case as ambiguous or low value.

The annotation guide is a governing artifact for dataset consistency and should be versioned.

### 11.10 Dataset versions and promotion policy

The harness should maintain at least three conceptual dataset lanes:

#### 11.10.1 Smoke suite
A very small set of high-signal cases used for fast local checks.

Purpose:
- catch obvious regressions quickly;
- verify basic end-to-end integrity.

#### 11.10.2 Baseline full suite
The primary stable comparison set used for offline evaluation and prototype comparison.

Purpose:
- compare design variants;
- generate historical scorecards;
- surface systematic failure patterns.

#### 11.10.3 Release suite
A curated subset or superset used for release decisions.

Purpose:
- enforce no-regression on trust-critical behavior;
- verify mixed-format support;
- verify abstention behavior.

Promotion policy should be explicit:

- new cases enter first as candidates;
- candidates must be reviewed;
- reviewed cases may be promoted into baseline;
- only stable cases may become release blockers.

### 11.11 Beta-query intake policy

Once beta usage begins, real user questions should become a major source of new evaluation pressure. However, raw user queries must not be promoted directly into the gold dataset.

Recommended intake process:

1. capture query, retrieved evidence, answer, and failure outcome;
2. cluster by recurring failure pattern;
3. select representative candidates;
4. re-author them as reviewed evaluation cases;
5. add them to a future baseline version.

This preserves dataset quality while allowing the harness to learn from live usage.

### 11.12 Required artifacts for Section 11

Recommended artifacts:

- `evals/corpus/corpus-manifest.json`
- `evals/scenarios/scenario-catalog.md`
- `evals/datasets/baseline-v1.jsonl`
- `evals/datasets/annotation-guide.md`
- `evals/datasets/review-log.md`
- `evals/suites/smoke.txt`
- `evals/suites/full.txt`
- `evals/suites/release.txt`
- `evals/intake/beta-query-log.jsonl`
- `evals/intake/candidate-cases.md`

---

## 12. Judging methods

The harness must make judgments in a way that is repeatable, explainable, and proportionate to the maturity of the MVP. This requires a layered judging strategy rather than a single technique.

For MVP, judgments should be chosen based on the nature of the question being asked by the evaluator, not based on convenience.

### 12.1 Governing principles for judgment

#### 12.1.1 Prefer deterministic checks where possible
If a property can be checked directly, it should not be routed through an LLM judge.

Examples:
- citation resolution;
- presence of stable document IDs;
- evidence hit-at-k against a gold evidence set;
- schema validity;
- anchor resolvability.

#### 12.1.2 Use rubric-based judgment for semantic questions
If evaluation requires interpretation, the harness should use explicit rubrics rather than implicit intuition.

Examples:
- whether an answer overstates support;
- whether a partial answer appropriately narrows scope;
- whether a citation is genuinely useful for inspection;
- whether context assembly preserves necessary support.

#### 12.1.3 Use model-assisted judging only where it adds leverage
Model-assisted judging can be useful, but it must operate under explicit prompts, explicit rubrics, and review thresholds. It is a tool, not a source of truth.

#### 12.1.4 Preserve reviewability
Every important judgment must remain reviewable by a human engineer. If the harness cannot explain why it produced a result, it will not be trusted in regression triage.

#### 12.1.5 Separate signal generation from release policy
A judgment may generate useful diagnostic information without immediately being suitable as a release gate. New judging methods should mature before they become blocking.

### 12.2 Judgment categories

The harness should support four judgment categories.

### 12.2.1 Deterministic structural checks
Used when the property under evaluation is objectively checkable.

Typical targets:
- schema validity;
- document identity presence;
- source-type tagging;
- citation target existence;
- anchor resolution;
- evidence hit rate against exact gold units where appropriate.

Typical outputs:
- pass/fail;
- counts;
- precision/recall style metrics;
- missing-field reports.

### 12.2.2 Rule-based semantic checks
Used when the property is not purely structural but can still be operationalized without subjective scoring.

Typical targets:
- abstention keyword/path presence where abstention is required;
- whether the answer references unsupported documents;
- whether required documents are absent from retrieved evidence;
- whether citation count falls below the minimum expected shape.

Rule-based checks should be conservative and explicit.

### 12.2.3 Rubric-based judgment
Used when an evaluator must interpret support sufficiency, answer restraint, or citation usefulness.

Typical targets:
- support sufficiency;
- answer overreach;
- usefulness of source references;
- context completeness;
- quality of scope narrowing.

Rubrics should define:
- judgment question;
- acceptable evidence for each score band;
- escalation criteria;
- examples of positive and negative outcomes.

### 12.2.4 Model-assisted judgment
Used when semantic comparison is necessary at scale and deterministic methods are insufficient.

Appropriate uses:
- support comparison between answer claims and provided evidence;
- preliminary categorization of failure mode;
- draft scoring of citation usefulness under a fixed rubric.

Model-assisted judgment is acceptable only if:
- the prompt is versioned;
- the rubric is explicit;
- review thresholds are defined;
- outputs are stored for audit;
- blocking decisions can be escalated to human review.

### 12.3 Judgment targets by evaluation layer

The following distribution is recommended.

#### 12.3.1 Representation layer
Primary methods:
- deterministic checks;
- limited rule-based validation.

Typical judgments:
- are section paths present where expected;
- are anchors resolvable;
- are stable IDs present;
- are structural snapshots valid.

#### 12.3.2 Retrieval layer
Primary methods:
- deterministic hit-rate checks;
- rule-based completeness checks;
- rubric-based review for edge cases with alternate evidence paths.

Typical judgments:
- did top-k include support sufficient for the requested answer shape;
- did retrieval include all required support or only fragments;
- were correct documents present.

#### 12.3.3 Context layer
Primary methods:
- rule-based checks;
- rubric-based judgment;
- model-assisted judgment where context semantics are difficult to score deterministically.

Typical judgments:
- was critical evidence preserved in the final prompt context;
- was context bloated with irrelevant evidence;
- were necessary neighbors included.

#### 12.3.4 Answer layer
Primary methods:
- rubric-based judgment;
- deterministic citation validation;
- model-assisted claim-support analysis where helpful.

Typical judgments:
- are answer claims supported;
- is the answer materially correct relative to the corpus;
- does it overstate what the evidence warrants;
- are citations accurate and useful.

#### 12.3.5 Failure layer
Primary methods:
- rule-based checks;
- rubric-based judgment;
- model-assisted classification as a diagnostic aid.

Typical judgments:
- did the system abstain when evidence was insufficient;
- did it narrow scope appropriately;
- did it fabricate support;
- did it express uncertainty honestly.

### 12.4 Claim-level vs answer-level judgment

The harness should support both:

- **answer-level judgment** for coarse system comparisons;
- **claim-level judgment** for support fidelity and diagnostic accuracy.

Claim-level judgment is more expensive, but it is important for grounded systems because one answer may mix supported and unsupported claims. The harness should therefore allow the answer evaluator to decompose answers into claims when necessary.

### 12.5 Support-state judgment

The harness must judge support state strictly according to `docs/evergreen/eval-support-semantics.md`.

Judging mechanics:
- record one explicit support-state label for the requested answer shape;
- use `sufficient support`, `partial support`, or `insufficient support`;
- judge against the active corpus rather than world knowledge;
- preserve structured reasons rather than collapsing the result into binary correct/incorrect.

### 12.6 Citation usefulness judgment

A citation is not useful merely because it exists. The harness should score citation usefulness against at least these criteria:

- resolves to the correct document;
- resolves to an inspectable location or anchor at MVP granularity;
- is relevant to the claim it accompanies;
- is not misleadingly broad;
- provides enough locality for a user to verify the claim without excessive searching.

### 12.7 Human review path

The harness must define when humans override automation.

Human review is required when:
- a model-assisted judge determines a release-blocking failure;
- a new scoring rubric is introduced;
- dataset annotations appear internally inconsistent;
- prototype variants appear close enough that automated scores alone are not trustworthy;
- a failure mode is novel and not yet well represented in the taxonomy.

Human review decisions should be logged and, where appropriate, used to refine rubrics or prompts.

### 12.8 Judge versioning and auditability

All nontrivial judgment logic should be versioned.

Versioned items include:
- rubric versions;
- model-judge prompts;
- deterministic evaluator implementations;
- threshold policies;
- score aggregation rules.

Every evaluation run should record which judging versions were used. Without this, historical comparisons will be unreliable.

### 12.9 Recommended artifact set for Section 12

- `evals/rubrics/representation-rubric.md`
- `evals/rubrics/retrieval-rubric.md`
- `evals/rubrics/context-rubric.md`
- `evals/rubrics/answer-rubric.md`
- `evals/rubrics/failure-rubric.md`
- `evals/judges/prompts/*.md`
- `evals/judges/configs/*.yaml`
- `evals/reports/judge-audit/*.jsonl`

---

## 13. Phased implementation plan

This section defines the recommended build order for the evaluation harness. The phases are structured to preserve semantic discipline while still forcing early executable progress.

The governing rule is simple:

> do not build a broad harness before the evaluation semantics are clear, and do not continue semantic modeling indefinitely once the minimum viable semantics are fixed.

### 13.1 Phase 1 — Semantic lock

Objective:
Freeze the minimum shared evaluation semantics before implementing runners or scorecards.

Primary outputs:
- evaluation vocabulary;
- support-state semantics;
- scenario taxonomy;
- failure taxonomy;
- layer definitions.

Key activities:
- reconcile terminology across MVP, workflow, and prototype design;
- define support-state criteria;
- define citation expectations by source type;
- define the meaning of honest abstention for MVP.

Exit criteria:
- the team agrees on the definitions of sufficient, partial, and insufficient support;
- the main scenario classes are frozen for baseline authoring;
- major failure categories are named and distinct.

### 13.2 Phase 2 — Seed corpus and baseline dataset

Objective:
Produce the first evaluable corpus and gold case set.

Primary outputs:
- corpus manifest;
- scenario catalog;
- baseline dataset v1;
- annotation guide;
- review log.

Key activities:
- choose representative mixed-format documents;
- author initial cases across all required scenario classes;
- peer review annotations;
- create smoke, full, and release suite definitions.

Exit criteria:
- baseline v1 exists and is reviewable end-to-end;
- mixed-format coverage is present;
- insufficient-evidence cases are represented;
- the dataset is stable enough for prototype comparison.

### 13.3 Phase 3 — Harness skeleton

Objective:
Implement the minimal runnable harness framework without waiting for every evaluator to be sophisticated.

Primary outputs:
- dataset loader;
- corpus-manifest loader;
- system-under-evaluation interface;
- runner shell;
- report directory structure;
- simple summary output.

Key activities:
- define run configuration;
- define how the harness invokes the system under evaluation;
- define raw-output capture;
- implement deterministic structural checks first.

Exit criteria:
- a complete run can execute against the system;
- raw retrieval outputs, final answers, and citations are captured;
- at least basic structural and citation checks run automatically.

### 13.4 Phase 4 — Layered evaluators

Objective:
Implement evaluators for each major quality layer.

Primary outputs:
- representation evaluator;
- retrieval evaluator;
- context evaluator;
- answer evaluator;
- failure evaluator.

Key activities:
- connect each evaluator to the dataset schema;
- implement deterministic metrics where possible;
- add rubric-based or model-assisted judging only where needed;
- produce per-layer reports and failure classifications.

Exit criteria:
- the harness can identify not only that a case failed, but where it failed;
- scorecards are produced by layer;
- regression diffs are intelligible to engineers.

### 13.5 Phase 5 — Baseline comparisons and prototype pressure

Objective:
Use the harness to compare early system variants and identify the dominant design pressures.

Primary outputs:
- baseline configuration registry;
- comparative scorecards;
- failure-diff reports;
- design decision logs.

Key activities:
- run the harness against prototype variants;
- compare section-aware vs flat chunking;
- compare alternate citation/provenance strategies;
- compare stricter vs looser abstention policies;
- identify systematic rather than anecdotal regressions.

Exit criteria:
- the harness can support concrete design decisions;
- there is at least one stable baseline variant for future regression tracking;
- major quality bottlenecks are known.

### 13.6 Phase 6 — CI integration and release gating

Objective:
Integrate the harness into the delivery loop.

Primary outputs:
- CI jobs for smoke and full evaluation;
- release scorecard generation;
- blocking thresholds for trust-critical metrics;
- regression history snapshots.

Key activities:
- wire smoke suite into fast checks;
- wire full suite into merge or nightly jobs;
- define release gating policy;
- record historical runs for trend analysis.

Exit criteria:
- the harness is part of normal engineering flow;
- trust-critical regressions are visible before release;
- score histories exist for comparison across versions.

### 13.7 Phase 7 — Beta shadow evaluation

Objective:
Extend the harness using real usage without destabilizing the baseline.

Primary outputs:
- beta query intake pipeline;
- candidate-case promotion workflow;
- baseline v2 planning;
- updated release suite proposals.

Key activities:
- ingest beta queries and failure outcomes;
- cluster recurring issues;
- author reviewed cases from production-like examples;
- expand the dataset deliberately.

Exit criteria:
- the harness evolves based on real user pressure;
- new cases are added through review rather than drift;
- release policy remains stable while the baseline grows.

### 13.8 Implementation sequencing rules

To keep the long-running workflow disciplined, the following sequencing rules should apply:

1. do not expand the dataset before the schema and annotation rules are stable enough to avoid rework;
2. do not add model-assisted judging before deterministic and rubric-based opportunities have been exhausted;
3. do not make a metric release-blocking on its first appearance;
4. do not keep semantic questions open once implementation depends on them;
5. do not wait for a “perfect” harness before using it to pressure the prototype.

### 13.9 Recommended workstream outputs by phase

#### Phase 1
- `docs/evergreen/eval-vocabulary.md`
- `docs/evergreen/eval-support-semantics.md`
- `docs/evergreen/eval-scenario-taxonomy.md`
- `docs/evergreen/eval-failure-taxonomy.md`

#### Phase 2
- `evals/corpus/corpus-manifest.json`
- `evals/scenarios/scenario-catalog.md`
- `evals/datasets/baseline-v1.jsonl`
- `evals/datasets/annotation-guide.md`

#### Phase 3
- `evals/runners/main.py`
- `evals/interfaces/system_under_eval.py`
- `evals/reports/<run_id>/summary.json`

#### Phase 4
- `evals/runners/representation_eval.py`
- `evals/runners/retrieval_eval.py`
- `evals/runners/context_eval.py`
- `evals/runners/answer_eval.py`
- `evals/runners/failure_eval.py`

#### Phase 5
- `evals/baselines/baseline-configs.yaml`
- `evals/reports/<run_id>/scorecard.md`
- `docs/workstreams/WS-XXX/eval-decisions.md`

#### Phase 6
- CI workflow files
- `evals/suites/{smoke,full,release}.txt`
- `evals/reports/history/*.json`

#### Phase 7
- `evals/intake/beta-query-log.jsonl`
- `evals/intake/candidate-cases.md`
- `evals/datasets/baseline-v2-plan.md`

---

## 14. Release gates and decision policy

The evaluation harness is only useful if its outputs affect engineering decisions. This section defines how evaluation results should influence release readiness and change acceptance.

### 14.1 Governing release philosophy

The MVP should be released based on preservation of the **trust contract**, not on isolated answer fluency.

A release decision should therefore prioritize:

- grounded-answer behavior;
- citation usefulness and inspectability;
- insufficient-evidence correctness;
- mixed-format reliability;
- absence of fabricated support.

The release process should prefer a narrower, honest system over a broader system that answers more often but violates support boundaries.

### 14.2 Gate categories

Release gates should be grouped into three categories.

#### 14.2.1 Hard blockers
Failures that should block release until fixed or explicitly waived.

Recommended hard blockers for MVP:
- fabricated or misleading provenance;
- systematic answering on insufficient-support cases where abstention is expected;
- loss of mixed-format support in the release suite;
- severe regression in citation resolution;
- inability to reproduce harness results for the candidate build.

#### 14.2.2 Soft blockers
Failures that require explicit review and decision but may not always block release.

Examples:
- moderate regression in one scenario class with limited user impact;
- localized representation regression in a non-goal document shape;
- non-critical score deterioration where trust-critical metrics remain stable.

#### 14.2.3 Observational signals
Metrics that are tracked for learning but do not yet affect release.

Examples:
- new experimental context-quality metrics;
- early model-judge outputs still undergoing calibration;
- beta-only scenario expansions not yet stabilized.

### 14.3 Trust-critical release metrics

The release scorecard should prominently report at least these metrics:

- grounded-answer rate;
- unsupported-claim incidence;
- citation usefulness rate;
- citation resolution success rate;
- insufficient-evidence correctness;
- mixed-format success rate;
- cross-document synthesis success rate for the supported subset.

These metrics should be shown both as current values and as deltas relative to the most recent accepted baseline.

### 14.4 Release suite policy

The release suite should be a curated set of cases designed to represent the minimum trustworthy system shape.

Requirements:
- include both PDFs and Markdown;
- include at least one representative case per required scenario class;
- include insufficient-evidence cases;
- include at least one degraded-source case within MVP scope;
- remain small enough for rapid review when release-blocking failures occur.

The release suite should be stable. Frequent churn in release cases weakens comparability and makes gate decisions noisy.

### 14.5 No-regression policy

The harness should enforce a **no-regression principle** on trust-critical behavior.

A release candidate should not be accepted if it materially worsens:
- grounded-answer behavior;
- provenance correctness;
- citation usefulness;
- insufficient-evidence handling.

Improvement in answer fluency does not compensate for regression in these properties.

### 14.6 Exception policy

There must be a formal path for exceptions, but exceptions should be rare.

An exception must document:
- the failing metric or gate;
- the scenario scope of impact;
- why the issue is accepted temporarily;
- risk to user trust;
- owner and deadline for remediation;
- whether the exception changes future baseline expectations.

Temporary exceptions should be recorded in the workstream documents, not hidden in chat or merge comments.

### 14.7 Promotion policy for new metrics

A new metric should not become release-blocking immediately.

Recommended promotion path:
1. observational only;
2. reviewed for stability over one or more baseline cycles;
3. optionally becomes soft blocker;
4. only then becomes a hard blocker if warranted.

This reduces noise and prevents premature gate instability.

### 14.8 Handling ambiguous failures

Some failures will not fit cleanly into a single category or may be close to decision thresholds.

When ambiguity exists:
- perform human review;
- inspect the evidence and source documents directly;
- classify the dominant failure mode;
- record the decision and rationale;
- update rubrics or thresholds if the ambiguity reveals a modeling gap.

The goal is not to force false precision. The goal is to preserve trustworthy release decisions.

### 14.9 Reporting requirements for release decisions

Every release-oriented evaluation run should produce:

- summary scorecard;
- comparison to previous accepted baseline;
- list of hard-blocking failures;
- list of soft-blocking regressions;
- failure taxonomy distribution;
- judge versions and dataset version;
- exception ledger if any waivers are applied.

### 14.10 Recommended artifact set for Section 14

- `evals/reports/<run_id>/scorecard.md`
- `evals/reports/<run_id>/summary.json`
- `evals/reports/<run_id>/failures.jsonl`
- `evals/reports/history/*.json`
- `docs/workstreams/WS-XXX/eval-regressions.md`
- `docs/workstreams/WS-XXX/eval-exceptions.md`

---

## 15. Ownership and operating model

The evaluation harness requires explicit ownership. If it is treated as a side utility owned by no one, it will drift, become noisy, and lose authority.

### 15.1 Ownership model

The recommended ownership model has four roles.

#### 15.1.1 Harness owner
Responsible for overall harness integrity.

Responsibilities:
- maintain runner architecture;
- maintain evaluation schemas and interfaces;
- maintain report generation;
- ensure reproducibility and historical comparability;
- coordinate upgrades to scoring logic.

#### 15.1.2 Dataset owner
Responsible for corpus and case integrity.

Responsibilities:
- maintain corpus manifest;
- curate baseline datasets;
- maintain annotation guide;
- review candidate cases;
- control dataset versioning and promotion.

#### 15.1.3 Rubric and judgment owner
Responsible for semantic consistency of evaluations.

Responsibilities:
- maintain rubrics;
- maintain judge prompts/configs;
- calibrate model-assisted judgments;
- define review thresholds;
- audit scoring drift.

#### 15.1.4 Subsystem metric owners
Engineers responsible for representation, retrieval, answer/citation, or failure-behavior subsystems.

Responsibilities:
- own improvements in their layer;
- investigate regressions surfaced by the harness;
- propose metric refinements with the harness owner;
- avoid subsystem-local optimization that breaks end-to-end trust behavior.

### 15.2 Review cadence

The harness should operate under a regular review rhythm.

Recommended cadence:

- **per change / local:** smoke suite during active development;
- **daily or merge-based:** full-suite review for major branches or mainline;
- **weekly:** evaluation review meeting focused on failure patterns and new candidate cases;
- **release-boundary:** formal release scorecard review with blocker decisions.

Cadence may be adapted to team size, but the distinction between local feedback, regression review, and release review should remain.

### 15.3 Decision forums

Different evaluation decisions belong in different forums.

#### 15.3.1 Semantic decisions
Examples:
- changing support-state definitions;
- revising scenario taxonomy;
- changing citation usefulness criteria.

Forum:
- RFC review or explicit architectural review.

#### 15.3.2 Operational decisions
Examples:
- adding cases to the smoke suite;
- rotating the release suite;
- updating thresholds for a mature metric.

Forum:
- harness review or workstream review.

#### 15.3.3 Incident and regression decisions
Examples:
- triaging a failing release candidate;
- deciding whether a regression is blocking;
- granting a temporary exception.

Forum:
- release readiness review or designated owner review.

### 15.4 Change control rules

The following changes should require explicit review and approval:

- changes to dataset schema;
- changes to support-state semantics;
- addition of a new hard-blocking metric;
- changes to core rubrics;
- replacement of the model-judge prompt/config used in blocking decisions;
- changes to the release suite composition.

Minor implementation refactors that do not alter semantics may proceed through normal engineering review.

### 15.5 Workstream integration

The harness must be integrated into the broader delivery workflow rather than run as an isolated QA process.

Each workstream should maintain at least:
- an `eval-decisions.md` log for notable design decisions informed by harness results;
- an `eval-regressions.md` log for important failure patterns, hypotheses, and fixes;
- where needed, an `eval-exceptions.md` ledger for temporary waivers.

This preserves institutional memory and prevents repeated rediscovery of the same failures.

### 15.6 Operating norms

The following norms should govern day-to-day harness use.

#### 15.6.1 Do not optimize to one number
Use the layered scorecard and failure taxonomy. A subsystem should not optimize a local metric at the cost of trust-critical end-to-end behavior.

#### 15.6.2 Do not hide ambiguity
When cases, rubrics, or judgments are ambiguous, record the ambiguity and resolve it deliberately rather than silently forcing a score.

#### 15.6.3 Do not let the dataset drift casually
Dataset changes must be reviewed. Casual case churn destroys comparability.

#### 15.6.4 Do not over-automate too early
Use humans where the rubrics or support semantics are not yet mature enough for reliable automation.

#### 15.6.5 Use the harness to learn, not just to block
The harness is both a gate and a learning instrument. Failure distributions and comparative runs should actively shape design decisions.

### 15.7 Minimal staffing recommendation

For a small MVP team, one person may temporarily hold multiple roles, but the responsibilities should still be explicit.

Minimum viable staffing model:
- one harness owner;
- one dataset/rubric owner, which may be the same person early on;
- subsystem engineers responsible for remediation in their layers.

Even in a small team, unowned evaluation responsibilities will degrade quickly.

### 15.8 Recommended artifact set for Section 15

- `docs/workstreams/WS-XXX/eval-decisions.md`
- `docs/workstreams/WS-XXX/eval-regressions.md`
- `docs/workstreams/WS-XXX/eval-exceptions.md`
- `evals/owners/ownership-map.md`
- `evals/owners/review-cadence.md`

---

## Closing note

Sections 11-15 should be treated as the **operational companion** to the normative core in Sections 1-10.

If implementation pressure reveals that a semantic assumption in these sections conflicts with the core vocabulary, support semantics, or failure taxonomy established in the normative document, the normative core wins and this companion must be revised.

The intended use of this document is stepwise delivery: establish the corpus and dataset, implement the harness skeleton, layer in judgments, pressure the prototype, and only then harden release policy and long-term operating rhythm.
