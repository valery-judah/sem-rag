---
artifact_kind: requirements
id: WS-006-R1
title: Query Lifecycle Requirements
status: draft
created: 2026-03-11
updated: 2026-03-11
---

# Query Lifecycle Requirements

## Purpose
Define the requirements for staged delivery of the MVP query lifecycle.

This artifact is a workstream planning document. It must stay aligned with:

- `docs/evergreen/mvp.md` for product scope
- `docs/evergreen/architecture.md` for current implementation truth
- `docs/delivery/workflow.md` for the conceptual lifecycle model
- `docs/evergreen/eval-vocabulary.md` for canonical evaluation terminology
- `docs/evergreen/eval-support-semantics.md` and `docs/evergreen/eval-scenario-taxonomy.md` for canonical support-state and scenario meanings
- `docs/workstreams/WS-003-seed-corpus/21_critical_failures.md` for the MVP trust-priority failure set

It does not create a public API contract or broaden MVP scope.

## Problem statement
The repo already contains internal retrieval and answer-related seams:

- `src/parity/retrieval.py` provides a demo retriever
- `src/parity/app/api.py` exposes an internal document-scoped retrieval smoke route
- `src/parity/_contracts/models.py` defines internal `Answer`, `RetrievalHit`, and `SourceReference` shapes

Those seams do not yet add up to the MVP query lifecycle described in `docs/delivery/workflow.md`.

There is no implemented end-to-end path that:

- accepts a user question over the bounded corpus,
- retrieves evidence across one or more relevant documents,
- selects evidence sets suitable for support,
- assembles ordered context within a budget,
- produces a grounded answer,
- and returns useful citations or an explicit abstention.

The workstream goal is to turn the currently partial query path into an implemented evidence-constrained lifecycle that preserves support semantics, traceability, and honest failure behavior.

## Outcome
WS-006 is complete when the system can accept an MVP-scoped natural-language question over an ingested corpus, retrieve and assemble supportable evidence, return a grounded answer with inspectable citations when support is sufficient, and otherwise narrow scope or abstain without fabricating support.

## Scope
### In scope
- query handling over the bounded ingested corpus
- evidence retrieval from one or more documents
- retrieval-unit selection and reranking policy
- context assembly with ordering, deduplication, and budget discipline
- grounded answer generation constrained by retrieved evidence
- citation rendering at useful MVP granularity
- explicit insufficient-evidence behavior
- validation across retrieval, context, answer, and failure quality

### Out of scope
- stable public HTTP, CLI, or package API commitments
- strong compare-and-contrast behavior across all viewpoints
- exact scholarly citation formatting
- rich table, figure, diagram, or image-based question answering
- advanced hybrid retrieval tuning or lexical retrieval as a first-class MVP requirement
- deliberate source diversification or exhaustive retrieval guarantees over very large corpora
- user-facing answer UI design beyond the runtime semantics needed to support inspection

## Requirements
### R1. Query lifecycle coverage
The implemented runtime must realize the conceptual query lifecycle from `docs/delivery/workflow.md`:

`Interpret -> Retrieve -> Select/Rerank -> Assemble Context -> Generate -> Cite or Abstain`

The workstream may refine execution details, but it must not collapse retrieval, support judgment, and answer rendering into an opaque single step that loses inspectability.

### R2. Corpus-bounded query intake
The system must accept natural-language questions against the bounded ingested corpus for a workspace or equivalent ownership boundary.

For MVP:

- questions are answered only from uploaded PDF and Markdown corpus content
- the system must not rely on external-world knowledge as hidden support
- query handling must remain explicitly corpus-bounded even if prompts or models contain broader priors

### R3. Query-intent acknowledgment
The lifecycle must preserve an explicit place for query interpretation, even if the first implementation keeps it lightweight.

At minimum, interpretation must support downstream distinctions that matter for delivery pressure:

- direct factual lookup
- section-scoped explanation
- one-document synthesis
- cross-document synthesis
- source navigation
- insufficient-evidence cases

The runtime does not need a heavyweight classifier for MVP, but it must not erase the intent distinctions needed for retrieval, context assembly, and abstention behavior.

### R4. Evidence-first retrieval
Retrieval must operate over evidence-bearing units derived from the document lifecycle rather than raw untraceable text blobs.

For MVP:

- passages remain the default retrieval unit
- section or heading metadata may supplement retrieval and later citations
- evidence may span one or more documents
- retrieval must preserve enough identity to resolve results back to document, chunk, and source context

### R5. Retrieval-unit hierarchy and semantics
The query lifecycle must respect the workflow retrieval hierarchy:

`DOCUMENT -> SECTION -> PASSAGE`

At minimum:

- sections remain structural containers rather than the default retrieval unit
- passages remain the primary retrievable evidence unit
- neighbors may be expanded for coherence without erasing the underlying passage identity
- section headers or metadata may be attached as context scaffolding

This requirement exists to keep retrieval, citation, and source inspection semantically aligned.

### R6. Selection and reranking discipline
After initial retrieval, the lifecycle must select and rerank evidence in a way that improves support quality rather than only score order.

At minimum, selection logic must account for:

- relevance to the question
- support completeness versus isolated fragments
- coherence within section or neighbor context
- duplicate or near-duplicate suppression
- multi-document evidence when the answer requires it

The runtime may remain simple for MVP, but it must make selection behavior explicit enough to validate and tune.

### R7. Evidence-set assembly
The system must support answers whose support comes from one evidence unit or from an evidence set.

At minimum:

- one-passage factual answers must be representable
- locally coherent explanations may combine passage plus section context
- synthesis answers may combine several passages across one or more documents

The answer path must not assume one claim maps to exactly one passage.

### R8. Context assembly quality
The lifecycle must assemble a context window from retrieved evidence with explicit ordering and budget rules.

Context assembly must:

- preserve deterministic ordering semantics
- include adjacent or neighboring evidence only when it improves local coherence
- remove redundant overlap where practical
- retain section or heading context when needed to interpret the passage correctly
- fit the configured prompt budget without silently dropping crucial support

Good retrieval must not be degraded into bad generation by accidental context construction.

### R9. Grounded answer generation
The generation step must produce answer text constrained by retrieved evidence rather than unsupported model inference.

At minimum:

- supported answers must be materially grounded in the assembled context
- answer text may synthesize across sources when the evidence warrants it
- the system must not overstate what the evidence supports
- answer generation must preserve enough linkage to explain why the answer was returned

For evaluation and review, supported answers and unsupported answers should use the meanings from `docs/evergreen/eval-vocabulary.md` rather than local synonyms.

### R10. Citation rendering and source inspection
Supported answers must include inspectable citations at useful MVP granularity.

For MVP, citations must resolve through recoverable provenance such as:

- document identity and title
- chunk or passage identity when retained
- section identity or heading path when recoverable
- page label or coarse page location when recoverable
- supporting snippet text

Exact span-perfect anchors are not required, but citations must remain useful for source navigation and trust.

### R11. Explicit insufficient-evidence behavior
The lifecycle must support honest non-answer behavior when the corpus does not sufficiently support the requested claim.

At minimum:

- insufficient support must produce an explicit abstention, scope narrowing, or equally honest insufficiency response
- unsupported answers must not include fabricated citations
- the system must avoid false confidence under degraded retrieval or fragmented evidence
- insufficient-evidence handling must align with canonical support-state meanings rather than ad hoc local labels

### R12. Evidence-to-claim traceability
The query path must preserve enough traceability to audit user-visible answers against retrieved evidence.

For MVP this requires:

- retained linkage from answer citations to retrieved evidence units
- retained linkage from evidence units to underlying document provenance
- inspectable support rationale at the answer level even without exact claim-span annotations

MVP does not require precise claim-to-citation span binding, but it does require auditable support.

### R13. Deterministic ordering and stable behavior
Given identical corpus content, configuration, and retrieval inputs, the lifecycle should behave deterministically where feasible and otherwise remain structurally stable enough for regression analysis.

At minimum:

- retrieval result ordering rules must be explicit
- tie handling must be deterministic
- deduplication behavior must be intentional
- context assembly order must not depend on incidental runtime iteration order

### R14. Failure handling by layer
The runtime must preserve failure quality by making query-path failures inspectable at the right layer.

At minimum, delivery must distinguish trust-priority primary failures from lower-level diagnostic causes.

Primary MVP failures must be representable in validation and review using the critical-failure framing:

- `U1` unsupported answer
- `U2` partially supported answer presented as complete
- `A1` wrong abstention
- `A2` failed abstention
- `P1` provenance missing or too weak to inspect
- `P2` incorrect provenance
- `I1` ingestion or structure failure visible in answer quality
- `S1` scope-boundary failure

Diagnostic layering may still distinguish failures such as:

- retrieval miss or low-quality evidence discovery
- evidence fragmentation or poor unit boundaries
- context assembly degradation
- unsupported claims or answer overreach
- citation mismatch or non-inspectable provenance

The system must fail locally and explicitly rather than returning a globally confident but weakly supported answer.

### R15. Validation surface
Each query-lifecycle stage must have validation evidence at the same semantic level as the requirement it satisfies.

Minimum validation expectations:

- contract tests for answer, citation, and retrieval-hit shapes
- retrieval tests that prove evidence ordering and traceability behavior
- scenario-driven tests covering factual lookup, section-scoped explanation, one-document synthesis, cross-document synthesis, source navigation, and insufficient-evidence cases
- failure-path tests that distinguish retrieval, context, answer, and citation failures
- review or harness outputs that can map user-visible failures onto `U1/U2/A1/A2/P1/P2/I1/S1`

## Delivery stages
### Stage 1. Query intake and evidence retrieval
Goal:
Make corpus-bounded question handling real enough to retrieve traceable evidence units from ingested content.

Must deliver:

- query intake over the bounded corpus
- retrieval over persisted evidence-bearing units
- explicit retrieval result identity and ordering semantics
- initial coverage for one-document and cross-document retrieval paths

Exit signal:
Representative questions can retrieve traceable evidence units from the corpus with deterministic ordering and inspectable provenance.

### Stage 2. Selection, reranking, and context assembly
Goal:
Turn raw retrieval hits into support-oriented evidence sets and ordered generation context.

Must deliver:

- explicit selection or reranking policy
- neighbor or section-context expansion where justified
- context assembly with deduplication and budget discipline
- validation proving good retrieval is preserved into usable context

Exit signal:
Representative scenarios produce ordered, budget-constrained context windows that preserve the support needed for answer generation.

### Stage 3. Grounded answering and citation rendering
Goal:
Produce answer outputs that expose support rather than hiding it.

Must deliver:

- grounded answer generation from assembled context
- supported-answer citation rendering
- citation payloads usable for inspection
- multi-source answer behavior within MVP scope

Exit signal:
Representative supported scenarios return answer text plus inspectable citations that resolve back to the retrieved evidence.

### Stage 4. Honest insufficiency and layered validation
Goal:
Make failure quality part of the runtime contract instead of a best-effort fallback.

Must deliver:

- explicit insufficient-evidence answer path
- prevention of fabricated or mismatched citations on unsupported answers
- validation across insufficient-evidence and degraded-retrieval scenarios
- failure classification evidence that localizes query-path breakdowns

Exit signal:
Representative unsupported or degraded scenarios abstain or narrow scope honestly, without unsupported claims or fabricated provenance.

## Invariants
- Query behavior must remain bounded to the uploaded corpus for MVP.
- Passages are the default retrievable evidence unit; sections are structural containers, not interchangeable text blobs.
- Evaluation terminology should prefer `passage`, `anchor`, `citation`, `support state`, `supported answer`, `unsupported answer`, and `abstention` for user-visible query semantics.
- Supported answers must include inspectable citations.
- Insufficient-evidence answers must not fabricate support.
- Retrieval, selection, and context assembly must preserve deterministic ordering semantics.
- Evidence used for answering must remain traceable back to recoverable document provenance.
- Coarse provenance is acceptable for MVP; missing provenance is not.

## Dependencies
- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/delivery/workflow.md`
- `docs/evergreen/eval-vocabulary.md`
- `docs/evergreen/eval-support-semantics.md`
- `docs/evergreen/eval-scenario-taxonomy.md`
- `docs/evergreen/eval-failure-taxonomy.md`
- `docs/workstreams/WS-003-seed-corpus/21_critical_failures.md`
- `src/parity/_contracts/models.py`
- `src/parity/retrieval.py`
- `src/parity/app/api.py`
- `src/parity/evaluation/`

## Open questions
- Should MVP query execution operate corpus-wide immediately, or should it temporarily route through document-scoped retrieval seams while the broader query path is being built?
- How much explicit intent handling is necessary before retrieval and context assembly improve materially over a single generic query path?
- Where should support sufficiency be decided in code: before generation, during answer rendering, or through a hybrid policy that keeps insufficiency behavior explicit?
- What is the smallest citation payload that still satisfies source-navigation trust for both Markdown and coarse-PDF provenance?
