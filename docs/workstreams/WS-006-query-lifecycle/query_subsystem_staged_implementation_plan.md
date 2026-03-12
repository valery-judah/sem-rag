# Staged Implementation and Delivery Plan for `07_design.md`

**Status:** Draft  
**Applies to:** MVP / Version 1  
**Last updated:** 2026-03-11

## Purpose

This document translates `07_design.md` into an implementation and delivery sequence that a coding agent can execute incrementally without collapsing the intended semantics of the query subsystem.

The goal is not to implement a generic "chat over files" loop quickly. The goal is to implement the explicit query lifecycle in a way that preserves the MVP trust contract:

- only `READY` documents are queryable;
- each query executes against a stable corpus snapshot;
- evidence is explicit rather than implicit prompt context;
- support assessment is first-class;
- answer posture is policy-driven rather than model-improvised;
- citations derive from stored provenance rather than model invention;
- traces are durable enough for debugging, replay, and evaluation.

This plan assumes the document lifecycle is already implemented and available as the upstream system of record.

---

## Related authoritative inputs

This staged plan should be read in the following authority order:

1. `mvp.md`
2. `07_design.md`
3. `eval-vocabulary.md`
4. `eval-support-semantics.md`
5. `21_critical_failures.md`
6. `workflow.md`
7. `21-design-exploration.md`

When these documents differ in emphasis:

- `mvp.md` governs product scope and trust guarantees;
- `07_design.md` governs the intended query architecture and runtime path;
- `eval-support-semantics.md` governs support-state and abstention behavior;
- `21_critical_failures.md` governs release-relevant failure priorities;
- `workflow.md` governs the modeling-first delivery posture.

---

## Design commitments this plan preserves

The query subsystem must preserve the normative runtime path from `07_design.md`:

`Interpret -> Retrieve -> Select -> Assemble Context -> Assess Support -> Decide Answer Mode -> Generate -> Cite or Abstain`

The staged implementation plan treats that path as binding runtime structure, not as explanatory prose.

In particular:

- `Assess Support` must remain a first-class stage.
- `Decide Answer Mode` must remain explicit and policy-driven.
- Later stages may preserve or narrow posture, but must not widen it.
- Only `READY` documents may participate in answering.
- Each query must run against a stable corpus snapshot.

---

## Delivery philosophy

Use staged vertical delivery with hard acceptance gates.

Each stage must produce:

- runnable code;
- explicit tests;
- observable trace artifacts;
- no semantic regressions against earlier invariants.

Do not let later stages force rewrites of earlier contracts unless a contract is clearly wrong.

The delivery posture should stay model-first rather than architecture-first:

- freeze semantics early;
- keep infrastructure simple;
- use implementation pressure to validate seams;
- prefer inspectable deterministic policy over hidden prompt behavior.

---

## Global target architecture to grow toward

The final MVP query subsystem should provide:

- one FastAPI service;
- one Postgres database;
- reuse of the existing document lifecycle read surface;
- explicit query lifecycle stages;
- durable query traces;
- support-state-aware grounded answering;
- provenance-derived citations;
- evaluation hooks tied to trust failures.

The coding sequence below introduces that architecture in a controlled order.

## Current delivery snapshot

As of 2026-03-11, the repo has completed the staged path through Stage 7:

- Stage 0: contracts, enums, policy defaults, and scaffolding
- Stage 1: queryable `READY`-corpus boundary and stable corpus snapshots
- Stage 2: deterministic interpretation and durable `interpret` traces
- Stage 3: snapshot-scoped dense retrieval and durable `retrieve` traces
- Stage 4: deterministic selection/evidence-set construction and durable `select` traces
- Stage 5: deterministic context assembly with inspectable `ContextManifest` output and durable `assemble_context` traces
- Stage 6: support assessment and answer-mode policy with durable `assess_support` and `decide_answer_mode` traces
- Stage 7: grounded generation, citation rendering, and durable final answer persistence

The current implementation gap begins at Stage 8:

- review-oriented read surfaces
- replay foundation
- structured JSON operational logging
- later evaluation hardening

---

# Stage 0 — Freeze contracts and scaffolding

## Goal

Create the minimum internal structure needed so later implementation does not collapse into ad hoc retrieval-plus-generation logic.

## Why this stage exists

Without this stage, the coding agent will likely implement a direct `/queries` endpoint with retrieval and generation fused together. That would violate `07_design.md` before the subsystem is even bootstrapped.

Detailed repo-facing design for this stage lives in `10_stage-0-foundation-design.md`.

## Deliverables

### 0.1 Query package skeleton

Create the initial package structure aligned to the design:

```text
src/<app>/
  query/
    service.py
    policies.py
    errors.py
    contracts.py
    persistence.py
    domain.py
    trace.py
    stages/
      interpret.py
      retrieve.py
      select.py
      evidence_sets.py
      context.py
      assess_support.py
      decide_answer_mode.py
      generate.py
      render_citations.py
  readmodels/
    documents.py
  inference/
    embeddings.py
    llm.py
    schemas.py
```

Early on, `contracts.py`, `domain.py`, and `persistence.py` may remain consolidated. Split only when real pressure appears.

### 0.2 Core semantic objects

Define stable internal objects for at least:

- `QueryRequest`
- `QueryRun`
- `CorpusSnapshot`
- `InterpretedQuery`
- `RetrievedCandidate`
- `EvidenceUnit`
- `EvidenceSet`
- `ContextManifest`
- `SupportAssessment`
- `AnswerModeDecision`
- `AnswerDraft`
- `CitationBundle`

### 0.3 Enumerations and invariant constants

Define enums or equivalent constants for:

- query run status;
- stage names;
- support states;
- answer modes;
- primary trust failure labels.

### 0.4 Central policy object

Create a canonical `QueryPolicy` / `QueryPolicyDefaults` object for:

- retrieval candidate count;
- evidence-set limits;
- neighbor expansion policy;
- duplicate suppression policy;
- context budget;
- deterministic tie-break order;
- support-state to answer-mode mapping;
- citation rendering defaults.

Do not leave these embedded in prompt text.

## Acceptance gate

This stage is done when:

- the repo has stable query-domain scaffolding;
- the core contracts compile and serialize cleanly;
- there is one canonical place for query-time defaults;
- tests verify enum values and support-state to answer-mode mapping tables exist.

## Coding-agent notes

- Do not implement real retrieval or LLM calls yet.
- Do not create transport-first DTO sprawl.
- Optimize for semantic clarity of internal contracts.

---

# Stage 1 — Queryable corpus boundary and document read model

## Goal

Make the query subsystem capable of reading a stable queryable corpus from the document lifecycle without owning document mutation.

## Why this stage exists

`READY` is the hard boundary for queryability. If this rule is not implemented first, every downstream behavior becomes semantically unstable.

## Deliverables

### 1.1 Read-only document read model adapter

Implement a read model over document-lifecycle persistence that can:

- list `READY` documents for a workspace;
- return the query-time corpus snapshot;
- expose sections and chunks with provenance-bearing metadata;
- expose heading or section path data;
- expose only query-relevant fields, not raw lifecycle internals.

### 1.2 Corpus snapshot capture

Implement a `CorpusSnapshot` artifact for each query run containing at minimum:

- workspace id;
- query start timestamp;
- list of eligible `doc_id`s;
- optional retrieval/index version markers if available.

### 1.3 Query-time boundary validation

Implement preflight validation logic for:

- workspace existence;
- visibility / ownership boundary;
- `READY`-only eligibility filtering;
- explicit handling of empty but valid corpus snapshots.

### 1.4 Minimal `/queries` path

Implement a thin internal endpoint that:

- accepts question + workspace id;
- captures a query run record;
- captures the corpus snapshot;
- returns a stub response while downstream stages remain placeholders.

## Tests

- query snapshot excludes non-`READY` documents;
- documents entering `READY` after query start are not included in an existing run;
- empty workspace snapshot is represented explicitly rather than as an exception;
- read model returns provenance-bearing chunks only.

## Acceptance gate

This stage is done when:

- the system can persist a query run with a stable snapshot;
- the query subsystem can only see `READY` documents;
- snapshot behavior is deterministic and test-covered.

## Coding-agent notes

- Keep this adapter read-only.
- Do not query raw artifact files directly from query logic.
- Do not leak lifecycle table shapes into query stage code.

---

# Stage 2 — Interpretation foundation

## Goal

Establish structured query interpretation as an explicit runtime contract before retrieval begins.

## Why this stage exists

`07_design.md` makes `Interpret` the first semantic stage after intake. If retrieval is implemented first, the subsystem will drift toward raw-query search and collapse the intended runtime backbone.

Detailed repo-facing design for this stage lives in `12_stage-2-interpretation-foundation-design.md`.

## Deliverables

### 2.1 Interpretation stage

Implement one structured LLM call with strict schema for:

- request type;
- answer-shape implications;
- scope and specificity;
- likely source-navigation intent;
- likely synthesis intent;
- obvious unsupported-question-type signals.

Follow with deterministic normalization and policy checks.

### 2.2 Stable `InterpretedQuery` contract

Define and persist an `InterpretedQuery` shape that later stages can consume without lossy translation.

### 2.3 Interpretation stage trace

Persist the interpretation payload including:

- the normalized `InterpretedQuery`;
- policy flags or unsupported-question-type signals;
- model/schema version metadata where relevant.

### 2.4 Endpoint integration

`POST /queries` should now run:

`boundary validation -> interpret -> persist interpretation trace -> return temporary developer-visible response`

## Tests

- interpretation preserves distinctions among factual lookup, explanation, synthesis, source navigation, and unsupported question type;
- normalization is deterministic for equivalent requests;
- interpreted-query artifacts serialize cleanly and are traceable;
- empty but valid corpus state does not bypass interpretation.

## Acceptance gate

This stage is done when:

- the system has an explicit interpreted-query contract;
- retrieval can be implemented downstream of interpretation rather than against raw request text alone;
- every query run has a persisted interpretation trace.

## Coding-agent notes

- Interpretation is not support assessment.
- Keep the schema constrained and inspectable.
- Do not bypass this stage by letting downstream stages depend semantically on raw request text.

---

# Stage 3 — Retrieval foundation with provenance-preserving candidates

## Goal

Implement the first real evidence discovery path using dense passage retrieval over the query-time snapshot, explicitly downstream of `InterpretedQuery`.

## Why this stage exists

Retrieval is the first place where the subsystem produces candidate evidence. It must preserve identity and provenance before any support reasoning can be trustworthy, and it must consume the interpreted query contract rather than stand in for it.

Detailed repo-facing design for this stage lives in `13_stage-3-retrieval-foundation-design.md`.

## Deliverables

### 3.1 Query embedding adapter

Implement a narrow embeddings interface for the retrieval-ready query representation derived from `InterpretedQuery`.

### 3.2 Dense-first passage retrieval

Implement retrieval that:

- searches only within the query-time snapshot;
- takes `InterpretedQuery` as the primary semantic input;
- returns passage-level candidates;
- preserves `doc_id`, `chunk_id`, `section_id`, `heading_path`, locator data, score, and rank;
- performs no external search.

Raw query text may remain available only as a bootstrap diagnostic fallback during retrieval investigation, not as the intended runtime contract.

### 3.3 Stable retrieval candidate contract

Define and persist a candidate shape that later stages can consume without lossy translation.

### 3.4 Retrieval stage trace

Persist the retrieval stage payload including:

- candidate list;
- ranks and scores;
- interpreted-query reference;
- snapshot id or embedded snapshot reference;
- retrieval config used.

### 3.5 Endpoint integration

`POST /queries` should now run:

`boundary validation -> interpret -> retrieve -> persist interpretation/retrieval traces -> return temporary developer-visible response`

## Tests

- retrieval never returns a chunk outside the captured snapshot;
- candidate objects always include provenance-bearing fields;
- retrieval over a fixture corpus returns expected passage matches in at least basic cases;
- retrieval on empty snapshot returns a valid empty candidate list.

## Acceptance gate

This stage is done when:

- retrieval is real, bounded, and traceable;
- candidate identity and provenance are stable;
- retrieval is explicitly downstream of `InterpretedQuery`;
- every query run has a persisted retrieval trace.

## Coding-agent notes

- Do not implement reranking here.
- Do not collapse retrieval output into prompt text.
- Keep retrieval output as structured candidates.

---

# Stage 4 — Selection and evidence-set construction

## Goal

Convert retrieved candidates into explicit supportable evidence structures instead of raw top-k text dumps.

## Why this stage exists

The design explicitly rejects naive top-k prompting. This stage is the bridge from search results to supportable evidence.

Detailed repo-facing design for this stage lives in `14_stage-4-selection-evidence-set-construction-design.md`.

## Deliverables

### 4.1 Heuristic reranking / selection stage

Implement deterministic heuristic reranking using signals such as:

- closeness to interpreted query;
- heading/path relevance;
- local coherence potential;
- candidate completeness;
- source-navigation precision;
- provenance quality;
- synthesis diversity when needed.

### 4.2 Duplicate suppression

Implement deterministic duplicate and near-duplicate suppression.

### 4.3 Neighbor expansion policy

Implement limited adjacent-passage expansion where local coherence matters.

### 4.4 Evidence-set builder

Implement MVP evidence grouping modes:

- single-passage support;
- passage plus neighbor support;
- same-document multi-passage grouping;
- small cross-document grouping for clear synthesis cases.

### 4.5 Selection and evidence-set traces

Persist structured outputs for:

- selected candidates;
- dropped candidates and why;
- evidence-set membership;
- grouping rationale.

## Tests

- duplicate suppression is deterministic;
- neighbor expansion stays within allowed policy bounds;
- explanation queries can group multiple passages from one document;
- synthesis grouping does not create oversized or incoherent evidence bundles.

## Acceptance gate

This stage is done when:

- selection is explicit and traceable;
- evidence sets exist as first-class runtime objects;
- the system no longer depends on naive raw top-k prompt assembly.

## Coding-agent notes

- Keep reranking heuristic and inspectable for MVP.
- Do not add neural rerankers yet.
- Do not make raw query text part of the semantic primary path for selection; treat it as retrieval-stage diagnostics only if needed.
- Prefer conservative grouping over aggressive synthesis.

---

# Stage 5 — Deterministic context assembly

**Status:** Implemented on 2026-03-11

## Goal

Build a deterministic, inspectable model-facing context from explicit evidence sets.

## Why this stage exists

Context assembly determines what the generator actually sees. It should remain its own stage so inclusion, ordering, and truncation are inspectable rather than disappearing into interpretation or generation.

## Deliverables

### 5.1 Context assembly stage

Build a deterministic `ContextManifest` that:

- orders evidence sets explicitly;
- tracks token budget consumption;
- preserves headings and source-local scaffolding when useful;
- suppresses near-duplicates;
- drops lower-value evidence sets first when over budget;
- records inclusion and exclusion reasons.

The unit of truncation should normally be the lower-value evidence set, not arbitrary clipping through already selected support.

### 5.2 Context trace

Persist the context-assembly output as a structured artifact.

### 5.3 Temporary developer-visible response

Until answer generation is implemented, allow an internal debug response mode that returns:

- interpreted query summary;
- selected evidence sets;
- context manifest.

## Tests

- context ordering is deterministic;
- budget overflow drops lower-priority evidence sets first;
- context manifest always references included evidence set ids.

## Acceptance gate

This stage is done when:

- the final model-facing context is structured and inspectable;
- context inclusion/exclusion decisions are persisted.

This acceptance gate is now satisfied in the repo through:

- executable Stage 5 context assembly in `src/parity/query/context_assembly.py` and `src/parity/query/stages/context.py`;
- `QueryService.execute_until_context_assembly()` orchestration;
- internal `POST /queries` responses that include `context_manifest`;
- Stage 5 trace persistence in `query_stage_traces`;
- focused contract, query, and route coverage.

## Coding-agent notes

- Context assembly is not answer generation.
- Keep this stage separate from interpretation even if both are implemented close together.

---

# Stage 6 — Support assessment and answer-mode policy

## Goal

Implement the trust-critical center of the subsystem: evidence sufficiency judgment and posture control.

## Why this stage exists

This is the main semantic difference between a trustworthy RAG system and a prompt chain that answers whenever it can.

## Deliverables

### 6.1 Support assessment stage

Implement a hybrid stage with:

- deterministic pre-checks for unsupported question types, empty evidence, and obvious provenance insufficiency;
- structured LLM judgment over interpreted query, evidence sets, and context manifest;
- deterministic post-rules that can preserve or narrow support, but never widen it.

Support states must align to the live semantics:

- `SUFFICIENT`
- `PARTIAL`
- `INSUFFICIENT`

### 6.2 Answer-mode decision stage

Implement deterministic policy mapping from support state plus qualifying reasons to allowed answer posture.

Supported answer modes should include at least:

- direct answer;
- narrowed answer;
- qualified answer;
- full abstention;
- scoped abstention;
- qualified uncertainty.

### 6.3 Stage traces

Persist:

- support assessment output;
- qualifying reasons;
- answer mode decision;
- policy version / config snapshot.

### 6.4 Failure-label hooks

Attach provisional primary trust-failure labels when obvious, such as:

- unsupported answer risk (`U1`);
- partially supported answer presented as complete risk (`U2`);
- wrong abstention risk (`A1`);
- failed abstention risk (`A2`);
- provenance too weak risk (`P1`);
- incorrect provenance risk (`P2`);
- scope-boundary failure risk (`S1`).

## Tests

- empty evidence cannot yield direct answer mode;
- unsupported question types cannot yield direct answer mode;
- partial support cannot widen to direct complete answer mode;
- deterministic post-rules can only preserve or narrow posture;
- answer-mode mapping is testable without invoking generation.

## Acceptance gate

This stage is done when:

- support is judged explicitly rather than implicitly by generation;
- answer posture is selected by policy logic;
- unsupported or partial-support cases are first-class and test-covered.

## Coding-agent notes

- Do not hide answer-mode choice in the generation prompt.
- Do not let the LLM invent new support states.
- Keep the policy mapping deterministic and versionable.

---

# Stage 7 — Grounded generation and citation rendering

## Goal

Produce final user-visible answers and citations without allowing hidden support widening or fabricated provenance.

## Why this stage exists

Only after support and posture are explicit can generation be safely introduced.

## Deliverables

### 7.1 Grounded generation stage

Implement one generation call that consumes:

- interpreted query;
- context manifest;
- support assessment;
- answer mode;
- visible limitation guidance.

Generation rules:

- supported content may be paraphrased;
- synthesis only when support covers it;
- partial support must remain visible;
- conflicting evidence must not be flattened into false consensus;
- unsupported gaps must not be silently filled.

### 7.2 Citation rendering stage

Derive citations from stored provenance, not from the generation model.

Implement citation objects that can represent:

- contributing `doc_id`;
- heading path or section path when available;
- page range or coarse locator when available;
- citation support role;
- multi-source bundles where needed.

### 7.3 Final answer persistence

Persist:

- answer text;
- support state;
- qualifying reasons;
- answer mode;
- visible limitations;
- citations.

### 7.4 Complete `/queries` response

Return:

- `query_id`;
- `answer`;
- `support_state`;
- `answer_mode`;
- `visible_limitations`;
- `citations`.

## Tests

- generation cannot return citations invented by the model;
- citation locators resolve only to stored provenance;
- partial-support answers include visible qualification;
- unsupported question types surface limitation language instead of fabricated answers;
- multi-source synthesis returns multi-source citation bundles when materially required.

## Acceptance gate

This stage is done when:

- the system can answer end to end over `READY` documents;
- citations are derived from provenance-bearing evidence objects;
- abstention and narrowing behaviors are visible in final answers.

## Coding-agent notes

- Keep generation constrained to supportable evidence only.
- Fail closed on missing citation provenance.
- Do not let answer fluency outrank support fidelity.

---

# Stage 8 — Trace persistence, review endpoints, and replay foundation

## Goal

Make query runs inspectable and observable enough for debugging, regression analysis, and evaluation.

## Why this stage exists

A grounded answer is not trustworthy if the team cannot inspect why it happened.

Detailed repo-facing design for this stage lives in `18_stage-8-trace-review-replay-logging-design.md`.

## Deliverables

### 8.1 Persistence read-side completion

Extend the existing persistence model with a bias toward structured JSON review artifacts:

- keep `query_runs`, `query_snapshots`, `query_stage_traces`, and `query_answers` as the primary durable query records;
- add only minimal terminal-state fields needed for summary/failure inspection;
- do not split citation or retrieval-debug payloads into extra tables unless review pressure proves it necessary.

### 8.2 Review endpoints

Implement internal endpoints:

- `GET /queries/{query_id}`
- `GET /queries/{query_id}/trace`
- `GET /queries/{query_id}/citations`

### 8.3 Replay foundation

Implement replay first as an internal service/test primitive rather than a required public HTTP feature.

### 8.4 Diagnostic utilities

Add review helpers for:

- stage timing;
- candidate inspection;
- evidence-set inspection;
- context manifest inspection;
- support and answer-mode decision review.

### 8.5 Structured JSON logging

Add live operational logging that is distinct from persisted traces:

- emit one JSON log event per line to stdout;
- bind request and query correlation ids;
- log stage lifecycle, completion, and failure events;
- keep detailed evidence artifacts in trace persistence rather than duplicating them in logs.

## Tests

- every successful query has a full trace chain;
- every stage trace is linked to the owning query run;
- citations endpoint is derived from persisted answer/citation state rather than recomputed ad hoc;
- replay can reconstruct a prior run's stage inputs from persisted artifacts.
- JSON log output is structured, correlated, and bounded.

## Acceptance gate

This stage is done when:

- a reviewer can inspect how a query answered or abstained;
- retrieval, support, and citation defects are localizable;
- live query execution is observable through correlated structured logs;
- the subsystem is evaluation-ready rather than demo-only.

## Coding-agent notes

- Prefer structured JSON payloads over premature relational decomposition.
- Treat logs and durable traces as separate observability surfaces.
- Keep trace payloads stable enough for regression tooling.
- Do not defer trace persistence until after "the core works." The trace is part of the core.

---

# Stage 9 — Evaluation hardening and release gates

## Goal

Move from "it runs" to "it meets the MVP trust contract."

## Why this stage exists

The subsystem should not be considered complete until it is measured against the project's explicit support, citation, and failure semantics.

## Deliverables

### 9.1 Stage-level tests

Add isolated tests for:

- interpretation;
- retrieval;
- selection;
- evidence-set building;
- context assembly;
- support assessment;
- answer-mode decision;
- citation rendering.

### 9.2 End-to-end scenario suite

Cover at least:

- direct factual lookup;
- section-scoped explanation;
- one-document synthesis;
- limited cross-document synthesis;
- unsupported-in-corpus;
- unsupported-question-type;
- ambiguous/conflicting evidence;
- provenance-sensitive navigation.

### 9.3 Failure-oriented suite

Track at minimum:

- unsupported answer (`U1`);
- partially supported answer presented as complete (`U2`);
- wrong abstention (`A1`);
- failed abstention (`A2`);
- provenance missing or too weak (`P1`);
- incorrect provenance (`P2`);
- ingestion/structure defect visible at query time (`I1`);
- scope-boundary failure (`S1`).

### 9.4 Release gates

Require that no change can increase:

- unsupported answers;
- failed abstentions;
- incorrect provenance;
- scope-boundary dishonesty.

without explicit review and justification.

## Acceptance gate

This stage is done when:

- the subsystem is measured against the same trust semantics as the rest of the project;
- failure categories are visible in evaluation output;
- changes can be judged as regressions or improvements.

## Coding-agent notes

- Do not optimize only for answer rate.
- Treat unsupported answers and false provenance as release-blocking classes.
- Keep scenario and failure slices visible in test reporting.

---

# Milestone grouping

If you want fewer, larger milestones for the coding agent, use this grouping.

## Milestone A — Query boundary and interpretation foundation

Includes Stages 0, 1, and 2.

Outcome:

- query runs exist;
- corpus snapshots are stable;
- interpreted queries are explicit and traceable.

## Milestone B — Retrieval, evidence structuring, and context path

Includes Stages 3, 4, and 5.

Outcome:

- retrieval is explicitly downstream of `InterpretedQuery`;
- raw retrieval is converted into evidence sets and deterministic context manifests.

## Milestone C — Trust decision path

Includes Stage 6.

Outcome:

- support assessment and answer-mode policy are explicit and testable.

## Milestone D — End-to-end answer delivery

Includes Stage 7.

Outcome:

- the system can answer, narrow, qualify, abstain, and cite end to end.

## Milestone E — Reviewability and hardening

Includes Stages 8 and 9.

Outcome:

- the subsystem is inspectable, replayable, and gateable by failure-oriented evals.

---

# Order constraints that must not be violated

1. Do not implement retrieval before interpretation exists as an explicit stage contract.
2. Do not implement final answer generation before support assessment and answer-mode policy exist.
3. Do not implement citation rendering from model text.
4. Do not let retrieval read directly from "latest ready docs" after query start; use the captured snapshot.
5. Do not substitute section retrieval for passage-first retrieval in MVP.
6. Do not skip evidence-set construction and dump top-k passages straight into generation as the default architecture.
7. Do not treat empty evidence as a soft prompt hint; handle it as a first-class support signal.
8. Do not make replay or trace inspection impossible by over-compressing stage outputs.

---

# Minimal MVP defaults to freeze early

These values may change later, but they must be explicit before serious implementation proceeds:

- dense-first retrieval only;
- passage-first retrieval unit;
- deterministic tie-break ordering;
- explicit candidate cap;
- explicit evidence-set cap;
- explicit context budget;
- limited neighboring-passage expansion;
- deterministic duplicate suppression;
- support-state-driven answer posture;
- provenance-derived citation rendering;
- internal HTTP surface only.

---

# Suggested coding-agent execution template per stage

For each stage, instruct the coding agent to deliver in this order:

1. update or create internal domain contracts;
2. implement the stage service logic;
3. persist the stage trace payload;
4. wire the stage into `query/service.py` orchestration;
5. add focused unit/contract tests;
6. add one end-to-end fixture test;
7. document stage invariants and likely failure modes near the code.

That sequence keeps delivery incremental while preserving inspectability.

---

# Definition of done for the subsystem

The query subsystem is only done for MVP when all of the following are true:

- it answers only from the active query-time corpus snapshot;
- it treats support state as an explicit semantic object rather than a generation side effect;
- it can narrow, qualify, or abstain according to explicit policy;
- it returns inspectable citations derived from stored provenance;
- it persists enough trace state to explain why it answered or abstained;
- it is evaluated against the primary trust failures rather than raw answer rate alone.

---

# Final recommendation

Build the query subsystem in this strict order:

1. scaffold contracts and policy defaults;
2. enforce `READY`-snapshot query boundaries;
3. implement structured interpretation;
4. implement provenance-preserving retrieval;
5. implement selection and evidence sets;
6. implement deterministic context assembly;
7. implement support assessment and answer-mode policy;
8. implement grounded generation and citation rendering;
9. implement trace/review surfaces and evaluation hardening.

That is the shortest path to a working system that still respects `07_design.md` rather than accidentally replacing it with a simpler but semantically weaker architecture.

Repo truth as of 2026-03-11 has completed steps 1 through 6 in this sequence.
The next stage to execute is step 7: support assessment and answer-mode policy.
