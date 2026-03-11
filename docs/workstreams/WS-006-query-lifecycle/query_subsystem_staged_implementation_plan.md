# Staged Implementation and Delivery Plan for `07_design.md`

## Purpose

This plan translates `07_design.md` into an implementation sequence that a coding agent can execute incrementally without collapsing the intended semantics of the query subsystem.

The goal is not to implement “chat over files” quickly. The goal is to implement the explicit query lifecycle in a way that preserves the MVP trust contract:

- only `READY` documents are queryable;
- each query executes against a stable corpus snapshot;
- evidence is explicit rather than implicit prompt context;
- support assessment is first-class;
- answer posture is policy-driven rather than model-improvised;
- citations come from stored provenance rather than model invention;
- traces are durable enough for debugging, evaluation, and replay.

This plan assumes the document lifecycle is already implemented and available as the upstream system of record.

---

## Guiding implementation rules

1. Do not skip semantic stages just because one prompt can do more in a demo.
2. Keep one FastAPI service, one Postgres database, and the existing artifact storage split.
3. Build thin vertical slices early, but keep stage boundaries explicit in code and persisted traces.
4. Prefer deterministic policy code wherever trust semantics depend on it.
5. Keep inference adapters replaceable and subordinate to stage contracts.
6. Prefer JSON stage traces over premature relational normalization.
7. Use the existing document lifecycle as a read-only dependency; do not duplicate document ownership logic inside query.
8. Treat unsupported or partial support behavior as a primary success path, not as an error case.

---

## Global target architecture to grow toward

The final MVP query path should remain:

`Interpret -> Retrieve -> Select -> Evidence Sets -> Assemble Context -> Assess Support -> Decide Answer Mode -> Generate -> Render Citations`

The coding sequence below intentionally does **not** implement everything at once. It introduces this path in stages while keeping each earlier stage compatible with the final design.

---

## Delivery strategy

Use staged vertical delivery with hard acceptance gates.

Each stage should produce:

- runnable code;
- explicit tests;
- observable trace artifacts;
- no semantic regressions against earlier invariants.

Do not let later stages force rewrites of earlier contracts unless a contract is clearly wrong.

---

# Stage 0 — Freeze contracts and establish scaffolding

## Goal

Create the minimal structural scaffolding so later implementation does not drift into ad hoc prompt orchestration.

## Why this stage exists

Without this stage, the coding agent will likely implement a direct `/queries` endpoint with retrieval and generation fused together. That would violate the design before the subsystem is even bootstrapped.

## Deliverables

### 0.1 Package layout skeleton

Create the initial package structure aligned to the design, but keep files few and substantial.

Suggested starting layout:

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

Early in implementation, `contracts.py`, `domain.py`, and `persistence.py` may stay consolidated. Split only when pressure is real.

### 0.2 Core domain contracts

Define the minimum stable internal objects:

- `QueryRequest`
- `QueryRun`
- `CorpusSnapshot`
- `InterpretedQuery`
- `RetrievalCandidate`
- `EvidenceSet`
- `ContextManifest`
- `SupportAssessment`
- `AnswerMode`
- `GeneratedAnswer`
- `RenderedCitation`

### 0.3 Enumerations and invariant constants

Define enums or equivalent constants for:

- query run status
- support state
- answer mode
- stage names
- primary query failure labels

### 0.4 Policy object

Create a central `QueryPolicy` / `QueryPolicyDefaults` object that holds explicit defaults for:

- retrieval candidate count
- evidence set limits
- neighbor expansion policy
- duplicate suppression policy
- context budget
- tie-break order
- support-state to answer-mode mapping
- citation rendering defaults

Do **not** leave these embedded in prompt text.

## Acceptance gate

This stage is done when:

- the repo has stable query-domain scaffolding;
- the core contracts compile and serialize cleanly;
- there is one canonical place for query-time defaults;
- tests verify enum values and support-state to answer-mode mapping tables exist.

## Coding-agent instructions

- Do not implement real retrieval or LLM calls yet.
- Do not create transport-first DTO sprawl.
- Optimize for semantic clarity of the internal contracts.

---

# Stage 1 — Queryable corpus boundary and document read model

## Goal

Make the query subsystem capable of reading a stable queryable corpus from the document lifecycle without owning document mutation.

## Why this stage exists

The design makes `READY` the hard boundary for queryability. If this rule is not implemented first, every downstream behavior becomes semantically unstable.

## Deliverables

### 1.1 Read-only document read model adapter

Implement a read model over document-lifecycle persistence that can:

- list `READY` documents for a workspace;
- return the query-time corpus snapshot;
- expose chunks with provenance-bearing metadata;
- expose section and heading path data;
- expose only query-relevant fields, not raw lifecycle internals.

### 1.2 Corpus snapshot capture

Implement a `CorpusSnapshot` artifact for each query run containing, at minimum:

- workspace id
- query start time
- list of eligible `doc_id`s
- optional retrieval/index version markers if available

### 1.3 Query-time boundary validation

Implement preflight validation logic for:

- workspace existence
- visibility / ownership boundary
- non-empty or empty-but-valid corpus snapshot
- `READY`-only eligibility filtering

### 1.4 Minimal `/queries` request path

Implement a thin internal endpoint that:

- accepts a user question and workspace id;
- captures a query run record;
- captures the corpus snapshot;
- returns a temporary stub response while downstream stages are still placeholders.

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

## Coding-agent instructions

- Keep this adapter read-only.
- Do not query raw artifact files directly from query logic.
- Do not leak lifecycle table shapes into query stage code.

---

# Stage 2 — Retrieval skeleton with provenance-preserving candidates

## Goal

Implement the first real evidence discovery path using dense passage retrieval over the query-time snapshot.

## Why this stage exists

Retrieval is the first place where the subsystem produces candidate evidence. It must preserve identity and provenance before any support reasoning can be trustworthy.

## Deliverables

### 2.1 Query embedding adapter

Implement a narrow embeddings interface for query text.

### 2.2 Dense-first passage retrieval

Implement retrieval that:

- searches only within the query-time snapshot;
- returns passage-level candidates;
- preserves `doc_id`, `chunk_id`, `section_id`, `heading_path`, locator data, score, and rank;
- performs no external search.

### 2.3 Retrieval candidate contract

Define and persist a stable candidate shape. It must support later selection, evidence grouping, and citation rendering without re-querying unrelated stores.

### 2.4 Retrieval stage trace

Persist the retrieval stage payload, including:

- candidate list
- ranks and scores
- snapshot id or embedded snapshot reference
- retrieval config used

### 2.5 Minimal retrieval-stage endpoint integration

`POST /queries` should now run:

`boundary validation -> retrieve -> persist retrieval trace -> return stub or temporary developer response`

## Tests

- retrieval never returns a chunk outside the captured snapshot;
- candidate objects always include provenance-bearing fields;
- retrieval over a fixture corpus returns at least some expected passage matches;
- retrieval on empty snapshot returns a valid empty candidate list.

## Acceptance gate

This stage is done when:

- retrieval is real, bounded, and traceable;
- candidate identity and provenance are stable;
- every query run has a persisted retrieval trace.

## Coding-agent instructions

- Do not implement reranking here.
- Do not collapse retrieval output into prompt text.
- Keep retrieval output as structured candidates.

---

# Stage 3 — Selection and evidence-set construction

## Goal

Convert retrieved candidates into explicit supportable evidence structures instead of raw top-k text dumps.

## Why this stage exists

The design explicitly rejects naive top-k prompting. This stage is the bridge from search results to supportable evidence.

## Deliverables

### 3.1 Heuristic reranking / selection stage

Implement deterministic heuristic reranking using signals such as:

- closeness to interpreted query or raw query
- heading/path relevance
- local coherence potential
- candidate completeness
- source-navigation precision
- provenance quality
- synthesis diversity when needed

### 3.2 Duplicate suppression

Implement deterministic duplicate and near-duplicate suppression.

### 3.3 Neighbor expansion policy

Implement limited adjacent-passage expansion where local coherence matters.

### 3.4 Evidence-set builder

Implement MVP evidence grouping modes:

- single-passage support
- passage plus neighbor support
- same-document multi-passage grouping
- small cross-document grouping for clear synthesis cases

### 3.5 Selection and evidence-set traces

Persist structured outputs for:

- selected candidates
- candidates dropped and why
- evidence-set membership
- grouping rationale

## Tests

- duplicate suppression is deterministic;
- neighbor expansion stays within allowed policy bounds;
- single-document explanation requests can group multiple passages from one document;
- synthesis grouping does not create oversized or incoherent evidence bundles.

## Acceptance gate

This stage is done when:

- selection is explicit and traceable;
- evidence sets exist as first-class runtime objects;
- the system no longer depends on naive raw top-k prompt assembly.

## Coding-agent instructions

- Keep reranking heuristic and inspectable for MVP.
- Do not add neural rerankers yet.
- Prefer conservative grouping over aggressive synthesis.

---

# Stage 4 — Interpretation and explicit context assembly

## Goal

Add structured query interpretation and deterministic context assembly over evidence sets.

## Why this stage exists

Interpretation determines answer-shape expectations and unsupported-question-type handling. Context assembly determines what the generator actually sees. Both are required before support assessment is meaningful.

## Deliverables

### 4.1 Interpretation stage

Implement one structured LLM call with strict schema for:

- request type
- answer-shape implications
- scope and specificity
- likely source-navigation intent
- likely synthesis intent
- obvious unsupported-question-type signal

Follow with deterministic normalization and policy checks.

### 4.2 Context assembly stage

Build a deterministic `ContextManifest` that:

- orders evidence sets explicitly;
- tracks token budget consumption;
- preserves headings and source-local scaffolding when useful;
- suppresses near-duplicates;
- drops lower-value evidence sets first when over budget;
- records inclusion and exclusion reasons.

### 4.3 Interpretation and context traces

Persist both stage outputs as structured artifacts.

### 4.4 Temporary developer-visible response

Until answer generation is implemented, allow an internal debug response mode that returns:

- interpreted query summary
- selected evidence sets
- context manifest

This helps validate semantics before generation is added.

## Tests

- interpretation preserves distinctions among factual lookup, explanation, synthesis, source navigation, and unsupported question type;
- context ordering is deterministic;
- budget overflow drops lower-priority evidence sets first;
- context manifest always references included evidence set ids.

## Acceptance gate

This stage is done when:

- the system can interpret question shape explicitly;
- the final model-facing context is structured and inspectable;
- context inclusion/exclusion decisions are persisted.

## Coding-agent instructions

- Interpretation is not support assessment.
- Context assembly is not answer generation.
- Keep those contracts separate even if implemented in the same sprint.

---

# Stage 5 — Support assessment and answer-mode policy

## Goal

Implement the trust-critical center of the subsystem: evidence sufficiency judgment and posture control.

## Why this stage exists

This is the main semantic difference between a trustworthy RAG system and a prompt chain that answers whenever it can.

## Deliverables

### 5.1 Support assessment stage

Implement a hybrid stage with:

- deterministic pre-checks for unsupported question types, empty evidence, and obvious provenance insufficiency;
- structured LLM judgment over interpreted query, evidence sets, and context manifest;
- deterministic post-rules that can preserve or narrow support, but never widen it.

Support states should align to the existing support semantics used elsewhere in the project.

### 5.2 Answer-mode decision stage

Implement deterministic policy mapping from support state plus qualifying reasons to allowed answer posture.

Supported answer modes should include at least:

- direct answer
- narrowed answer
- qualified answer
- full abstention
- scoped abstention
- qualified uncertainty

### 5.3 Stage traces

Persist:

- support assessment output
- qualifying reasons
- answer mode decision
- policy version / config snapshot

### 5.4 Failure classification hooks

Attach provisional primary failure labels when obvious, such as:

- failed abstention risk
- wrong abstention risk
- scope-boundary handling
- provenance insufficiency

## Tests

- empty evidence cannot yield direct answer mode;
- unsupported question types cannot yield direct answer mode;
- partial support cannot widen to direct complete answer mode;
- deterministic policy post-rules can only preserve or narrow posture;
- answer-mode mapping is testable without invoking generation.

## Acceptance gate

This stage is done when:

- support is judged explicitly rather than implicitly by generation;
- answer posture is selected by policy logic;
- unsupported or partial-support cases are first-class and test-covered.

## Coding-agent instructions

- Do not hide answer-mode choice in the generation prompt.
- Do not let the LLM invent new support states.
- Keep the policy mapping deterministic and versionable.

---

# Stage 6 — Grounded generation and citation rendering

## Goal

Produce final user-visible answers and citations without allowing hidden support widening or fabricated provenance.

## Why this stage exists

Only after support and posture are explicit can generation be safely introduced.

## Deliverables

### 6.1 Grounded generation stage

Implement one generation call that consumes:

- interpreted query
- context manifest
- support assessment
- answer mode
- visible limitation guidance

Generation rules:

- supported content may be paraphrased;
- synthesis only when support covers it;
- partial support must remain visible;
- conflicting evidence must not be flattened into false consensus;
- unsupported gaps must not be silently filled.

### 6.2 Citation rendering stage

Derive citations from stored provenance, not from the generation model.

Implement citation objects that can represent:

- contributing `doc_id`
- heading path or section path when available
- page range or coarse locator when available
- citation support role
- multi-source bundles where needed

### 6.3 Final answer persistence

Persist:

- answer text
- support state
- qualifying reasons
- answer mode
- visible limitations
- citations

### 6.4 Complete `/queries` response

Return:

- `query_id`
- `answer`
- `support_state`
- `answer_mode`
- `visible_limitations`
- `citations`

## Tests

- generation cannot return citations invented by the model;
- citation locators resolve only to stored provenance;
- partial-support answers include visible qualification;
- unsupported question types surface limitation language instead of fabricated answers;
- multi-source synthesis returns multi-source citation bundles when materially required.

## Acceptance gate

This stage is done when:

- the system can answer end-to-end over `READY` documents;
- citations are derived from provenance-bearing evidence objects;
- abstention and narrowing behaviors are visible in final answers.

## Coding-agent instructions

- Keep generation constrained to supportable evidence only.
- Fail closed on missing citation provenance.
- Do not let answer fluency outrank support fidelity.

---

# Stage 7 — Trace persistence, review endpoints, and replay support

## Goal

Make query runs inspectable enough for debugging, regression analysis, and evaluation.

## Why this stage exists

A grounded answer is not trustworthy if the team cannot inspect why it happened.

## Deliverables

### 7.1 Persistence tables

Implement the initial persistence model with a bias toward structured JSON traces:

- `query_run`
- `query_stage_trace`
- `query_answer`
- `query_citation`
- optional `query_retrieval_candidate`
- optional `query_failure`

### 7.2 Review endpoints

Implement internal endpoints:

- `GET /queries/{query_id}`
- `GET /queries/{query_id}/trace`
- `GET /queries/{query_id}/citations`

### 7.3 Replay foundation

Implement replay first as an internal service/test primitive rather than a required public HTTP feature.

### 7.4 Diagnostic utilities

Add review helpers for:

- stage timing
- candidate inspection
- evidence-set inspection
- context manifest inspection
- support and answer-mode decision review

## Tests

- every successful query has a full trace chain;
- every stage trace is linked to the owning query run;
- citations endpoint is derived from persisted answer/citation state rather than recomputed ad hoc;
- replay can reconstruct a prior run’s stage inputs from persisted artifacts.

## Acceptance gate

This stage is done when:

- a reviewer can inspect how a query answered or abstained;
- retrieval, support, and citation defects are localizable;
- the subsystem is evaluation-ready rather than demo-only.

## Coding-agent instructions

- Prefer structured JSON payloads over premature relational decomposition.
- Keep trace payloads stable enough for regression tooling.
- Do not defer trace persistence until after “the core works.” The trace is part of the core.

---

# Stage 8 — Evaluation hardening and release gating

## Goal

Move from “it runs” to “it meets the MVP trust contract.”

## Why this stage exists

The subsystem should not be considered complete until it is measured against the project’s explicit support, citation, and failure semantics.

## Deliverables

### 8.1 Stage-level tests

Add isolated tests for:

- interpretation
- retrieval
- selection
- evidence-set building
- context assembly
- support assessment
- answer-mode decision
- citation rendering

### 8.2 End-to-end scenario suite

Cover at least:

- direct factual lookup
- section-scoped explanation
- one-document synthesis
- limited cross-document synthesis
- unsupported-in-corpus
- unsupported-question-type
- ambiguous/conflicting evidence
- provenance-sensitive navigation

### 8.3 Failure-oriented suite

Track failures such as:

- unsupported answer
- partial evidence presented as complete
- wrong abstention
- failed abstention
- provenance missing / too weak
- incorrect provenance
- scope-boundary failure
- document-side defect surfacing as query-time trust failure

### 8.4 Release gates

Require that no stage-implementation change can increase:

- unsupported answers
- failed abstentions
- incorrect provenance
- scope-boundary dishonesty

without explicit review and justification.

## Acceptance gate

This stage is done when:

- the subsystem is measured against the same trust semantics as the rest of the project;
- failure categories are visible in evaluation output;
- changes can be judged as regressions or improvements.

## Coding-agent instructions

- Do not optimize only for answer rate.
- Treat unsupported answers and false provenance as release-blocking classes.
- Keep scenario and failure slices visible in test reporting.

---

# Recommended milestone grouping

If you want fewer, larger milestones for the coding agent, use this grouping:

## Milestone A — Query boundary and retrieval foundation

Includes Stages 0, 1, and 2.

Outcome:

- query runs exist;
- corpus snapshots are stable;
- retrieval over `READY` documents is real and traceable.

## Milestone B — Evidence structuring and context path

Includes Stages 3 and 4.

Outcome:

- raw retrieval is converted into evidence sets and deterministic context manifests.

## Milestone C — Trust decision path

Includes Stage 5.

Outcome:

- support assessment and answer-mode policy are explicit and testable.

## Milestone D — End-to-end answer delivery

Includes Stage 6.

Outcome:

- the system can answer, narrow, qualify, abstain, and cite end to end.

## Milestone E — Reviewability and hardening

Includes Stages 7 and 8.

Outcome:

- the subsystem is inspectable, replayable, and gateable by failure-oriented evals.

---

# Order constraints that should not be violated

1. Do not implement final answer generation before support assessment and answer-mode policy exist.
2. Do not implement citation rendering from model text.
3. Do not let retrieval read directly from “latest ready docs” after query start; use the captured snapshot.
4. Do not substitute section retrieval for passage-first retrieval in MVP.
5. Do not skip evidence-set construction and dump top-k passages straight into generation as the default architecture.
6. Do not treat empty evidence as a soft prompt hint; handle it as a first-class support signal.
7. Do not make replay or trace inspection impossible by over-compressing stage outputs.

---

# Minimal MVP defaults to freeze early

These values can change later, but they must be explicit before serious implementation proceeds:

- dense-first retrieval only
- passage-first retrieval unit
- deterministic tie-break ordering
- explicit candidate cap
- explicit evidence-set cap
- explicit context budget
- limited neighboring-passage expansion
- deterministic duplicate suppression
- support-state-driven answer posture
- provenance-derived citation rendering
- internal HTTP surface only

---

# Suggested coding-agent execution template per stage

For each stage, ask the coding agent to deliver in this order:

1. update or create internal domain contracts;
2. implement the stage service logic;
3. persist the stage trace payload;
4. wire the stage into `query/service.py` orchestration;
5. add focused unit/contract tests;
6. add one end-to-end fixture test;
7. document the stage invariants and failure modes in code comments or nearby markdown.

That sequence keeps delivery incremental while preserving inspectability.

---

# Final recommendation

Build the query subsystem in the following strict order:

1. scaffold contracts and policies;
2. enforce `READY`-snapshot query boundaries;
3. implement provenance-preserving retrieval;
4. implement selection and evidence sets;
5. implement interpretation and deterministic context assembly;
6. implement support assessment and answer-mode policy;
7. implement grounded generation and citation rendering;
8. implement trace/review surfaces and evaluation hardening.

That is the shortest path to a working system that still respects `07_design.md` rather than accidentally replacing it with a simpler but semantically weaker architecture.

