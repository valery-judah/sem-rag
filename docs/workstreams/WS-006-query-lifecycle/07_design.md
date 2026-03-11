# Query Lifecycle Architecture Draft

## 1. Architectural intent

The query subsystem exists to implement the MVP product promise for grounded question answering over an uploaded bounded corpus.

This is not a generic chat-over-files subsystem. Its purpose is to enforce the following properties end to end:

- answers are constrained by the active uploaded corpus rather than hidden external knowledge;
- user-visible claims remain within what retrieved evidence actually supports;
- the system can qualify, narrow, or abstain when evidence is partial, weak, conflicting, or absent;
- returned citations are inspectable at MVP granularity;
- query-path failures remain localizable to the correct stage rather than disappearing into a single opaque prompt step.

The subsystem must therefore preserve the normative query path as explicit runtime structure:

`Interpret -> Retrieve -> Select -> Assemble Context -> Assess Support -> Decide Answer Mode -> Generate -> Cite or Abstain`

This sequence is not documentation-only guidance. It is the semantic backbone of the implementation. In particular:

- **Assess Support** must remain a first-class runtime concern rather than an implicit side effect of generation;
- **Decide Answer Mode** must remain explicit so the system can enforce downgrade-only behavior after support has been assessed;
- later stages may preserve or narrow answer posture, but they must not widen it beyond what the evidence supports.

The architecture should optimize for correctness of support semantics, inspectability, and MVP invariants rather than latency or distributed scalability. Because the goal is a local Docker-based MVP, the preferred design is one service with strong internal contracts rather than multiple services with weak semantic boundaries.

Compatibility with the document lifecycle is a hard requirement. The query subsystem must assume and consume the existing document-side guarantees:

- stable document identity;
- persisted normalized artifacts;
- persisted sections and chunks;
- recoverable provenance;
- readiness semantics tied to persisted index publication and smoke-checked retrieval;
- `READY` as the only state from which documents may participate in answering.

## 2. Topology

### 2.1 Deployment shape

The subsystem should run inside the existing local Docker-based Python/FastAPI application as part of the same codebase and process boundary as the document lifecycle.

Recommended MVP topology:

- one FastAPI application;
- one Postgres database as the primary persistence layer;
- the existing filesystem artifact storage used by the document lifecycle;
- one query domain inside the service;
- one inference adapter layer for embeddings and LLM calls;
- internal HTTP endpoints only.

This preserves simplicity while keeping semantic stage boundaries explicit in code and persistence.

### 2.2 Why one service

The one-service design is the correct MVP choice because it:

- keeps local deployment simple;
- minimizes operational complexity;
- avoids introducing network boundaries before the semantic contracts are stable;
- makes debugging and trace inspection easier;
- allows direct reuse of the document-lifecycle persistence model, readiness predicate, chunk representations, and provenance-bearing metadata.

The architecture must not split the query subsystem into separate services merely to mirror conceptual stages. Stages should be explicit in contracts, traces, and modules, but not prematurely externalized into infrastructure boundaries.

### 2.3 Data and storage shape

The service should continue to use the same broad storage split already established by the document lifecycle:

- **Postgres** for metadata, vectors, stage traces, query results, and inspectable runtime state;
- **filesystem artifacts** for document-side raw and normalized artifacts, remaining owned by the document lifecycle.

The query subsystem should not become the owner of raw file artifacts. It should consume document-derived read models and provenance-bearing retrieval records.

### 2.4 Queryability boundary

Only documents in `READY` state may be considered queryable.

This rule is non-negotiable because it protects trust semantics:

- a document that is extracted but not structurally persisted is not query-ready;
- a document that is chunked but not indexed is not query-ready;
- a document that lacks stable provenance or readiness confirmation must not silently leak into answer generation.

The query subsystem must treat `READY` as the hard boundary between “ingested but not trustworthy for answering” and “allowed evidence source.”

## 3. Primary bounded contexts

The query architecture should be organized into bounded contexts derived from semantics, not from framework layers.

### 3.1 Document read model

This is the query-facing read surface over document-lifecycle outputs.

Responsibilities:

- expose queryable `READY` documents;
- expose sections, chunks, and provenance-bearing metadata;
- expose indexing and retrieval-readiness state;
- provide stable identifiers and source-local locators;
- shield query logic from raw persistence schema details.

This context is read-only from the query subsystem’s perspective. It does not own document mutation, retries, or lifecycle transitions.

### 3.2 Query lifecycle domain

This is the semantic center of the query subsystem.

Responsibilities:

- interpret user questions;
- retrieve evidence-bearing candidates;
- rerank/select candidates;
- construct explicit evidence sets;
- assemble a deterministic context window;
- assess support against requested answer shape;
- decide the correct answer mode;
- generate grounded answer text;
- produce citation-ready fragment linkage.

This domain owns the end-to-end query path and the invariants that must survive all implementation changes.

### 3.3 Inference adapters

This context encapsulates model-facing operations.

Responsibilities:

- query embedding generation;
- optional learned reranking later;
- structured LLM calls for interpretation, support assessment, answer-mode assistance, and grounded generation;
- schema validation around model outputs.

Inference adapters must not become the architectural center of gravity. Model providers may change. The semantic stage contracts must remain stable.

### 3.4 Query trace and review surface

This context persists the runtime explanation of what happened during a query.

Responsibilities:

- persist stage outputs;
- persist rankings, evidence sets, and context manifests;
- persist support-state decisions and answer-mode decisions;
- persist final answer text and citation bundles;
- preserve enough information to reproduce failure localization and evaluation outcomes.

This context exists because a fluent answer is not sufficient proof of correctness. Review, debugging, regression, and eval work all require inspectable traces.

## 4. Runtime flow

A synchronous query request should execute the following runtime path.

### 4.1 Intake and boundary validation

The service accepts:

- natural-language user question;
- workspace or equivalent corpus boundary;
- optional runtime policy config;
- optional user-visible answer preferences if supported later.

Before interpretation begins, the service must validate:

- the workspace exists;
- the request is authorized to see that workspace;
- the active query corpus is bounded and known;
- only `READY` documents are eligible for retrieval.

### 4.2 Interpretation

The question is transformed into a structured, retrieval-ready representation that preserves:

- answer-shape implications;
- scope and specificity;
- whether the request is asking for explanation, location, comparison, or synthesis;
- whether the request appears to depend on unsupported MVP capabilities.

Interpretation should be schema-driven and constrained. It does not decide support. It prepares downstream stages to behave correctly.

### 4.3 Retrieval

The service retrieves passage-first evidence candidates from the active `READY` corpus.

Retrieval must preserve:

- stable document/chunk identity;
- structure context such as section or heading path;
- source-local provenance such as page range or stable markdown locator;
- raw retrieval score and rank.

Retrieval returns candidates, not conclusions.

### 4.4 Selection and reranking

Retrieved candidates are reranked and filtered to improve answerability rather than merely topical similarity.

The selection stage should optimize for:

- support completeness;
- local coherence;
- correct source targeting;
- diversity when synthesis is required;
- duplicate suppression;
- recoverability of provenance.

This stage prepares explicit evidence sets rather than relying on a naive top-k prompt dump.

### 4.5 Evidence-set construction

Selected candidates are organized into explicit evidence sets.

An evidence set may be:

- a single passage that directly supports a narrow factual answer;
- a passage plus adjacent supporting passage for local coherence;
- multiple passages from the same document for section-scoped explanation;
- multiple passages across documents for synthesis;
- a deliberate conflicting-source set when material divergence is detected.

This is the stage that converts “related retrieved text” into “supportable evidence structure.”

### 4.6 Context assembly

The service builds an ordered, budgeted context from the selected evidence sets.

Context assembly must be explicit about:

- ordering rules;
- duplicate suppression;
- inclusion of structural scaffolding such as headings when useful;
- intentional truncation when prompt budget is reached;
- which evidence sets were dropped and why.

The unit of truncation should normally be the lower-value evidence set, not arbitrary clipping through already selected support.

### 4.7 Support assessment

The assembled evidence is evaluated against the requested answer shape.

Support assessment must determine whether the query is:

- `SUPPORTED`;
- `PARTIALLY_SUPPORTED`;
- `UNSUPPORTED_IN_CORPUS`;
- `UNSUPPORTED_QUESTION_TYPE`;
- `AMBIGUOUS_OR_CONFLICTING`.

This stage must evaluate support sufficiency, not just topical relevance.

### 4.8 Answer-mode decision

The service translates the support state into answer posture.

Required behavior:

- `SUPPORTED` -> direct answer with inspectable citation support;
- `PARTIALLY_SUPPORTED` -> narrow or qualify the answer;
- `UNSUPPORTED_IN_CORPUS` -> abstain or state that the corpus lacks enough support;
- `UNSUPPORTED_QUESTION_TYPE` -> explicit capability-boundary response;
- `AMBIGUOUS_OR_CONFLICTING` -> surface disagreement or uncertainty.

Answer mode is a guardrail between support assessment and generation. It exists to prevent the generator from broadening or overclaiming.

### 4.9 Grounded generation

The generator renders user-visible answer text constrained by:

- answer mode;
- supportable evidence only;
- provenance and citation candidates;
- explicit unsupported boundaries when present.

Generation may paraphrase and synthesize only when the support state permits it.

### 4.10 Citation rendering

The service maps answer fragments to evidence anchors and renders inspectable citations.

Minimum MVP provenance expectations:

- **PDF**: document identity plus page;
- **Markdown**: document identity plus heading path, section path, or equivalent stable local locator;
- **cross-document synthesis**: one usable citation per materially contributing source.

### 4.11 Trace persistence and response

The service persists the full query trace and returns:

- answer text;
- support state;
- answer mode;
- visible limitations when applicable;
- inspectable citations;
- query identifier for later trace or replay.

## 5. Core domain objects

The subsystem should make the core semantic objects explicit in code, ideally as internal domain models and Pydantic contracts.

### 5.1 QueryRequest

Represents the incoming request.

Suggested fields:

- `query_id`
- `workspace_id`
- `user_text`
- `runtime_policy`
- `requested_answer_shape`
- `created_at`

### 5.2 InterpretedQuery

Represents the structured output of interpretation.

Suggested fields:

- `normalized_text`
- `query_type`
- `retrieval_plan`
- `specificity`
- `needs_synthesis`
- `needs_source_navigation`
- `scope_flags`
- `answer_shape`
- `unsupported_capability_flags`

This object is the semantic bridge from user language to retrieval behavior.

### 5.3 RetrievedCandidate

Represents one retrievable evidence-bearing result.

Suggested fields:

- `candidate_id`
- `doc_id`
- `chunk_id`
- `section_id`
- `score`
- `rank`
- `heading_path`
- `page_start`
- `page_end`
- `ordinal`
- `text`
- `source_type`
- `metadata`

This object must remain traceable and citation-capable.

### 5.4 EvidenceUnit

Represents the minimal evidence-bearing unit used downstream.

Usually this is a passage, optionally enriched with:

- section or heading context;
- neighboring text;
- source-local locators;
- source type;
- structural labels;
- chunk provenance.

### 5.5 EvidenceSet

Represents one or more evidence units sufficient to support a claim or answer fragment.

Suggested fields:

- `evidence_set_id`
- `purpose`
- `units`
- `supporting_claims`
- `completeness_score`
- `conflict_flags`
- `coverage_notes`

The evidence set is critical because support often depends on grouped evidence rather than isolated passages.

### 5.6 ContextManifest

Represents the actual assembled prompt context.

Suggested fields:

- `ordered_items`
- `included_evidence_set_ids`
- `dropped_evidence_set_ids`
- `token_budget`
- `assembly_reasons`
- `truncation_reasons`
- `duplicate_suppression_notes`

This object is needed for determinism, debugging, and evaluation.

### 5.7 SupportAssessment

Represents the support-state judgment.

Suggested fields:

- `support_state`
- `rationale`
- `supported_subquestions`
- `unsupported_gaps`
- `conflicting_sources`
- `required_citation_shape`
- `confidence_notes`

This object is not optional. It is the primary semantic control point for honest answering.

### 5.8 AnswerModeDecision

Represents the allowed posture for final rendering.

Suggested fields:

- `mode`
- `allowed_scope`
- `qualification_rules`
- `abstention_kind`
- `must_surface_conflict`
- `citation_requirement`

### 5.9 AnswerDraft

Represents generated answer output before final API rendering.

Suggested fields:

- `text`
- `visible_limitations`
- `fragment_links`
- `render_warnings`

### 5.10 CitationBundle

Represents the rendered provenance attached to answer content.

Suggested fields:

- `answer_fragment_id`
- `anchors`
- `doc_titles`
- `locators`
- `support_role`
- `inspection_notes`

## 6. Stage implementations

### 6.1 Interpretation stage

Recommended implementation:

- one structured LLM call with a strict response schema;
- deterministic normalization and policy checks after model output;
- minimal heuristics for obvious boundary detection and normalization.

This stage must preserve distinctions that materially affect downstream behavior, including:

- direct factual lookup;
- section-scoped explanation;
- one-document synthesis;
- cross-document synthesis;
- source-navigation requests;
- unsupported question-type cases.

It must not silently broaden the question or reduce a precise request into generic topical retrieval.

### 6.2 Retrieval stage

Recommended implementation:

- dense-first retrieval over passage vectors;
- hard filter to `READY` documents in the active workspace;
- metadata-preserving retrieval output;
- no use of external-world search.

Passage-first retrieval is the default because passages are the MVP evidence-bearing retrieval unit. Sections remain semantic containers and citation scaffolding, not the default retrieval unit.

### 6.3 Selection and reranking stage

Recommended initial implementation:

- heuristic reranking rather than a neural cross-encoder;
- deterministic tie-breaking;
- explicit duplicate suppression.

Primary reranking signals:

- lexical or semantic closeness to the interpreted query;
- heading/path relevance;
- local coherence potential;
- evidence completeness;
- diversity for synthesis tasks;
- source-navigation precision;
- provenance quality.

The goal is not only “most similar text.” The goal is “best supportable evidence candidates.”

### 6.4 Evidence-set builder

This stage should convert reranked candidates into meaningful support structures.

Required capabilities:

- single-passage support for narrow factual answers;
- neighboring-passage expansion where local coherence matters;
- multi-passage same-document grouping for explanations;
- cross-document grouping for synthesis;
- conflict-aware grouping when sources diverge.

The builder should prefer explicit evidence grouping over implicit prompt-side assumptions.

### 6.5 Context assembly stage

Recommended implementation principles:

- deterministic ordering of included material;
- explicit budget accounting;
- preserve headings and source-local scaffolding when they improve inspection or comprehension;
- suppress near-duplicate passages;
- drop lower-value evidence sets first when the budget is exceeded;
- record all inclusion and exclusion reasons.

The context assembler owns prompt composition mechanics, but not support-state judgment.

### 6.6 Support assessment stage

Recommended implementation:

- hybrid approach;
- deterministic pre-checks for obvious unsupported question types and provenance insufficiency;
- structured LLM judgment over interpreted query plus evidence sets plus context manifest;
- deterministic post-rules that can preserve or narrow, but never widen, support.

This stage must judge evidence sufficiency against the requested answer shape. It must not treat retrieval success as evidence sufficiency.

### 6.7 Answer-mode decision stage

Recommended implementation:

- deterministic mapping from support state to allowed posture;
- explicit handling of direct answer, narrowed answer, qualified answer, full abstention, scoped abstention, and qualified uncertainty;
- optional generation hints derived from the chosen posture.

This stage should be implemented as policy logic, not as a prompt suggestion.

### 6.8 Generation stage

Recommended implementation:

- one grounded generation call that consumes answer mode and supportable evidence only;
- structured fragment linkage output where feasible;
- no hidden widening of answer scope.

Generation rules:

- supported content may be paraphrased;
- synthesis is allowed only when support covers the synthesis;
- partial support must remain visible in the wording;
- conflict must not be flattened into false consensus;
- unsupported gaps must not be silently filled from model priors.

### 6.9 Citation rendering stage

Recommended implementation:

- derive citations from stored provenance, not from model invention;
- attach answer fragments to one or more evidence anchors;
- preserve multi-source bundles where multiple sources materially contribute.

Citation quality requirements:

- correct contributing document;
- useful inspection point at MVP granularity;
- materially consistent with the claim;
- no fabricated page, heading, or section references;
- no omission of required contributing sources in synthesis cases.

## 7. Persistence model

The query subsystem should persist stage artifacts in Postgres so that behavior remains inspectable and replayable.

### 7.1 Query run records

Suggested table: `query_run`

Purpose:

- one durable record per query request;
- links the final answer to the complete runtime trace;
- stores workspace boundary, timestamps, and terminal status.

Suggested columns:

- `id`
- `workspace_id`
- `user_text`
- `requested_answer_shape`
- `status`
- `created_at`
- `completed_at`
- `config_snapshot_json`

### 7.2 Interpretation records

Suggested table: `query_interpretation`

Purpose:

- persist structured interpretation output;
- preserve answer-shape and scope assumptions used downstream.

### 7.3 Retrieval candidate records

Suggested table: `query_retrieval_candidate`

Purpose:

- persist all retrieved candidates, not only winners;
- preserve ranking and provenance;
- support debugging of retrieval misses and thresholding errors.

### 7.4 Evidence set records

Suggested tables:

- `query_evidence_set`
- `query_evidence_set_member`

Purpose:

- persist explicit evidence grouping;
- preserve how supportable units were formed;
- enable review of grouping quality and conflict handling.

### 7.5 Context manifest records

Suggested tables:

- `query_context_manifest`
- `query_context_item`

Purpose:

- persist the actual ordered context seen by the generator;
- preserve dropped evidence, truncation reasons, and deterministic ordering decisions.

### 7.6 Support assessment records

Suggested table: `query_support_assessment`

Purpose:

- persist the canonical support-state decision;
- preserve rationale and unsupported gaps;
- make answer-policy debugging possible.

### 7.7 Answer mode records

Suggested table: `query_answer_mode`

Purpose:

- record the chosen answer posture independently from generation;
- allow inspection of whether generation violated policy.

### 7.8 Answer records

Suggested table: `query_answer`

Purpose:

- store final answer text and visible limitations;
- support replay, comparison, and review.

### 7.9 Fragment-to-evidence linkage records

Suggested table: `query_answer_fragment_link`

Purpose:

- preserve evidence-to-answer traceability at fragment granularity where available;
- support citation rendering and review.

### 7.10 Citation records

Suggested table: `query_citation`

Purpose:

- persist final citation bundles and rendered locators;
- make provenance defects inspectable.

### 7.11 Failure and diagnostic records

Suggested table: `query_failure`

Purpose:

- preserve primary trust failure labels and secondary diagnostic causes;
- support evaluation and targeted engineering response.

At minimum, the query subsystem should be able to represent failures such as:

- unsupported answer;
- partially supported answer presented as complete;
- wrong abstention;
- failed abstention;
- provenance missing or too weak;
- incorrect provenance;
- ingestion or structure defect visible in answer quality;
- scope-boundary failure.

## 8. FastAPI surface

The HTTP surface should remain internal for MVP.

### 8.1 `POST /queries`

Runs the full synchronous query lifecycle.

Request body should include:

- workspace or corpus boundary;
- user question;
- optional policy or debug flags.

Response should include:

- `query_id`
- `answer`
- `support_state`
- `answer_mode`
- `visible_limitations`
- `citations`

### 8.2 `GET /queries/{query_id}`

Returns a summary view of a completed query run.

Suggested purpose:

- operator inspection;
- test harness lookup;
- debugging of prior runs.

### 8.3 `GET /queries/{query_id}/trace`

Returns the stage-level trace.

Suggested contents:

- interpretation output;
- retrieval candidates;
- evidence sets;
- context manifest;
- support assessment;
- answer mode;
- answer text;
- citations;
- timings.

### 8.4 `GET /queries/{query_id}/citations`

Returns normalized citation objects detached from the full trace.

This is useful for validation and inspection tooling.

### 8.5 `POST /queries/{query_id}/replay`

Optional internal endpoint to rerun a query against the same boundary and config snapshot.

This is useful for regression and operator debugging, especially while the subsystem is still being hardened.

### 8.6 API design notes

The API should remain a thin transport layer. The domain contracts are primary. The internal HTTP surface exists to support runtime and operator workflows, not to define the product’s permanent public API.

## 9. Package layout

A practical package layout should preserve bounded contexts and stage contracts without over-fragmenting the codebase.

Suggested target structure within the existing service/package:

```text
src/<app>/
  app/
    api.py
    deps.py
    settings.py

  query/
    service.py
    policies.py
    errors.py

    contracts/
      requests.py
      trace.py
      citations.py

    domain/
      query.py
      interpreted_query.py
      evidence.py
      context_manifest.py
      support.py
      answer_mode.py
      answer.py
      citation.py

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

    persistence/
      models.py
      repositories.py

    review/
      diagnostics.py
      failure_labels.py
      replay.py

  readmodels/
    documents.py
    chunks.py
    provenance.py

  inference/
    embeddings.py
    llm.py
    schemas.py
```

This is a target internal module layout for the future query subsystem inside the existing service, not a statement of current implementation.
