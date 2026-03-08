# Post-MVP-Framing Workflow

**Status:** Draft  
**Scope:** Execution workflow after MVP framing  
**Last updated:** 2026-03-08

---

## 1. Purpose of This Workflow

This document defines the execution workflow that begins **after MVP framing has been completed**.

The MVP document establishes the product problem, scope, success criteria, invariants, technical direction, and explicit non-goals. This workflow is the next operational layer: it translates that framing into a parallelizable engineering model that can move from concept to a working release candidate without collapsing into a serialized design phase.

This workflow exists to do five things.

1. Convert MVP framing into a set of **bounded engineering phases** with clear exit criteria.
2. Preserve **parallelism across domains** rather than funneling all decisions through a single lead engineer or one monolithic technical design document.
3. Shift evaluation to the left so that the team is not tuning parsing, retrieval, and answer generation without a defined quality bar.
4. Establish a **walking skeleton** early so that the system is validated as an integrated product rather than as a set of disconnected subsystem experiments.
5. Keep implementation effort anchored to the MVP invariants and out-of-scope boundaries, preventing uncontrolled drift into later-version architecture.

This workflow is intentionally opinionated. It treats the MVP not as a document-processing research program, but as a constrained systems-delivery problem with the following central objective:

> Build a usable question-answering service over a user-uploaded corpus of PDF books and Markdown files, with answers grounded in retrievable source material and failure modes that remain honest when evidence is weak.

This workflow is therefore not a generic agile plan, not a broad product roadmap, and not a comprehensive architecture specification. It is the operating model for converting the MVP into a buildable and releasable system.

---

## 2. Operating Assumptions and Constraints

This workflow assumes a small engineering organization operating across a limited number of bounded domains. It also assumes that the team is willing to adopt evaluation as a first-class engineering primitive rather than relying on ad hoc demos or qualitative “looks good” judgment.

### 2.1 Assumptions

#### Assumption A — Concurrent execution across bounded domains

The engineering team is expected to operate concurrently across the following domains:

- **Platform**
- **Parsing**
- **Search / RAG**
- **LLMOps**

Each domain may work independently within its bounded context, but must align on shared contracts and release criteria.

#### Assumption B — Evaluation maturity exists or can be established quickly

The team has enough engineering capacity to build and maintain a lightweight evaluation framework. This may include:

- deterministic retrieval checks
- schema validation and contract tests
- answer-format validation
- LLM-as-a-judge checks where deterministic evaluation is not feasible
- regression tracking over a stable Golden Dataset

The workflow assumes that tuning decisions will be validated against this evaluation system rather than accepted solely by manual inspection.

#### Assumption C — Engineers can execute across their local stack

Domain ownership does not imply narrow specialization. The intended model is that a domain owner or small pair can implement both the local business logic and the supporting API, storage, or orchestration needed inside that domain boundary.

#### Assumption D — MVP scope discipline is real

The team is willing to defer clearly excluded work even when it appears technically attractive. OCR, table understanding, hybrid retrieval sophistication, large-scale performance optimization, and derived-knowledge surfaces remain outside the critical path unless the release gate proves them necessary.

### 2.2 Constraints

#### Constraint A — Anti-monolith design discipline

The next step after MVP framing must **not** be a monolithic technical design document that attempts to fully specify parsing logic, chunking logic, retrieval design, answer generation, observability, and operational policy in one artifact.

That approach would serialize the team, centralize decision-making prematurely, and convert a parallelizable MVP into a waterfall design phase.

Instead, this workflow uses:

- a small **global contract layer**
- a **shared evaluation layer**
- domain-specific implementation specs owned in parallel

#### Constraint B — Early integration over isolated subsystem sophistication

The workflow prioritizes system connectivity before subsystem excellence. A poor but fully connected end-to-end system is more valuable than four high-quality subsystems that have never been integrated.

#### Constraint C — Invariants dominate local optimization

No domain may optimize its local subsystem in a way that violates global MVP invariants such as traceability, groundedness, stable document identity, or honest failure behavior.

#### Constraint D — Source preservation is mandatory

This product is not merely a text-generation system. Every implementation choice in parsing, chunking, retrieval, and answering must preserve provenance strongly enough to support source inspection.

#### Constraint E — Scope ceiling is enforced

This workflow is for MVP execution only. It is explicitly not the execution workflow for:

- broad enterprise document intelligence
- web retrieval or public-world grounding
- high-scale corpus orchestration
- multimodal document understanding
- collaborative knowledge systems

---

## 3. System Invariants Carried Forward from MVP

The MVP document defines hard requirements that remain true regardless of implementation details. Those are not optional quality goals; they are system invariants. This workflow assumes that every phase, artifact, and domain decision must preserve them.

### 3.1 Stable document identity

Every uploaded document must receive a stable internal identifier that survives ingestion, transformation, retrieval preparation, and answer generation.

This identifier is the anchor for:

- metadata persistence
- provenance tracking
- section ownership
- chunk ownership
- answer citation
- debugging and replay

No workflow step should create ambiguous ownership of document content.

### 3.2 Structural integrity

Recovered structure must form a coherent hierarchy whenever the source allows that hierarchy to be inferred. For Markdown, this usually means preserving heading order and nesting directly. For PDFs, this means inferring structure conservatively and avoiding fabricated precision.

Structural integrity matters because chunk context, citation fidelity, and source navigation all depend on it.

### 3.3 Traceability

Every retrieval unit that can influence answer generation must be traceable back to:

- a source document
- a section or heading path when available
- a page or source location when available
- a normalized transformation lineage when useful for debugging

Traceability is a release invariant, not an observability nice-to-have.

### 3.4 Grounded answering

The answering subsystem must remain bounded by retrieved corpus evidence. The model may synthesize, summarize, or compare, but it must not treat unsupported inference as acceptable answer content.

This invariant affects prompt design, context packaging, answer formatting, and evaluation.

### 3.5 Honest failure behavior

When the corpus does not provide enough support, the system must say so. The system should prefer incomplete but supported output over confident fabrication.

This invariant is central because document QA systems often fail by over-answering. The release gate should explicitly check this behavior.

### 3.6 Unified corpus semantics

Even though inputs may arrive in different formats, the system must present them as one queryable workspace. The user should not have to think in terms of separate PDF and Markdown processing pipelines once ingestion is complete.

### 3.7 Scope-bounded implementation

The system must remain useful without depending on deferred capabilities such as OCR, table extraction, figure understanding, lexical retrieval, or hybrid search optimization.

This invariant prevents hidden scope inflation, where a domain implicitly blocks MVP readiness by treating deferred capabilities as prerequisites.

---

## 4. Execution Model

The execution model defines how the team should operate between framed MVP and releasable system.

The central principle is:

> Lock only what must be global, evaluate early, integrate early, and tune locally under fixed invariants.

### 4.1 Core execution pattern

The workflow uses five sequential phases at the program level:

1. **Global Contract Lock**
2. **Golden Dataset and Evaluation Harness**
3. **Walking Skeleton**
4. **Domain Heuristic Tuning**
5. **Integrated Release Gate**

However, inside each phase, work is intentionally parallelized across bounded domains.

### 4.2 What gets centralized vs what stays local

#### Centralized

The following concerns are global and should be locked early:

- shared schemas
- provenance and source-reference contracts
- ingest/job states needed across domains
- evaluation dimensions
- release criteria

These define the interoperability surface.

#### Local to domains

The following should remain domain-owned and evolve independently as long as contracts are preserved:

- parsing heuristics
- PDF heading inference rules
- chunking strategies
- retrieval tuning
- prompt design and answer-shaping logic
- operational instrumentation internal to a domain

This prevents central architectural overhead from blocking implementation.

### 4.3 Artifact model

The workflow deliberately separates artifacts into layers:

#### Layer 1 — Global architecture artifacts

Small number of shared artifacts that define interfaces and quality boundaries.

#### Layer 2 — Domain speclets

Short, domain-owned documents that define local implementation logic, heuristics, internal constraints, and tuning plans.

#### Layer 3 — Running system and eval outputs

Executable code, Golden Dataset assets, regression reports, and release evidence.

This layering prevents the architecture process from becoming a bottleneck while still forcing coherence.

### 4.4 Why evaluation is left-shifted

Without evaluation, domains will optimize according to local intuition:

- Parsing may optimize for structure richness without evidence that it improves retrieval.
- Search / RAG may tune chunking or k-values without knowing whether support recall actually improved.
- LLMOps may tune prompts for fluency rather than groundedness.

To prevent blind tuning, the workflow requires the Golden Dataset and evaluation harness to be established before substantial optimization begins.

### 4.5 Why a walking skeleton is required

A walking skeleton proves that the core control path is real:

- the user can upload supported files
- the system can extract enough text to process them
- content can be chunked and indexed
- a question can retrieve relevant chunks
- an answer can be generated and tied to sources

This is not a quality milestone. It is an integration milestone.

### 4.6 Change acceptance rule

After the walking skeleton exists, no local optimization should be accepted merely because it seems reasonable. A change should be accepted if at least one of the following is true:

- it improves evaluation results
- it improves reliability or debuggability without regressing evaluation
- it reduces operational complexity while preserving evaluation and contracts
- it closes a release-blocking defect

### 4.7 Governance model

A lightweight governance model is sufficient.

- Global contract changes require cross-domain review.
- Domain-local heuristic changes do not require global review unless they alter shared contracts or release behavior.
- Release criteria changes require explicit sign-off because they redefine the MVP bar.

This keeps coordination cost proportional to architectural impact.

---

## 5. Workflow Overview

This section provides the high-level map of the workflow.

### Phase 1 — Global Contract Lock

Define the minimal shared contract surface that all domains need in order to build concurrently. Lock schemas, ownership boundaries, provenance requirements, and answer/citation shapes.

### Phase 2 — Golden Dataset and Evaluation Harness

Build the initial evaluation corpus and quality framework. Define representative questions, expected evidence, and scoring rules before the team starts tuning parsing and retrieval logic.

### Phase 3 — Walking Skeleton

Build the thinnest end-to-end system that connects upload, extraction, chunking, retrieval, prompting, and source-backed response generation. Quality may be low; connectivity must be real.

### Phase 4 — Domain Heuristic Tuning

Improve system quality by tuning local heuristics against the Golden Dataset while preserving shared contracts and invariants.

### Phase 5 — Integrated Release Gate

Run the integrated system against functional and quality release criteria derived from the MVP. Decide readiness based on grounded behavior, source inspectability, and transparent failure handling rather than feature count.

### 5.1 Canonical phase progression

The intended progression is:

**Contract Lock → Eval Definition → Walking Skeleton → Heuristic Tuning → Release Gate**

### 5.2 Non-canonical behaviors to avoid

The workflow should explicitly avoid the following failure patterns:

- writing a complete design spec before any code is integrated
- building retrieval without an evaluation dataset
- optimizing PDF parsing before the end-to-end system exists
- shipping fluent answers without inspecting support quality
- treating deferred features as hidden prerequisites for MVP

### 5.3 Expected outputs by phase

| Phase | Primary output |
|---|---|
| Global Contract Lock | Shared contracts and interface boundaries |
| Golden Dataset and Evaluation Harness | Stable eval corpus, question set, and scoring framework |
| Walking Skeleton | First fully connected end-to-end system |
| Domain Heuristic Tuning | Measurable quality improvements without contract drift |
| Integrated Release Gate | Release evidence and go / no-go decision |

---

## 6. Phase 1 — Global Contract Lock

The purpose of this phase is to define the minimum shared interface layer required for parallel execution.

This phase is intentionally narrow. It should not attempt to lock all implementation logic. It should only lock the contracts whose ambiguity would otherwise block cross-domain work.

### 6.1 Objectives

The objectives of this phase are:

- define the shared internal object model
- define answer and citation payload structure
- define ingest and processing lifecycle states that affect multiple domains
- define provenance and source-reference guarantees
- define domain boundaries and ownership rules

### 6.2 Required outputs

At the end of this phase, the team should have:

- a shared schema definition for core entities
- a documented contract for answer payloads and source references
- a documented lifecycle for document ingestion and processing
- a clear boundary map across Platform, Parsing, Search / RAG, and LLMOps
- initial contract tests or schema validation hooks

### 6.3 Shared corpus model

The corpus model should be minimal but stable enough to support ingestion, retrieval, and traceable answer generation.

#### 6.3.1 Document

A `Document` should represent the stable top-level identity for an uploaded file.

Recommended minimal fields:

- `doc_id`
- `workspace_id` or equivalent ownership boundary
- `source_type` (`pdf` or `markdown`)
- `title`
- `filename`
- `upload_timestamp`
- `ingest_status`
- raw-storage reference
- optional derived metadata

#### 6.3.2 Section

A `Section` should represent a logical structural node recovered from the source.

Recommended minimal fields:

- `section_id`
- `doc_id`
- `parent_section_id` or document-root binding
- ordered heading path
- heading text
- structural depth
- optional page span
- optional source offsets
- structure confidence or provenance marker where useful

#### 6.3.3 Retrieval unit / Chunk

A `Chunk` should be the retrieval-addressable text unit used by the search layer.

Recommended minimal fields:

- `chunk_id`
- `doc_id`
- `section_id` when available
- text payload
- chunk order within section or document
- page reference when available
- heading path snapshot
- metadata used for retrieval filtering or debugging

#### 6.3.4 Transformation lineage

If feasible within MVP complexity, each derived object should carry enough lineage to reconstruct how it was produced. This may include:

- parser version
- chunker version
- source extraction mode
- normalization pipeline markers

This is especially useful for regressions and replay.

### 6.4 Answer and citation contract

The answer payload is a global contract because it binds Search / RAG, LLMOps, UI, and user trust.

A minimal answer contract should include:

- answer text
- answer status (`supported`, `insufficient_evidence`, optionally `partial`)
- cited supporting units
- source references normalized for inspection
- optional confidence or support notes if the product chooses to expose them

#### 6.4.1 Citation primitives

A citation or source reference should be able to resolve to at least:

- document identity
- document title
- section / heading path when available
- page reference when available
- snippet or passage anchor sufficient for user inspection

The citation contract should not depend on perfect PDF structure recovery. It should degrade gracefully from `page + inferred heading path` to `page only` when necessary.

### 6.5 Ingestion and job lifecycle contract

Multiple domains depend on document-processing state, so the lifecycle must be standardized.

A minimal state model might include:

- `uploaded`
- `registered`
- `extracting`
- `normalized`
- `chunked`
- `indexed`
- `ready`
- `failed`

This contract does not need to specify orchestration technology, only state semantics and observable transitions.

### 6.6 Observability and debug contract

The MVP does not require production-grade observability, but the workflow does require enough shared debug surfaces to support tuning and regression analysis.

Minimum required debug visibility:

- what document was processed
- which parser path ran
- how sections were produced
- how many chunks were created
- what chunks were retrieved for a question
- what source units were handed to the answer generator
- what answer status was returned

### 6.7 Domain interface boundaries

#### Platform owns

- upload entrypoints
- document registration
- storage references
- processing orchestration
- readiness state exposure

#### Parsing owns

- text extraction from supported file types
- Markdown hierarchy recovery
- PDF structure inference
- section construction

#### Search / RAG owns

- chunk generation
- embeddings and indexing
- retrieval selection
- evidence packaging for the answer layer

#### LLMOps owns

- prompting strategy
- answer status behavior
- answer formatting and citation rendering contract compliance
- qualitative answer-bound enforcement

### 6.8 Exit criteria

Phase 1 is complete when:

- core schemas are defined and agreed
- answer/citation payloads are stable enough for downstream work
- lifecycle states are documented and usable
- domain boundaries are explicit
- no unresolved contract ambiguity blocks concurrent implementation

---

## 7. Phase 2 — Golden Dataset and Evaluation Harness

This phase defines the quality framework that will govern tuning and release decisions.

The Golden Dataset is not a late-stage QA asset. It is a design primitive. It tells the team what kinds of user questions matter, what support behavior is expected, and how system changes will be measured.

### 7.1 Objectives

The objectives of this phase are:

- define a representative corpus slice for MVP evaluation
- codify important question types from the product definition
- establish measurable criteria for retrieval and answer quality
- create a reproducible mechanism for regression testing

### 7.2 Golden Dataset composition

The initial Golden Dataset should be intentionally small but behaviorally representative.

Recommended composition:

- text-based PDFs with recoverable headings
- text-based PDFs with weak or inconsistent structure
- clean Markdown notes with explicit heading hierarchies
- Markdown converted from PDFs with imperfect formatting
- documents that require cross-document synthesis to answer certain questions

The dataset should cover both “easy” and “annoying but in-scope” cases.

### 7.3 Question taxonomy

The evaluation set should reflect the MVP use cases.

#### 7.3.1 Factual lookup

Questions answerable from a single local source span.

Examples:

- definition questions
- requirement lookup
- direct concept identification

#### 7.3.2 Localized explanation

Questions requiring bounded synthesis from a local section or chapter.

Examples:

- explain a documented strategy
- summarize a local explanation
- describe a concept as presented in a specific source

#### 7.3.3 Multi-source synthesis

Questions whose best answer requires combining support from more than one document or section.

Examples:

- compare two descriptions
- aggregate what several documents say about a topic
- reconcile overlapping descriptions

#### 7.3.4 Source navigation

Questions whose primary value is in locating the relevant source material.

Examples:

- where is topic X discussed
- which sections are most relevant to question Y
- show passages related to concept Z

#### 7.3.5 Insufficient evidence cases

The dataset must include questions that **should not** be answered confidently. These cases are necessary to test honest failure behavior.

### 7.4 Labeling strategy

Not every question requires full extractive ground truth, but the labeling strategy should still be explicit.

Possible label types:

- expected supporting document(s)
- expected supporting section(s)
- expected page(s) for PDFs when available
- allowed answer status (`supported` or `insufficient_evidence`)
- answer rubric for judge-based scoring

The evaluation framework should tolerate realistic ambiguity where multiple source spans are acceptable.

### 7.5 Metrics and scoring

The eval harness should score both retrieval quality and answer quality.

#### Retrieval metrics

Possible metrics include:

- support recall at `k`
- document hit rate
- section hit rate
- page hit rate where page labeling exists
- retrieval stability across repeated runs, if nondeterminism is present

#### Answer metrics

Possible metrics include:

- groundedness / support faithfulness
- citation correctness
- answer completeness within the available evidence
- excess unsupported content rate
- insufficient-evidence precision and recall

#### Structural metrics

Where feasible, parsing quality should be measured independently for:

- heading recovery correctness
- section boundary plausibility
- page association fidelity
- malformed-document fallback behavior

### 7.6 Deterministic checks vs LLM-judge checks

The evaluation harness should use deterministic checks where possible and reserve model-based judgment for questions that are inherently semantic.

#### Deterministic checks are appropriate for:

- schema validity
- answer status validity
- citation payload completeness
- support document hit checks
- page hit checks
- known section hit checks

#### Judge-based checks are appropriate for:

- answer groundedness when multiple phrasings are acceptable
- adequacy of synthesis across sources
- whether the system overstates claims beyond support
- whether insufficient-evidence responses are justified

### 7.7 Day-to-day usage of evals

The evaluation harness should not be treated as a release-only tool.

It should be used:

- after significant parsing changes
- after chunking or retrieval changes
- after prompt changes
- before merging release-sensitive modifications
- before release gate assessment

### 7.8 Output artifacts

At the end of this phase, the team should have:

- the first Golden Dataset corpus slice
- a labeled question set
- a runnable evaluation harness
- baseline metrics from the current system state, even if the scores are poor

### 7.9 Exit criteria

Phase 2 is complete when:

- the Golden Dataset exists and is versioned
- question classes cover the core MVP use cases
- insufficient-evidence cases are included
- at least one runnable scoring workflow exists
- the team can compare two system states using the same eval framework

---

## 8. Phase 3 — Walking Skeleton

The walking skeleton is the first fully connected system.

Its purpose is not to be good. Its purpose is to be real.

### 8.1 Objectives

The objectives of this phase are:

- prove the end-to-end architecture with the least possible complexity
- establish the complete control path from upload to answer
- create a concrete base system that later tuning can improve
- flush out contract problems early by forcing domains to integrate

### 8.2 Required end-to-end path

The minimum connected path should include:

1. file upload and document registration
2. raw extraction from PDF or Markdown
3. coarse normalization into sections or fallback document-level structure
4. naive chunk generation
5. embedding and indexing of chunks
6. retrieval for a user question
7. answer generation over retrieved evidence
8. source-backed response rendering

### 8.3 Quality expectations for this phase

Quality is intentionally low in this phase. The skeleton is allowed to be weak in:

- PDF heading inference
- chunk boundary quality
- retrieval relevance
- answer completeness
- answer style

It is **not** allowed to be weak in:

- basic end-to-end connectivity
- stable identity propagation
- provenance propagation
- answer payload validity
- ability to return a source-backed or insufficient-evidence response

### 8.4 Minimal implementation guidance by domain

#### Platform

Implement:

- upload endpoint or basic UI
- document registration and storage
- simple process invocation or job triggering
- readiness state exposure

#### Parsing

Implement:

- raw text extraction for PDFs
- heading-based parsing for Markdown
- conservative fallback for weakly structured PDFs
- first-pass section objects, even if coarse

#### Search / RAG

Implement:

- naive chunking
- simple embedding model selection
- baseline nearest-neighbor retrieval
- top-k evidence packaging

#### LLMOps

Implement:

- simple answer prompt
- strict instruction to stay within provided evidence
- explicit insufficient-evidence behavior
- answer format compatible with the shared contract

### 8.5 Non-goals for this phase

The walking skeleton should avoid:

- sophisticated PDF reconstruction
- complex metadata filtering
- reranking pipelines
- hybrid retrieval
- polished UI behavior
- extensive background job infrastructure
- advanced observability systems

### 8.6 Baseline evaluation expectation

The walking skeleton should be run against the Golden Dataset even if results are poor. The purpose is to establish a baseline and identify which domains are the largest contributors to failure.

### 8.7 Exit criteria

Phase 3 is complete when:

- a user can upload supported files and receive a response to a question
- the response contains source references or an insufficient-evidence result
- retrieved support can be inspected in a debuggable way
- all domains are integrated against shared contracts
- the system can be scored by the evaluation harness

---

## 9. Phase 4 — Domain Heuristic Tuning

This phase is where quality improves.

Once the skeleton is walking, each domain can tune its local logic against the Golden Dataset without destabilizing the global architecture. This phase should be understood as **heuristic tuning under fixed invariants**, not open-ended redesign.

### 9.1 Objectives

The objectives of this phase are:

- improve retrieval support quality
- improve structure recovery quality
- improve answer groundedness and failure behavior
- reduce obvious operational fragility
- do all of the above without breaking contracts or expanding scope

### 9.2 Tuning principles

#### Principle A — Eval movement is the acceptance signal

A tuning change should be accepted only if it improves evaluation results, improves reliability without harming evaluation, or closes a release-blocking issue.

#### Principle B — Local optimization must preserve provenance

No tuning is acceptable if it weakens traceability or makes source inspection less reliable.

#### Principle C — Conservative structure inference beats fabricated precision

Especially for PDFs, it is better to expose coarse but correct structure than rich but unreliable hierarchy.

#### Principle D — Prompt quality is subordinate to evidence discipline

Fluent answers are not a goal if they overstate unsupported claims.

### 9.3 Parsing heuristics

Likely tuning areas for Parsing include:

- heading recovery from text patterns
- page-aware structural segmentation
- normalization of malformed Markdown heading trees
- fallback strategies for documents with weak structure
- preservation of code blocks and lists where semantically important

The goal is not perfect structural reconstruction. The goal is enough structure to materially improve retrieval and source navigation.

### 9.4 Chunking and retrieval heuristics

Likely tuning areas for Search / RAG include:

- chunk sizing policy
- overlap policy
- chunking by section vs fallback by length
- top-k retrieval policy
- metadata-aware filtering or grouping
- document diversity balancing for synthesis questions
- evidence packaging to the answer layer

The tuning target is support quality, not abstract retrieval elegance.

### 9.5 Prompting and answer-bounding heuristics

Likely tuning areas for LLMOps include:

- instructions for bounded synthesis
- refusal and insufficient-evidence behavior
- citation formatting discipline
- answer decomposition for compare/summarize questions
- mitigation of unsupported extrapolation

The answer layer should be tuned toward conservative support usage rather than maximum verbosity.

### 9.6 Reliability and operational tuning

Likely tuning areas for Platform include:

- retry and failure recovery for ingestion
- idempotency around document processing
- clearer readiness signals
- better debugging surfaces for failed or low-quality documents
- simple replay mechanisms for regression investigation

### 9.7 Working method

This phase should proceed in small loops:

1. identify a failure mode from evals or real usage
2. localize the likely domain owner
3. implement a constrained heuristic change
4. rerun relevant eval slices
5. accept, reject, or refine based on measured effect

### 9.8 Things not to do in this phase

Avoid turning this phase into:

- a full architecture rewrite
- a hidden v2 feature wave
- a broad scale/performance program
- a UI redesign effort
- speculative tuning without eval support

### 9.9 Exit criteria

Phase 4 is complete when:

- the system shows material improvement against baseline evals
- the main in-scope failure modes are reduced to acceptable levels
- answer grounding and source inspection behave consistently
- remaining deficiencies are either release-tolerable or explicitly deferred

---

## 10. Phase 5 — Integrated Release Gate

This phase determines whether the system is ready to be called the MVP.

The release gate should not be framed as “did we build everything we can think of?” It should be framed as “does the integrated system satisfy the MVP invariants and success criteria at a level that makes the product useful?”

### 10.1 Objectives

The objectives of this phase are:

- validate the integrated system against the MVP definition
- ensure the release bar is based on user utility and system integrity
- document known limitations clearly
- make an explicit go / no-go decision

### 10.2 Functional release criteria

The system should satisfy all of the following:

- accepts both text-based PDF and Markdown inputs
- ingests them into one user-visible corpus or workspace
- allows natural-language questioning over that corpus
- retrieves support from one or more documents
- returns an answer tied to identifiable source references
- allows source inspection at the level supported by the source material

### 10.3 Quality release criteria

The system should satisfy the following quality expectations:

- structure recovery is reliable enough in common cases to support navigation and chunk context
- retrieval works across document boundaries for the intended use cases
- answer content remains bounded by available evidence
- insufficient-evidence behavior is explicit and credible
- citation payloads are complete enough for user inspection

### 10.4 Failure-mode requirements

The release gate should explicitly test the following failure classes:

- weakly structured PDF input
- malformed Markdown input
- questions whose answer is absent from the corpus
- questions whose answer depends on excluded modalities such as tables or figures
- synthesis questions that risk unsupported generalization

A release candidate is not acceptable if these cases produce routinely misleading answers.

### 10.5 Evaluation evidence required

The release decision should be backed by:

- Golden Dataset results
- regression comparison against earlier system baselines
- evidence that insufficient-evidence handling works on negative cases
- manual spot checks only as a supplement, not as the primary proof

### 10.6 Known limitations statement

Before release, the team should be able to state clearly what the MVP does **not** do. At minimum, this should include:

- no OCR for scanned PDFs
- no special handling for tables, figures, or images
- no external-world knowledge grounding
- no guarantee of exhaustive retrieval over very large corpora
- no advanced collaboration or enterprise controls

### 10.7 Go / no-go decision rule

A reasonable decision rule is:

- **Go** if the system satisfies all functional requirements, preserves invariants, and meets a credible quality threshold on the Golden Dataset.
- **No-go** if the system still fabricates unsupported answers frequently, fails to preserve provenance reliably, or cannot support source inspection in normal in-scope cases.

### 10.8 Exit criteria

Phase 5 is complete when:

- release evidence has been assembled
- known limitations are documented
- a go / no-go decision has been made explicitly
- deferred work is not confused with release blockers unless it violates the MVP invariants

---

## 11. Domain Responsibilities by Phase

This section makes domain concurrency explicit. It defines what each bounded domain is responsible for during each workflow phase.

### 11.1 Domain summary

- **Platform** owns document registration, storage references, processing orchestration, and readiness surfaces.
- **Parsing** owns extraction and structural normalization of PDF and Markdown inputs.
- **Search / RAG** owns chunk creation, indexing, retrieval, and evidence selection.
- **LLMOps** owns answer generation behavior, bounded synthesis, and insufficient-evidence discipline.

### 11.2 Responsibility matrix by phase

| Phase | Platform | Parsing | Search / RAG | LLMOps |
|---|---|---|---|---|
| Global Contract Lock | Define document registration and job-state semantics; storage-facing contract surfaces | Define section model requirements and parsing output expectations | Define chunk contract, retrieval input/output contract, evidence packaging needs | Define answer payload, citation requirements, answer-status semantics |
| Golden Dataset and Evaluation Harness | Provide dataset loading support and reproducible execution hooks | Help label structure-sensitive cases and parsing-specific failure categories | Define retrieval metrics and support-hit expectations | Define groundedness, citation, and insufficient-evidence scoring rubrics |
| Walking Skeleton | Build upload, registration, storage, and simple orchestration path | Implement baseline extraction and coarse structure recovery | Implement naive chunking, indexing, and baseline retrieval | Implement baseline prompt and source-backed answer behavior |
| Domain Heuristic Tuning | Improve reliability, retries, idempotency, and debug surfaces | Tune heading recovery, section segmentation, and fallback logic | Tune chunking, retrieval policy, and evidence packaging | Tune prompting, refusal behavior, and citation discipline |
| Integrated Release Gate | Supply release-state visibility and operational readiness evidence | Supply parsing quality evidence and known-structure limitations | Supply retrieval quality evidence and cross-document support behavior | Supply answer groundedness evidence and negative-case behavior |

### 11.3 Boundary rules

To keep the domains from collapsing into each other, the following rules apply.

#### Rule A — Platform does not own parsing logic

Platform may orchestrate parsing, but it should not become the owner of structural heuristics.

#### Rule B — Parsing does not own retrieval semantics

Parsing provides structure and normalized text. It does not decide retrieval ranking policy.

#### Rule C — Search / RAG does not own final user-facing answer policy

Search / RAG selects evidence and packages it, but the answer layer owns bounded synthesis behavior.

#### Rule D — LLMOps does not rewrite source truth

LLMOps may shape prompts and answer formats, but it must operate on evidence provided by the shared contracts and retrieval layer rather than inventing unsupported structure.

### 11.4 Collaboration expectations

The domains should collaborate most closely at these edges:

- **Platform ↔ Parsing** for ingestion lifecycle and replay/debug behavior
- **Parsing ↔ Search / RAG** for section fidelity and chunk-context quality
- **Search / RAG ↔ LLMOps** for evidence packaging, answer status semantics, and citation formatting
- **All domains ↔ Evaluation** because every meaningful tuning decision must be measurable

### 11.5 Escalation cases

A change should be escalated for cross-domain review if it does any of the following:

- changes a shared schema
- changes citation semantics
- changes answer-status behavior
- changes ingest/job lifecycle semantics
- changes what counts as release success

### 11.6 Phase-level ownership outcomes

By the end of sections 1–11 of this workflow, the intended operating model should be clear:

- shared contracts are global
- heuristics are local
- evaluation is shared and early
- integration happens before optimization
- release is gated by invariants and evidence, not by speculative completeness

---

## End of Sections 1–11

Sections 12 and beyond are intentionally deferred for the next document iteration.
