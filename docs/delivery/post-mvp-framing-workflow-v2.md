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

---

## 12. Artifact Set

This section makes the workflow operational by defining the concrete artifacts the team is expected to produce. Without an explicit artifact set, the workflow risks becoming a conceptual process description rather than an executable delivery model.

The artifact model follows the same principle as the execution model:

> keep global artifacts small and stable; keep domain artifacts local and mutable.

### 12.1 Artifact design principles

The artifact set should satisfy the following rules.

#### Rule A — Shared artifacts define interfaces, not implementation details

A global artifact should exist only when multiple domains need the same boundary condition. Shared artifacts should lock contracts, semantics, and release criteria, but should avoid embedding local heuristic logic.

#### Rule B — Domain artifacts should be short and directly actionable

A domain artifact is not a mini-architecture thesis. It should describe the local design choices, heuristics, inputs, outputs, test surfaces, and rollout constraints needed for that domain to execute.

#### Rule C — Evaluation artifacts are first-class engineering assets

The Golden Dataset, labels, scoring rubrics, and evaluation runner are not temporary QA collateral. They are part of the system-definition layer and should be versioned accordingly.

#### Rule D — Release artifacts must prove integrity, not merely summarize activity

A release artifact should demonstrate that the MVP bar has been met. It should not degenerate into a status update or an aspirational milestone deck.

### 12.2 Global shared artifacts

The following artifacts should exist at the shared layer.

#### 12.2.1 Architecture RFC

This is the primary cross-domain design artifact.

Its scope should be intentionally constrained to:

- shared schemas
- provenance guarantees
- answer and citation contract
- lifecycle states and state semantics
- release invariants
- evaluation dimensions
- domain ownership boundaries

It should not attempt to specify:

- PDF heading-recovery heuristics
- chunk-size tuning policy
- prompt wording details
- embedding model experiments
- storage implementation details beyond contract relevance

Recommended sections:

1. context and purpose
2. shared object model
3. lifecycle semantics
4. source-reference contract
5. answer-status contract
6. cross-domain ownership map
7. compatibility and change policy

#### 12.2.2 Schema registry or schema definition package

The team should maintain a single source of truth for the shared payloads and entities used across domains. Depending on the stack, this may be expressed as:

- JSON Schema
- Protocol Buffers
- typed backend definitions
- generated client/server contract package

At minimum, the schema set should cover:

- `Document`
- `Section`
- `Chunk`
- processing/job-state payloads
- retrieval-result payload
- answer payload
- citation/source-reference payload

#### 12.2.3 Contract test suite

Shared contracts should be enforced mechanically, not socially.

Recommended test categories:

- schema conformance tests
- backward/forward compatibility checks where relevant
- citation-resolution tests
- answer-payload validation tests
- ingest/job-state transition tests

#### 12.2.4 Golden Dataset specification

This artifact defines the evaluation corpus and labeling rules.

Recommended contents:

- dataset purpose and scope
- corpus composition rules
- question taxonomy
- negative-case requirements
- labeling guidelines
- scoring semantics
- dataset versioning rules
- known blind spots

#### 12.2.5 Evaluation harness specification

This artifact describes how the system is executed against the Golden Dataset and how results are recorded.

Recommended contents:

- runner inputs and outputs
- deterministic vs model-based evaluators
- scoring aggregation logic
- regression-comparison policy
- storage location of historical runs
- treatment of flaky evaluation dimensions

#### 12.2.6 Release checklist and release evidence template

The team should maintain a release artifact template that records:

- system version under evaluation
- Golden Dataset results
- known limitations
- unresolved defects
- go / no-go recommendation
- sign-off owners

### 12.3 Domain-specific artifacts

Each bounded domain should maintain a lightweight speclet or equivalent implementation note.

#### 12.3.1 Platform speclet

Recommended contents:

- upload flow
- document registration semantics
- storage references and ownership model
- processing orchestration approach
- idempotency strategy
- retry and failure semantics
- debug visibility surfaces

#### 12.3.2 Parsing speclet

Recommended contents:

- Markdown parsing approach
- PDF text extraction path
- structure-recovery heuristics
- section-construction rules
- fallback behavior for weak structure
- parser output examples
- parsing-specific evaluation dimensions

#### 12.3.3 Search / RAG speclet

Recommended contents:

- chunking policy
- embedding and indexing baseline
- retrieval flow
- evidence-packaging contract
- metadata usage
- cross-document retrieval behavior
- retrieval-specific metrics and ablations

#### 12.3.4 LLMOps speclet

Recommended contents:

- answer prompt contract
- answer-status rules
- insufficient-evidence behavior
- citation rendering constraints
- prompt-evaluation methodology
- rollback rules for prompt regressions

### 12.4 Supporting operational artifacts

The following supporting artifacts are not global architecture documents, but they are still useful for execution.

#### 12.4.1 Corpus fixture manifest

A manifest describing the concrete files used in the Golden Dataset, including source type, topical category, and any known structural peculiarities.

#### 12.4.2 Failure-case catalog

A rolling catalog of known failure examples. Each entry should record:

- the user question
- retrieved evidence
- system answer
- expected behavior
- observed defect class
- disposition (`fixed`, `known`, `deferred`)

#### 12.4.3 Baseline result snapshot

A durable record of the walking-skeleton performance so that later improvements can be measured against an agreed baseline rather than memory.

#### 12.4.4 Release limitations statement

A short, user-facing or internal-facing statement describing what the MVP explicitly does not support. This ensures that deferred scope is represented clearly at release time.

### 12.5 Artifact ownership model

Artifacts should have explicit owners.

| Artifact | Primary owner | Reviewers |
|---|---|---|
| Architecture RFC | Technical lead or delegated architecture owner | All domain leads |
| Schema registry | Shared contract owner | Platform, Search / RAG, LLMOps |
| Contract test suite | Platform or shared infra owner | All domain leads |
| Golden Dataset specification | Evaluation owner | Parsing, Search / RAG, LLMOps |
| Evaluation harness specification | Evaluation owner | Platform, Search / RAG, LLMOps |
| Platform speclet | Platform | Architecture owner + adjacent domains |
| Parsing speclet | Parsing | Architecture owner + Search / RAG |
| Search / RAG speclet | Search / RAG | Architecture owner + LLMOps |
| LLMOps speclet | LLMOps | Architecture owner + Search / RAG |
| Release evidence template | Program or release owner | All domain leads |

### 12.6 Minimum viable artifact set

If the team needs the smallest acceptable artifact footprint, the minimum viable set is:

- Architecture RFC
- shared schema package
- Golden Dataset specification
- evaluation harness
- one speclet per domain
- baseline result snapshot
- release evidence template

Anything less risks ambiguity in interfaces, quality standards, or release proof.

---

## 13. Decision Log and Deferred Decisions

This section distinguishes between decisions that must be locked for MVP execution and decisions that should remain intentionally open. A workflow becomes brittle when it pretends every question should be answered immediately.

The purpose of this section is to prevent two common failure modes:

1. pseudo-precision, where the team locks details too early and constrains learning unnecessarily
2. scope drift, where unresolved details silently expand into unplanned work

### 13.1 Decision categories

The workflow recognizes three decision classes.

#### Class A — Locked for MVP

These decisions define the build boundary and should not change casually once implementation begins.

#### Class B — Deferred within MVP execution

These decisions may remain open during the walking-skeleton phase, but must be resolved before release if they materially affect quality or integrity.

#### Class C — Deferred beyond MVP

These decisions are explicitly outside the MVP bar and should not become hidden blockers.

### 13.2 Decisions that should be locked now

The following decisions should be treated as mandatory early locks.

#### 13.2.1 Supported source types

Lock that MVP supports:

- text-based PDFs
- Markdown files

Do not broaden the source-type matrix during MVP execution.

#### 13.2.2 Core entity contracts

Lock the existence and semantics of:

- `Document`
- `Section`
- `Chunk`
- answer payload
- citation/source-reference payload
- processing/job-state surface

#### 13.2.3 Invariants

Lock the invariant set:

- stable document identity
- structural integrity
- traceability
- grounded answering
- honest failure behavior
- unified corpus semantics
- scope-bounded implementation

#### 13.2.4 Release philosophy

Lock that release is gated by:

- source-backed answer behavior
- provenance and inspectability
- negative-case honesty
- measured performance on the Golden Dataset

Do not redefine the release bar around feature count.

#### 13.2.5 Deferred-scope exclusions

Lock the exclusion of:

- OCR
- special handling for tables, figures, and images
- lexical retrieval as a first-class retrieval layer
- advanced hybrid retrieval sophistication
- derived summaries and synthetic questions as first-class artifacts
- collaboration and enterprise-control surfaces
- external-world retrieval

### 13.3 Decisions that may remain open briefly during MVP execution

The following decisions can remain flexible during early execution, provided the shared contracts remain intact.

#### 13.3.1 PDF structure-recovery heuristics

The specific rules used to infer headings, section boundaries, and page-to-section relationships in PDFs should remain open to experimentation during the walking-skeleton and tuning phases.

#### 13.3.2 Chunking policy

The exact chunk size, overlap strategy, and section-boundary policy may remain open initially. What must remain fixed is the need for chunk-level provenance and stable retrieval addressing.

#### 13.3.3 Retrieval composition

The team may experiment with:

- top-k values
- metadata-aware filtering
- simple reranking choices
- evidence-packaging layout

These are tuning parameters rather than first-order product definitions.

#### 13.3.4 Prompt wording and answer formatting details

The exact prompt phrasing, response structure, and exposed user-facing support notes may remain adjustable until evals show stable behavior.

#### 13.3.5 Confidence exposure policy

The product may choose to expose or hide support notes or confidence-like fields. This does not need to be resolved immediately unless the UI depends on it.

### 13.4 Decisions deferred beyond MVP

The following decisions should be recorded as intentionally deferred and should not become accidental release blockers.

#### 13.4.1 OCR and scanned-document support

Scanned PDFs remain outside the MVP. Any architecture work to support OCR should be isolated from the critical path.

#### 13.4.2 Rich layout and multimodal understanding

This includes:

- tables
- charts
- figures
- diagrams
- images
- margin annotations and other complex layout artifacts

#### 13.4.3 Hybrid and lexical retrieval expansion

A lexical or hybrid retrieval stack may be valuable later, but MVP should prove utility without it.

#### 13.4.4 Derived knowledge products

This includes:

- persistent summaries
- generated study aids
- synthetic question banks
- knowledge graphs
- entity extraction pipelines

#### 13.4.5 Scale-oriented platform decisions

This includes:

- sharding strategies
- aggressive performance optimization
- enterprise-grade tenancy and ACL design
- connector ecosystems and sync infrastructure

### 13.5 Decision logging process

A lightweight decision process is sufficient.

Each decision entry should record:

- decision identifier
- title
- class (`locked now`, `deferred within MVP`, `deferred beyond MVP`)
- rationale
- owner
- date
- downstream impact
- reversal conditions if applicable

### 13.6 Decision change policy

A previously locked decision should be reopened only if one of the following is true:

- the Golden Dataset shows the locked choice makes the MVP non-viable
- the decision violates an invariant in practice
- the implementation cost is disproportional to the MVP value gained
- an adjacent locked decision changed and created inconsistency

### 13.7 Anti-patterns to avoid

The decision layer should avoid the following behaviors:

- silently changing shared contracts without a decision record
- reclassifying deferred work as required without explicit rationale
- using vague language such as “we may need OCR” to justify premature scope expansion
- confusing local tuning parameters with globally locked architecture choices

---

## 14. Risks and Failure Modes

This section describes the principal execution and system risks for the MVP. The purpose is not to eliminate uncertainty, but to make the dominant failure modes visible early enough that they can be managed deliberately.

### 14.1 Risk model

The workflow recognizes four broad risk classes:

- product-value risk
- structural / data-quality risk
- retrieval and answer-quality risk
- execution / coordination risk

### 14.2 Product-value risks

#### 14.2.1 The system answers fluently but not usefully

A document QA system can appear impressive in demos while still failing the primary user job. This happens when the answer sounds plausible but does not reduce the user’s effort to find and validate relevant source material.

**Primary indicators**

- answers are verbose but weakly supported
- citations exist but are too vague to inspect
- retrieval finds adjacent text rather than decisive evidence

**Mitigations**

- keep source inspectability in the release gate
- score citation usefulness, not just citation presence
- include source-navigation questions in the Golden Dataset

#### 14.2.2 The unified-corpus promise fails in practice

The system may technically support multiple documents but behave like a single-document assistant if cross-document retrieval or synthesis is weak.

**Mitigations**

- include explicit multi-source questions in the Golden Dataset
- measure cross-document support behavior
- inspect retrieval diversity rather than answer text alone

### 14.3 Structural and data-quality risks

#### 14.3.1 PDF structure recovery is too weak

This is one of the dominant MVP risks. PDF text may be extractable while heading structure remains unreliable.

**Failure expression**

- incorrect section boundaries
- missing or fabricated headings
- page references detached from section context
- poor source-navigation experience

**Mitigations**

- treat section recovery as heuristic and conservative
- preserve page-level provenance even when heading inference is weak
- degrade citation quality honestly rather than inventing structure
- ensure the release gate tests weakly structured PDFs explicitly

#### 14.3.2 Markdown structural variance creates normalization issues

Markdown is easier than PDF, but not fully standardized in practice.

**Failure expression**

- malformed heading hierarchies
- front-matter and code-block handling inconsistencies
- overly literal chunking around formatting artifacts

**Mitigations**

- normalize Markdown ASTs conservatively
- include malformed but in-scope Markdown in the Golden Dataset
- keep parsing fallbacks explicit and inspectable

#### 14.3.3 Provenance breaks during transformation

A system may produce usable chunks while losing the ability to map them back to stable source references.

**Mitigations**

- enforce provenance at the schema level
- test citation resolution mechanically
- reject optimizations that improve retrieval while degrading traceability

### 14.4 Retrieval and answer-quality risks

#### 14.4.1 Chunk boundaries destroy meaning

Poor chunk segmentation can separate definitions from qualifiers, split examples from explanations, or detach a heading from the text it contextualizes.

**Mitigations**

- evaluate chunking against support quality, not only retrieval similarity
- preserve heading-path context in chunk metadata
- test both localized and synthesis questions

#### 14.4.2 Retrieval misses evidence that exists in the corpus

This is a classic false-negative risk.

**Failure expression**

- the system claims insufficient evidence even when the answer exists
- the wrong document dominates retrieval due to topical overlap

**Mitigations**

- include support-recall metrics where possible
- compare retrieval outputs directly, not only final answers
- inspect failure examples at the evidence layer

#### 14.4.3 The answer layer overgeneralizes beyond evidence

This is one of the most damaging user-trust failures.

**Failure expression**

- synthesis claims not directly supported by retrieved text
- polished answers that hide evidence gaps
- negative-case questions answered with unjustified certainty

**Mitigations**

- enforce insufficient-evidence behavior in prompts and evals
- score negative cases explicitly
- prefer partial supported answers over full speculative answers

#### 14.4.4 Citations become ornamental

A system may include citations structurally while those citations add little verification value.

**Mitigations**

- evaluate citation resolution and usefulness
- require passage-level or page-level anchors when feasible
- include source-navigation tasks as first-class evaluations

### 14.5 Execution and coordination risks

#### 14.5.1 Monolithic design bottleneck reappears informally

Even if the workflow rejects a monolithic TDD, the organization can recreate the same bottleneck by routing every decision through one person or one central document.

**Mitigations**

- keep the architecture RFC intentionally narrow
- empower domain-local ownership
- require cross-domain review only for shared-contract changes

#### 14.5.2 Evaluation becomes ceremonial rather than operational

The team may create a Golden Dataset but continue making decisions based on anecdotal demos.

**Mitigations**

- require baseline and regression comparisons for material changes
- review eval movement in domain tuning work
- track known flaky dimensions explicitly rather than ignoring them

#### 14.5.3 Skeleton quality is mistaken for product quality

The walking skeleton may work end to end yet remain far below acceptable user quality.

**Mitigations**

- treat the skeleton as an integration milestone only
- communicate clearly that heuristic tuning is still mandatory
- retain a separate release gate with explicit quality criteria

#### 14.5.4 Deferred features creep back in as hidden dependencies

This often appears as statements such as “the retrieval is not good enough without lexical search” or “source inspection is not acceptable without table parsing.”

**Mitigations**

- record deferred scope explicitly
- require evidence before promoting a deferred capability into a release blocker
- distinguish true invariant violations from local quality dissatisfaction

### 14.6 Failure taxonomy for incident and eval analysis

The team should use a lightweight defect taxonomy to classify failures consistently.

Recommended categories:

- `parse_structure_missing`
- `parse_structure_incorrect`
- `provenance_missing`
- `chunk_boundary_bad`
- `retrieval_false_negative`
- `retrieval_wrong_document`
- `citation_unhelpful`
- `answer_unsupported`
- `answer_overstated`
- `answer_should_refuse`
- `format_contract_broken`
- `job_state_incorrect`

### 14.7 Risk review cadence

Risk review does not need to be heavy. A lightweight cadence is sufficient:

- at the end of Global Contract Lock: review architectural and execution risks
- at the end of Walking Skeleton: review dominant quality risks with baseline evidence
- before Release Gate: review remaining known limitations and unresolved risk acceptance

### 14.8 Risk acceptance rule

A risk may be accepted for MVP only if all of the following are true:

- it does not violate a hard invariant
- it is visible and documented
- it does not materially mislead the user in normal in-scope use
- it has a clear rationale for deferment or tolerated limitation

---

## 15. Appendix — Mapping Back to MVP

This appendix ensures that the workflow remains anchored to the MVP document rather than evolving into an unbounded v2 program.

### 15.1 Mapping from MVP problem and goal to workflow structure

| MVP element | Workflow implication | Primary workflow sections |
|---|---|---|
| Users need to query PDF and Markdown corpora as one knowledge source | The execution model must preserve unified corpus semantics across different parsing paths | 3, 4, 6, 8, 10 |
| Answers must be grounded in uploaded documents | Groundedness becomes a system invariant, answer-contract rule, and evaluation dimension | 3, 6, 7, 9, 10 |
| Users need to inspect supporting source material | Provenance and citation contracts must be explicit and release-gated | 3, 6, 10, 14 |
| The system should validate usefulness, not solve every document-processing problem | Scope-bounded execution and deferred-decision discipline are required | 2, 4, 13, 14 |

### 15.2 Mapping from MVP in-scope capabilities to workflow phases

| MVP in-scope capability | Workflow phase where it becomes concrete |
|---|---|
| Document ingestion | Phase 1 contract lock, then Phase 3 walking skeleton |
| Structure recovery and normalization | Phase 1 section model, Phase 3 baseline implementation, Phase 4 heuristic tuning |
| Retrieval preparation | Phase 1 chunk contract, Phase 3 baseline implementation, Phase 4 tuning |
| Question answering over the corpus | Phase 1 answer contract, Phase 3 baseline implementation, Phase 4 tuning |
| Source-grounded navigation | Phase 1 citation contract, Phase 4 usability improvement, Phase 5 release gate |

### 15.3 Mapping from MVP invariants to workflow controls

| MVP invariant / hard requirement | Workflow control |
|---|---|
| Stable document identity | Shared schema lock; Platform ownership; contract tests |
| Structural integrity | Parsing heuristics bounded by section model; eval coverage for structure-sensitive cases |
| Traceability | Provenance contract; citation-resolution tests; release gate checks |
| Grounded answering | Answer-status contract; retrieval packaging; negative-case evals |
| Honest failure behavior | Prompt policy; explicit insufficient-evidence scoring; go / no-go rule |

### 15.4 Mapping from MVP out-of-scope items to workflow deferment

| MVP out-of-scope item | Workflow treatment |
|---|---|
| OCR for scanned PDFs | Deferred beyond MVP; not a release blocker unless scope changes explicitly |
| Table / figure / image handling | Deferred beyond MVP; represented as known limitation and negative-case category |
| Lexical retrieval as first-class layer | Deferred beyond MVP; do not treat as hidden prerequisite during tuning |
| Advanced hybrid retrieval / reranking sophistication | Deferred unless the release gate proves the MVP non-viable without limited adjustment |
| Summaries and synthetic questions | Deferred beyond MVP; not part of the execution critical path |
| Collaboration / external connectors / enterprise controls | Deferred beyond MVP; excluded from the artifact and release model |

### 15.5 Mapping from MVP success criteria to release evidence

| MVP success criterion | Required release evidence |
|---|---|
| Upload a small collection of PDFs and Markdown files | Demonstrated walking-skeleton and release-candidate ingestion behavior |
| Ask a question over the collection | End-to-end functional validation |
| Receive answer based primarily on retrieved source content | Golden Dataset groundedness results and manual audit samples |
| Inspect which source documents and sections informed the answer | Citation-resolution evidence and source-navigation checks |
| Understand when the corpus lacks enough evidence | Negative-case evaluation results and refusal-behavior checks |

### 15.6 Mapping from MVP non-goals to execution discipline

The MVP non-goals imply the following workflow discipline.

- Do not turn parsing into a generic PDF-understanding program.
- Do not treat exhaustive correctness across all question types as the release bar.
- Do not turn the service into a web-grounded research agent.
- Do not expand the format-support matrix during MVP execution.

### 15.7 How to use this appendix

This appendix should be used whenever the team faces a scope or prioritization dispute.

A useful test is:

1. identify the contested item
2. locate the corresponding MVP constraint or success criterion
3. determine whether the workflow already accounts for it
4. decide whether the item is a release blocker, a tuning topic, or a deferred concern

If the item cannot be justified by the MVP problem, goal, scope, or invariants, it is very likely not part of the MVP critical path.

---

## End of Workflow Document

Sections 1–15 together define the intended post-framing execution model for the MVP. The next step after this document is not another broad planning pass; it is to instantiate the artifact set, lock the shared contracts, and begin building the Golden Dataset and walking skeleton in parallel.
