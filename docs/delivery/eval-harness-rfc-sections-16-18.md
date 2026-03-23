# RFC Companion: Evaluation Harness for MVP Document-Grounded QA — Sections 16-18

**Status:** Draft  
**Scope:** MVP / Version 1  
**Owner:** TBD  
**Last updated:** 2026-03-09  
**Related documents:** `mvp.md`, `workflow.md`, `eval-harness-rfc-sections-1-10.md`, `eval-harness-rfc-sections-11-15.md`  
**Document role:** Supporting companion covering artifact map, open questions, and appendices.

---

## Document purpose

This companion document completes the three-part evaluation harness RFC set.

- `eval-harness-rfc-sections-1-10.md` fixes the normative core: purpose, constraints, vocabulary, object model, scenario model, failure taxonomy, scoring philosophy, and harness architecture.
- `eval-harness-rfc-sections-11-15.md` defines the implementation-facing operating model: dataset strategy, judging methods, phased implementation, release gates, and ownership.
- This document defines the **supporting artifact map**, the **bounded open questions register**, and the **appendical reference material** needed to execute the harness over time without letting the core RFC expand into an operational monolith.

This document is intentionally more concrete than the normative core but less binding than the core semantics. It should remain aligned to the first two documents and should not introduce product-scope expansion on its own.

---

## 16. Artifact map

The evaluation harness should be treated as a real subsystem with a deliberate artifact topology, not as a loose pile of scripts and ad hoc spreadsheets. The artifact map exists to do four things:

1. make the harness discoverable and operable by more than one engineer;
2. separate evergreen semantics from temporal execution material;
3. make runs, datasets, rubrics, and reports reproducible;
4. prevent drift between what the RFC says and what the repository actually contains.

For MVP, the artifact map should distinguish four classes of artifacts:

- **evergreen artifacts** that define stable semantics and policy;
- **execution artifacts** that implement and operate the harness;
- **temporal workstream artifacts** that track current decisions, regressions, and rollout issues;
- **generated artifacts** that are produced by harness runs and should not be manually edited.

### 16.1 Top-level artifact classes

#### 16.1.1 Evergreen artifacts
These are documents whose role is to remain stable across multiple workstreams and implementation iterations.

Typical characteristics:
- reviewed deliberately;
- changed relatively infrequently;
- referenced by engineering decisions and release policy;
- authoritative for semantics.

#### 16.1.2 Execution artifacts
These are files that directly implement or configure the harness.

Typical characteristics:
- evolve as the harness matures;
- encode schemas, runners, suites, and judgment logic;
- versioned with the codebase;
- should remain consistent with the semantics fixed in the evergreen docs.

#### 16.1.3 Temporal workstream artifacts
These capture the current state of an active delivery track.

Typical characteristics:
- tied to a workstream or milestone;
- record regressions, decisions, trade-offs, and rollout notes;
- may be superseded later;
- should not quietly override evergreen policy.

#### 16.1.4 Generated artifacts
These are outputs of the harness itself.

Typical characteristics:
- created by runs;
- immutable once published for a given run;
- used for debugging, comparison, and auditability;
- often large or machine-generated.

### 16.2 Recommended repository layout

The exact repository layout may vary, but for MVP the harness should expose a directory structure with clear semantic separation.

```text
/docs
  /evergreen
    eval-harness-rfc.md
    eval-vocabulary.md
    eval-support-semantics.md
    eval-failure-taxonomy.md
    eval-rubrics.md
  /workstreams
    /WS-XXX-eval-harness
      workstream.md
      eval-decisions.md
      eval-regressions.md
      rollout-notes.md

/evals
  /corpus
    corpus-manifest.json
    corpus-notes.md
  /datasets
    baseline-v1.jsonl
    baseline-v2.jsonl
    smoke-v1.jsonl
    release-v1.jsonl
    annotation-guide.md
    dataset-review-log.md
  /scenarios
    scenario-catalog.md
    direct-factual-lookup.md
    section-scoped-explanation.md
    one-document-synthesis.md
    cross-document-synthesis.md
    source-navigation.md
    insufficient-evidence.md
    degraded-source-edge-cases.md
  /schemas
    eval-case.schema.json
    corpus-manifest.schema.json
    run-summary.schema.json
    failure-record.schema.json
  /configs
    harness-defaults.yaml
    suites.yaml
    judging.yaml
    report-format.yaml
  /suites
    smoke.txt
    full.txt
    release.txt
  /runners
    run_eval.py
    representation_eval.py
    retrieval_eval.py
    context_eval.py
    answer_eval.py
    failure_eval.py
    report_builder.py
  /judges
    deterministic_checks.py
    rubric_checks.py
    model_assisted_judges.py
    human_review_templates.md
  /reports
    /2026-03-09-baseline-a
      summary.json
      scorecard.md
      failures.jsonl
      per_case.jsonl
      retrieval_debug.jsonl
      context_debug.jsonl
      answer_debug.jsonl
  /baselines
    baseline-configs.yaml
    comparison-notes.md
```

This layout is illustrative, not mechanically binding, but the separation of concerns is deliberate and should be preserved even if naming changes.

### 16.3 Evergreen artifact set

At minimum, the following evergreen artifacts should exist.

#### 16.3.1 `docs/evergreen/eval-harness-rfc.md`
This is the assembled RFC or an index document pointing to the three RFC fragments.

Role:
- canonical entry point for the evaluation harness design;
- defines the normative and operational document set;
- links to companion artifacts.

#### 16.3.2 `docs/delivery/eval-vocabulary.md`
Role:
- freezes shared terms such as document, section, passage, anchor, evidence unit, evidence set, support state, citation, abstention, and failure class;
- prevents semantic drift across ingestion, retrieval, answer generation, and evaluation.

#### 16.3.3 `docs/delivery/eval-support-semantics.md`
Role:
- defines sufficient, partial, and insufficient support;
- defines acceptable support alternatives;
- defines evidence-set sufficiency rules;
- defines what counts as groundedness for MVP.

#### 16.3.4 `docs/delivery/eval-failure-taxonomy.md`
Role:
- enumerates failure classes and sub-classes;
- provides examples and likely upstream causes;
- aligns debugging and release triage.

#### 16.3.5 `docs/evergreen/eval-rubrics.md`
Role:
- provides stable judgment rubrics for support, citation usefulness, answer overreach, abstention, and failure classification;
- centralizes judgment policy so it is not duplicated across code and notes.

### 16.4 Execution artifact set

These artifacts make the harness runnable.

#### 16.4.1 Corpus artifacts

**`evals/corpus/corpus-manifest.json`**  
Defines the corpus used for a dataset or suite.

Recommended fields:
- `corpus_id`
- `corpus_version`
- document descriptors
- checksums/fingerprints
- source type
- optional notes about structure quality or caveats

**`evals/corpus/corpus-notes.md`**  
Human-readable explanation of why the corpus was selected, its structure characteristics, and its intended scenario pressure.

#### 16.4.2 Dataset artifacts

**`evals/datasets/*.jsonl`**  
Structured case collections such as baseline, smoke, and release suites.

**`evals/datasets/annotation-guide.md`**  
Defines annotation policy and review rules.

**`evals/datasets/dataset-review-log.md`**  
Records case additions, removals, clarifications, and review outcomes.

#### 16.4.3 Scenario artifacts

**`evals/scenarios/scenario-catalog.md`**  
Lists supported scenario classes and their evaluation purpose.

**Per-scenario reference docs**  
Capture the behavioral intent of each scenario family and serve as the conceptual bridge between RFC and dataset authoring.

#### 16.4.4 Schema artifacts

**`evals/schemas/eval-case.schema.json`**  
Machine-readable schema for evaluation cases.

**`evals/schemas/corpus-manifest.schema.json`**  
Machine-readable schema for corpus manifests.

**`evals/schemas/run-summary.schema.json`**  
Schema for run summary outputs.

**`evals/schemas/failure-record.schema.json`**  
Schema for failure records.

Schemas are valuable because they turn implicit conventions into enforceable structure.

#### 16.4.5 Runner artifacts

**`evals/runners/run_eval.py`**  
Entrypoint for harness execution.

**Layer-specific evaluators**  
Representation, retrieval, context, answer, and failure evaluators should remain individually runnable where practical. This keeps diagnosis and local iteration efficient.

**`evals/runners/report_builder.py`**  
Responsible for assembling machine-readable outputs into a stable report package.

#### 16.4.6 Judgment artifacts

**`evals/judges/deterministic_checks.py`**  
Implements non-probabilistic checks such as schema validity, anchor resolution, citation resolvability, or evidence hit-at-k.

**`evals/judges/rubric_checks.py`**  
Implements rubric-driven evaluation logic, whether performed by code, operator workflow, or model-assisted judgment.

**`evals/judges/model_assisted_judges.py`**  
Encapsulates any judge models used for support or overreach classification. This layer should remain explicit and configurable rather than hidden inside general runner code.

#### 16.4.7 Configuration artifacts

**`evals/configs/harness-defaults.yaml`**  
Default execution configuration.

**`evals/configs/suites.yaml`**  
Maps suites to dataset files, corpora, and thresholds.

**`evals/configs/judging.yaml`**  
Defines judgment modes, thresholds, and any confidence-related settings.

**`evals/configs/report-format.yaml`**  
Standardizes report shape so downstream readers and tools remain stable.

### 16.5 Temporal workstream artifacts

These artifacts keep long-running delivery grounded without polluting evergreen documents.

#### 16.5.1 `docs/workstreams/WS-XXX-eval-harness/workstream.md`
The current workstream state card.

Recommended contents:
- current goals;
- current stage;
- active risks;
- next decisions;
- links to current run reports and related branches.

#### 16.5.2 `eval-decisions.md`
Captures decisions that affect implementation or rollout within the workstream but do not yet warrant evergreen promotion.

Examples:
- temporary judgment policy for prototype comparison;
- choice of seed corpus revision;
- decision to keep a metric advisory rather than release-blocking.

#### 16.5.3 `eval-regressions.md`
Tracks material regressions and their disposition.

Recommended fields:
- regression identifier;
- first observed run;
- affected dimensions;
- suspected failure class;
- severity;
- mitigation plan;
- closure criteria.

#### 16.5.4 `rollout-notes.md`
Operational notes during beta or release-hardening phases.

This should include:
- notable failure patterns from user traffic;
- cases proposed for dataset promotion;
- temporary guardrails or mitigations.

### 16.6 Generated artifact set

Generated artifacts should be treated as immutable outputs for a given run and version set.

#### 16.6.1 Run package
Each run should emit a package with at least:
- summary;
- scorecard;
- per-case results;
- failure records;
- any layer-specific debug outputs needed for diagnosis.

#### 16.6.2 Suggested generated files

**`summary.json`**  
High-level machine-readable summary.

**`scorecard.md`**  
Human-readable summary emphasizing trust dimensions and regressions.

**`per_case.jsonl`**  
Case-level outputs for filtering and analysis.

**`failures.jsonl`**  
Normalized failure records.

**`retrieval_debug.jsonl`**, **`context_debug.jsonl`**, **`answer_debug.jsonl`**  
Optional but valuable debugging detail for deep inspection.

### 16.7 Artifact lifecycle rules

To keep the harness coherent, the following lifecycle rules are recommended.

#### 16.7.1 Evergreen promotion rule
A concept should not become an evergreen artifact unless:
- it has affected multiple decisions or workstreams;
- it is expected to remain stable for some time;
- ambiguity around it has already produced or is likely to produce drift.

#### 16.7.2 Temporal artifact retirement rule
Temporal artifacts may be retired or archived once:
- the workstream closes;
- relevant decisions have either been promoted or intentionally discarded;
- referenced reports remain discoverable elsewhere.

#### 16.7.3 Generated artifact immutability rule
A published run package should not be edited in place. If a bug invalidates the run, publish a corrected run with a new identifier and record the supersession relationship.

#### 16.7.4 Dataset and schema compatibility rule
Schema evolution should prefer additive, backward-compatible changes. Breaking changes should trigger explicit version increments and migration notes.

### 16.8 Traceability expectations across artifacts

The artifact graph should support the following traceability chain:

- release decision -> scorecard -> run package -> suite -> dataset version -> corpus version -> source documents;
- regression record -> failure class -> affected cases -> underlying reports -> candidate fix;
- scenario definition -> dataset cases -> evaluator outputs -> threshold policy.

If this traceability is missing, the harness will be difficult to trust under delivery pressure.

### 16.9 Minimum artifact set for initial implementation

If implementation needs to start with the smallest viable artifact set, begin with:

**Evergreen**
- `docs/evergreen/eval-harness-rfc.md`
- `docs/delivery/eval-vocabulary.md`
- `docs/delivery/eval-failure-taxonomy.md`

**Execution**
- `evals/corpus/corpus-manifest.json`
- `evals/datasets/baseline-v1.jsonl`
- `evals/datasets/annotation-guide.md`
- `evals/scenarios/scenario-catalog.md`
- `evals/schemas/eval-case.schema.json`
- `evals/runners/run_eval.py`
- `evals/reports/<run-id>/summary.json`
- `evals/reports/<run-id>/scorecard.md`

**Temporal**
- `docs/workstreams/WS-XXX-eval-harness/workstream.md`
- `docs/workstreams/WS-XXX-eval-harness/eval-regressions.md`

This set is intentionally minimal but still sufficient to avoid total operational drift.

---

## 17. Open questions

Open questions should be treated as a bounded register of unresolved decisions that materially affect implementation, evaluation legitimacy, or release policy. This section exists to prevent unresolved issues from remaining implicit.

Open questions should not be used as a dumping ground. Every question should either:
- be answered and promoted into the evergreen or operational documents;
- be explicitly deferred with rationale;
- or be removed because it no longer matters.

### 17.1 How to use this section

For each open question, record:
- the question itself;
- why it matters;
- the likely decision owner;
- the expected evidence needed to resolve it;
- whether it blocks implementation, release gating, or neither.

A simple status model is sufficient:
- `open`
- `in investigation`
- `decided`
- `deferred`
- `retired`

### 17.2 Core open questions for MVP

The following questions are likely to matter early and should be carried explicitly.

#### 17.2.1 What is the minimum acceptable provenance granularity for PDFs?

**Why it matters:**  
The MVP requires inspectable evidence and coarse provenance, but not exact layout reconstruction. The release harness needs a concrete rule for when a PDF citation is considered useful enough.

**Competing interpretations:**
- page-level provenance is sufficient for MVP;
- page + inferred section path is required when recoverable;
- anchor-like within-page spans are desirable but non-blocking.

**Impact area:**
- citation usefulness scoring;
- release gates;
- parser and normalizer requirements.

**Likely owner:**
- principal engineer / ingestion and evaluation leads.

**Expected evidence to resolve:**
- annotation trials on representative PDF cases;
- user inspection studies or internal operator review.

#### 17.2.2 What qualifies as a useful citation in Markdown and PDF?

**Why it matters:**  
The harness can resolve a citation mechanically yet still produce a poor user inspection experience. MVP needs a practical definition of “useful enough” that goes beyond technical resolvability.

**Impact area:**
- citation rubric;
- answer evaluator;
- release policy.

#### 17.2.3 How strict should support judgments be for multi-passage synthesis?

**Why it matters:**  
Cross-passage and cross-document synthesis can be either under-credited or over-credited depending on how support sufficiency is defined. Too strict and the harness blocks useful behavior; too loose and it legitimizes overreach.

**Impact area:**
- support semantics;
- answer-support judging;
- release thresholds.

#### 17.2.4 When should abstention be required versus optional?

**Why it matters:**  
Not every weak-support case should collapse to total abstention. Some cases may justify a narrow or qualified answer. The harness needs a stable distinction.

**Impact area:**
- failure-quality evaluation;
- answer behavior rubric;
- release gate policy.

#### 17.2.5 How much model-assisted judging is acceptable in the early harness?

**Why it matters:**  
Model-assisted judges are often useful for nuanced support and overreach decisions, but they also introduce variance and policy ambiguity. Early on, the team needs a clear boundary.

**Impact area:**
- judging methods;
- reproducibility;
- trust in regression signals.

**Resolution considerations:**
- deterministic checks should dominate where possible;
- model-assisted judging should be explicit, configurable, and reviewable;
- human spot-review may remain necessary early.

#### 17.2.6 What is the minimum mixed-format coverage required for release confidence?

**Why it matters:**  
The MVP target is mixed PDF + Markdown support, but the release harness needs a concrete statement of how much coverage is enough to claim confidence rather than isolated success.

**Impact area:**
- release suite composition;
- corpus selection;
- milestone planning.

#### 17.2.7 How should degraded-source cases be represented without distorting the MVP boundary?

**Why it matters:**  
The harness should include realistic weak-structure cases, but it should not accidentally create a release standard for OCR-heavy or table-centric documents that MVP explicitly defers.

**Impact area:**
- dataset curation;
- release interpretation;
- scope control.

#### 17.2.8 What should be release-blocking in early MVP versus advisory only?

**Why it matters:**  
Some failure classes should block release immediately, while others should initially remain advisory so the team can learn without deadlocking itself.

**Impact area:**
- gate policy;
- scorecard semantics;
- rollout tempo.

#### 17.2.9 How should real beta questions be promoted into the baseline dataset?

**Why it matters:**  
Post-beta evolution of the harness will depend on a controlled intake path. Without explicit policy, noisy or anecdotal cases will pollute the dataset.

**Impact area:**
- dataset growth;
- long-term regression value;
- operational workload.

#### 17.2.10 What degree of evaluator determinism is required for regression trust?

**Why it matters:**  
If evaluator output changes unpredictably between runs, the harness will become noisy and engineering teams will stop trusting it.

**Impact area:**
- runner design;
- judging configuration;
- CI integration.

### 17.3 Optional secondary questions

These questions are less likely to block the first implementation but may become relevant quickly.

#### 17.3.1 Should the harness evaluate answer structure and clarity explicitly, or only support-bound correctness?

The MVP centers groundedness and inspectability rather than writing quality. However, some minimum readability standard may still matter if poor structure interferes with inspection.

#### 17.3.2 Should there be distinct support semantics for factual lookup versus explanatory synthesis?

A single support model may be too coarse once the dataset grows.

#### 17.3.3 How much neighbor expansion should count as retrieval success versus context assembly success?

This matters because some systems retrieve local support directly, while others rely on retrieval + neighbor expansion to create sufficient context.

#### 17.3.4 Should corpus-manifest drift be treated as a harness failure or a release-process failure?

This becomes relevant once multiple corpora or corpus versions are used concurrently.

### 17.4 Open-question operating rules

To prevent stagnation, apply the following operating rules.

#### 17.4.1 No silent assumptions
If implementation depends on an unresolved question, that dependency must be recorded somewhere visible, usually in the active workstream notes.

#### 17.4.2 Resolve by evidence, not preference
Questions should be resolved by prototype runs, annotation trials, report analysis, or user inspection evidence wherever possible.

#### 17.4.3 Promote resolved questions quickly
Once a question is resolved and the answer appears stable, promote it into the appropriate evergreen or operational artifact and remove it from the open register.

#### 17.4.4 Defer explicitly when necessary
If a question is intentionally deferred, record:
- why it is deferred;
- what temporary policy applies;
- what event or evidence should trigger reconsideration.

---

## 18. Appendices

The appendices are intentionally informative rather than normative. They exist to make the RFC easier to implement and operate without forcing every practical example into the main body.

### 18.1 Appendix A — Example evaluation case template

Below is a suggested conceptual template for an evaluation case.

```yaml
case_id: cross-doc-synth-0007
dataset_version: baseline-v1
scenario_class: cross_document_synthesis
question: >
  What constraints does the corpus place on evaluation strategy for the MVP,
  and how do those constraints affect answer behavior?
corpus_id: seed-corpus-a
corpus_subset:
  - mvp-md
  - workflow-rewrite-md
expected_support_state: sufficient
required_documents:
  - mvp-md
  - workflow-rewrite-md
gold_evidence_units:
  - doc: mvp-md
    locator:
      section_path: ["Answer Quality Expectations"]
  - doc: workflow-rewrite-md
    locator:
      section_path: ["Evaluation", "Failure Taxonomy"]
acceptable_evidence_sets:
  -
    - doc: mvp-md
      locator:
        section_path: ["Success Criteria"]
    - doc: workflow-rewrite-md
      locator:
        section_path: ["Evaluation Harness"]
citation_expectation:
  mode: document_and_section
expected_answer_behavior:
  - must mention grounded answers
  - must mention inspectable evidence
  - must mention honest abstention
expected_failure_behavior:
  - should not invent external constraints
  - should not cite non-corpus sources
tags:
  - trust-contract
  - cross-doc
  - release-relevant
notes: >
  A qualified answer is acceptable if it remains fully corpus-bounded.
```

This template is illustrative. The exact serialized form can vary.

### 18.2 Appendix B — Example failure record template

```yaml
failure_id: fail-2026-03-09-014
run_id: 2026-03-09-baseline-a
case_id: insuff-evidence-0004
layer: answer
failure_class: unsupported_synthesis
severity: high
release_blocking: true
symptom: >
  System produced a definitive answer although gold support state was insufficient.
observed_artifacts:
  - answer_debug.jsonl#case=insuff-evidence-0004
suspected_upstream_causes:
  - abstention threshold too low
  - judge incorrectly accepted partial support as sufficient
owner: answering-team
status: open
```

A normalized failure record makes regression triage much more reliable.

### 18.3 Appendix C — Example run scorecard outline

A run scorecard should be brief enough to scan but structured enough to support release decisions.

Suggested sections:
- run metadata;
- corpus and dataset versions;
- suite executed;
- top-level trust metrics;
- per-dimension metrics;
- release blockers observed;
- notable regressions versus prior baseline;
- recommended actions.

Illustrative shape:

```text
Run: 2026-03-09-baseline-a
Suite: release-v1
Corpus: seed-corpus-a@v1
Dataset: baseline-v1

Trust view
- grounded-answer rate: 0.84
- citation usefulness rate: 0.79
- insufficient-evidence correctness: 0.90
- mixed-format success rate: 0.76

Layered view
- representation: 0.81
- retrieval: 0.78
- context: 0.74
- answer: 0.83
- failure quality: 0.90

Blockers
- 2 fabricated or non-resolving citation incidents
- 1 unsupported synthesis in release suite

Recommendation
- do not promote current build to beta
- fix citation resolver and re-run release suite
```

The exact metric names and thresholds can change, but the scorecard should remain legible to engineering and product reviewers.

### 18.4 Appendix D — Example release gate review checklist

A release review can use a short checklist such as:

- Did the release suite run against the intended corpus and dataset versions?
- Are all report artifacts present and readable?
- Were any release-blocking failure classes observed?
- Are citation failures within tolerated bounds?
- Are insufficient-evidence cases handled within policy?
- Does mixed-format performance remain acceptable?
- Are any major regressions unexplained?
- Have any temporary exceptions expired?

This checklist should not replace the gate policy, but it helps operationalize it.

### 18.5 Appendix E — Example open-question register template

```yaml
question_id: oq-007
status: in_investigation
question: What is the minimum acceptable provenance granularity for PDFs?
why_it_matters: >
  Release policy depends on a stable definition of citation usefulness.
owner: principal-ai-engineer
blocking_scope: release
temporary_policy: >
  Accept page-level provenance for MVP if citation resolves and review indicates
  the page is inspectable without excessive search effort.
resolution_evidence_required:
  - annotation trial across 20 representative PDF cases
  - reviewer agreement above chosen threshold
next_review_date: 2026-03-23
```

A lightweight template like this prevents open questions from becoming informal hallway decisions.

### 18.6 Appendix F — Suggested implementation order for supporting artifacts

If the team needs a concrete order after the first two RFC fragments are accepted, use this sequence:

1. create `eval-vocabulary.md` and `eval-failure-taxonomy.md`;
2. define `corpus-manifest.json` and `eval-case.schema.json`;
3. create `scenario-catalog.md` and `annotation-guide.md`;
4. author `baseline-v1.jsonl`;
5. implement `run_eval.py` and deterministic checks;
6. emit first `summary.json` and `scorecard.md`;
7. create `eval-regressions.md` and start tracking failures;
8. expand into layered evaluators and release suites.

This order is not binding, but it is a sensible path for stepwise implementation.

### 18.7 Appendix G — Suggested assembly of the final RFC set

If these three markdown files are later consolidated into a single document, the recommended order is:

1. sections 1-10 as the normative core;
2. sections 11-15 as the operational implementation plan;
3. sections 16-18 as supporting references.

The final assembled document should still preserve the distinction between:
- normative sections;
- operational sections;
- informative appendices.

That distinction matters because implementation detail will evolve faster than semantics.

---

## Closing note

Sections 16-18 complete the RFC set by making the harness operationally legible: what artifacts should exist, what unresolved decisions remain visible, and what reference templates should be available while the system is built out iteratively.

The intent is not to over-document the harness. The intent is to make the harness durable enough that implementation can proceed step by step without losing semantic coherence, traceability, or release discipline.
