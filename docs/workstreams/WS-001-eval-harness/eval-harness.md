I would design the evaluation harness as a **trust-contract enforcement system**, not as a loose collection of answer metrics.

For this MVP, the harness has one job: prove that the system can ingest a bounded mixed-format corpus, retrieve evidence from it, answer within that evidence boundary, expose inspectable provenance, and fail honestly when support is weak. That follows directly from the MVP’s success criteria, invariants, and answer-quality expectations. 

The alternate workflow adds the right structure around that goal: evaluation should be derived from scenarios, evidence semantics, retrieval-unit semantics, and a named failure taxonomy; it should measure layered quality rather than only final answer quality; and it should pressure a thin prototype so architecture is earned from observed behavior.

## 1. Governing principles

### 1) Evaluate the contract, not the model

The primary question is not “did the LLM sound good?” It is “did the system preserve grounded behavior?” The harness should therefore treat groundedness, provenance, and abstention as first-class targets, not side checks.

### 2) Scenario-first, not metric-first

Start from concrete question classes that pressure the system end to end: factual lookup, section-scoped explanation, within-document synthesis, cross-document synthesis, source navigation, insufficient-evidence cases, and degraded-source cases. Metrics are then derived from those scenarios.

### 3) Layered evaluation

The harness must isolate failure origin across at least five layers:

* representation quality
* retrieval quality
* context quality
* answer quality
* failure quality

That is necessary because a bad answer may be caused by parsing, segmentation, retrieval, context assembly, or generation. 

### 4) Evidence is the unit of truth

The harness should evaluate support at the level of evidence units and evidence sets, not only whole answers. The workflow explicitly distinguishes sufficient, partial, and insufficient evidence; the harness should preserve that distinction. 

### 5) Abstention is a success mode

For this MVP, “I could not find enough support in the uploaded documents” is often the correct outcome. Penalizing abstention indiscriminately would train the system in the wrong direction. 

### 6) Mixed-format remains the target

The harness must always include both text PDFs and Markdown. Markdown-only can exist as a fallback diagnostic track, but not as the definition of success.

### 7) Prototype findings are durable; prototype code is not

The harness should exist early and remain stable enough to compare prototype variants. It is part of the learning instrument, not post hoc QA. 

---

## 2. What the harness should evaluate

I would split the harness into five evaluation planes.

### A. Representation evaluation

Checks whether ingestion and normalization preserved enough structure to support retrieval and inspection.

Questions:

* Did the parser recover a usable hierarchy?
* Are section paths valid?
* Are document IDs stable?
* Are anchors/provenance recoverable at MVP granularity?
* Are passage boundaries structurally sane?

This plane protects the MVP invariants around stable identity, structural integrity, and traceability.

### B. Retrieval evaluation

Checks whether the system discovers the right evidence.

Questions:

* Does top-k contain sufficient evidence?
* Does retrieval return complete support or only fragments?
* Does chunking help or destroy recall?
* Does cross-document retrieval work?

This is evidence discovery quality, not generic search relevance. 

### C. Context assembly evaluation

Checks whether retrieved evidence is assembled into usable prompt context.

Questions:

* Is ordering coherent?
* Are critical neighbors present?
* Is context redundant or bloated?
* Was necessary support truncated out?

This is where many seemingly “LLM” failures actually originate. 

### D. Answer and citation evaluation

Checks whether the answer stays within support and whether source references are usable.

Questions:

* Are claims materially correct relative to the corpus?
* Are claims supported by retrieved evidence?
* Are citations resolvable and useful?
* Does the answer overstate support?

This plane directly tests the MVP answer-quality contract.

### E. Failure-quality evaluation

Checks whether the system behaves honestly under weak or missing support.

Questions:

* Does it abstain when evidence is insufficient?
* Does it narrow scope correctly?
* Does it avoid fabricated provenance?
* Does it expose uncertainty instead of pretending completeness?

This is not optional. It is part of the product.

---

## 3. Phases

## Phase 1 — Lock the evaluation semantics

Before writing the harness runner, fix the semantic contract the harness will enforce.

Main steps:

* define scenario taxonomy
* define evidence support states: sufficient / partial / insufficient
* define what counts as a valid citation at MVP granularity
* define failure classes
* define the minimum shared eval vocabulary

Artifacts:

* `docs/evergreen/eval-principles.md`
* `docs/delivery/eval-vocabulary.md`
* `docs/delivery/eval-failure-taxonomy.md`
* `docs/delivery/eval-support-semantics.md`

Exit criteria:

* the team agrees what “supported answer,” “partial support,” and “abstain” mean
* provenance expectations are frozen for PDFs and Markdown
* major failure classes are named and non-overlapping

This phase should be short. Its purpose is to prevent every team from evaluating a different system. 

## Phase 2 — Build the scenario set

Construct a compact but representative set of end-to-end scenarios derived from the workflow.

Use these classes:

* direct factual lookup
* section-scoped explanation
* multi-passage synthesis within one document
* cross-document synthesis
* source navigation / citation resolution
* insufficient-evidence
* degraded-source / malformed-structure edge cases

Artifacts:

* `evals/scenarios/scenario-catalog.md`
* `evals/scenarios/*.md` for individual scenario definitions
* `evals/corpus/corpus-manifest.json`

Each scenario should specify:

* corpus condition
* information need
* expected evidence pattern
* expected answer behavior
* expected failure behavior

This mirrors the workflow almost exactly and gives the harness its design pressure. 

## Phase 3 — Author the baseline dataset

Create the first gold dataset by hand. Do not start with synthetic generation.

I would begin with a small but sharp set, roughly:

* 10 factual lookup
* 10 section explanation
* 8 one-document synthesis
* 8 cross-document synthesis
* 6 source navigation
* 10 insufficient-evidence
* 6 degraded-source cases

That gives you about 50–60 cases, which is enough to expose failure patterns without delaying delivery.

Each case should contain:

* `case_id`
* `scenario_class`
* `question`
* `corpus_subset`
* `expected_support_state`
* `gold_evidence_units` or `acceptable_evidence_set`
* `required_documents`
* `required provenance granularity`
* `acceptable answer constraints`
* `expected abstention behavior`
* `failure_tags`

Artifacts:

* `evals/datasets/baseline-v1.jsonl`
* `evals/datasets/annotation-guide.md`
* `evals/datasets/review-log.md`

This becomes the stable comparison surface across prototype variants.

## Phase 4 — Implement layered evaluators

Now build the actual harness.

I would implement five evaluator families.

### 4.1 Representation verifier

Checks structural outputs after ingestion.

Signals:

* hierarchy validity
* missing section paths
* anchor resolution success rate
* stable identity presence
* malformed passage distribution

Artifacts:

* `evals/runners/representation_eval.py`
* `evals/schemas/structure_snapshot.json`
* `evals/reports/representation/*.json`

### 4.2 Retrieval evaluator

Checks whether sufficient evidence appears in retrieved results.

Signals:

* evidence hit rate at k
* complete-support hit rate
* partial-vs-complete ranking error
* cross-document retrieval success
* source-nav retrieval success

Artifacts:

* `evals/runners/retrieval_eval.py`
* `evals/reports/retrieval/*.json`

### 4.3 Context evaluator

Checks assembled prompt context, not just retrieved raw hits.

Signals:

* evidence coverage in final context
* redundant overlap rate
* missing-neighbor rate
* context budget loss
* order coherence violations

Artifacts:

* `evals/runners/context_eval.py`
* `evals/reports/context/*.json`

### 4.4 Answer-support evaluator

Checks answer behavior relative to support.

Signals:

* supported-claim rate
* unsupported-claim rate
* citation resolution success
* answer overreach rate
* corpus-boundedness violations

Artifacts:

* `evals/runners/answer_eval.py`
* `evals/rubrics/answer-rubric.md`
* `evals/reports/answer/*.json`

### 4.5 Failure-quality evaluator

Checks whether the system fails correctly.

Signals:

* abstention precision
* abstention recall
* false-answer-on-insufficient-evidence rate
* fabricated-provenance incidents
* scope-narrowing correctness

Artifacts:

* `evals/runners/failure_eval.py`
* `evals/rubrics/failure-rubric.md`
* `evals/reports/failure/*.json`

The key design choice is that the harness should emit both **scores** and **failure classification**, so regressions are diagnosable rather than just “quality down.” 

## Phase 5 — Establish baselines and comparison discipline

Before optimizing, lock a few baseline system variants and compare them under the same dataset.

Examples:

* flat chunking vs section-aware chunking
* passage-only retrieval vs passage + neighbor expansion
* citation by page only vs page + inferred section path
* strict abstention vs looser answering

Artifacts:

* `evals/baselines/baseline-configs.yaml`
* `evals/reports/baseline-scorecard.md`
* `docs/workstreams/WS-XXX/eval-decisions.md`

The purpose here is not leaderboard vanity. It is to discover which design choices preserve the trust contract under pressure. 

## Phase 6 — Integrate into delivery

The harness now becomes part of the engineering loop.

I would use three lanes:

### Lane 1: local smoke eval

Very small subset, fast, run on every material change.

Purpose:

* catch obvious provenance breakage
* catch answering regressions
* catch serialization/schema drift

### Lane 2: full offline regression

Run on every merge to main or nightly.

Purpose:

* compare variants
* inspect failure taxonomy shifts
* keep score histories

### Lane 3: release gate eval

Smaller curated release pack with strict thresholds.

Purpose:

* enforce no-regression on trust metrics
* validate mixed-format performance
* validate insufficient-evidence behavior

Artifacts:

* `evals/suites/smoke.txt`
* `evals/suites/full.txt`
* `evals/suites/release.txt`
* CI workflow files
* `evals/reports/history/*.json`

## Phase 7 — Beta shadow evaluation

Once beta starts, capture real user queries and convert a subset into reviewed eval cases.

Rules:

* do not immediately promote raw user questions into the gold set
* review and annotate them
* tag new failure modes
* only then add them to `baseline-vNext`

Artifacts:

* `evals/intake/beta-query-log.jsonl`
* `evals/intake/candidate-cases.md`
* `evals/datasets/baseline-v2.jsonl`

This is how the harness remains grounded in actual usage without becoming noisy or unstable.

---

## 4. Minimum artifact set

If I were making this concrete today, I would require this minimum set:

**Evergreen**

* `docs/evergreen/eval-principles.md`
* `docs/delivery/eval-vocabulary.md`
* `docs/delivery/eval-failure-taxonomy.md`
* `docs/delivery/eval-support-semantics.md`

**Scenario and dataset**

* `evals/scenarios/scenario-catalog.md`
* `evals/datasets/baseline-v1.jsonl`
* `evals/datasets/annotation-guide.md`
* `evals/corpus/corpus-manifest.json`

**Rubrics**

* `evals/rubrics/representation-rubric.md`
* `evals/rubrics/retrieval-rubric.md`
* `evals/rubrics/context-rubric.md`
* `evals/rubrics/answer-rubric.md`
* `evals/rubrics/failure-rubric.md`

**Execution**

* `evals/runners/*.py`
* `evals/configs/*.yaml`
* `evals/suites/{smoke,full,release}.txt`

**Outputs**

* `evals/reports/<date>/summary.json`
* `evals/reports/<date>/failures.jsonl`
* `evals/reports/<date>/scorecard.md`

**Temporal workstream**

* `docs/workstreams/WS-XXX/eval-decisions.md`
* `docs/workstreams/WS-XXX/eval-regressions.md`

---

## 5. Scoring model

I would not collapse everything into a single number at first.

Use a scorecard with five top-level dimensions:

* representation
* retrieval
* context
* answer
* failure

And one release-oriented trust view:

* grounded-answer rate
* citation usefulness rate
* insufficient-evidence correctness
* mixed-format success rate

A system can have strong factual accuracy and still fail the MVP if provenance is weak or it answers confidently on insufficient support. The scorecard must make that visible.

---

## 6. Ownership model

The evaluation harness should be a bounded context with real ownership, not a side utility. The workflow explicitly names Evaluation / Verification as a candidate bounded context because semantic drift between parsing, retrieval, citation, and answering is otherwise easy to miss. 

In practice:

* ingestion/parsing owns representation metrics
* retrieval owns retrieval metrics
* answer pipeline owns answer/failure metrics
* one cross-cutting owner owns dataset integrity, rubrics, and release scorecards

Without that, each subsystem will optimize its own local success condition and the end-to-end product will still drift.

---

## 7. First release gate I would enforce

Before calling the MVP “working,” I would require that the release suite demonstrates:

* mixed PDF + Markdown cases pass at useful rates
* source references resolve at MVP granularity
* insufficient-evidence cases mostly abstain or narrow scope correctly
* cross-document synthesis works in a limited but real subset
* regressions are classifiable by failure taxonomy rather than anecdotal inspection

That gate is directly aligned with the MVP’s definition of success.

My recommendation: treat the evaluation harness as one of the first implementation tracks, not something added after the prototype. The workflow already points in that direction, and for this product that is the correct order.
