Below is the architecture draft I would use for the query lifecycle, given your decisions and the existing document-lifecycle design.

The governing shape is straightforward: one local FastAPI service, synchronous query execution, retrieval only from `READY` documents, passage-first evidence retrieval, explicit evidence sets, explicit support assessment, explicit answer-mode selection, and persisted traces so failures remain inspectable at the correct layer. That aligns with the document-lifecycle architecture already chosen for MVP: single-node Python service, internal HTTP endpoints, Postgres-backed persistence, filesystem artifacts, strict readiness semantics, and real retrieval over provenance-bearing chunks.   

## 1. Architectural intent

The architecture should preserve the normative query path as first-class runtime structure, not as prompt choreography: `Interpret -> Retrieve -> Select -> Assemble Context -> Assess Support -> Decide Answer Mode -> Generate -> Cite or Abstain`. The requirements are explicit that support assessment and answer-mode selection must not disappear inside generation, and that later stages may narrow posture but must not widen it beyond assessed support.   

The resulting design goal is not “fast chat over files.” It is a bounded-corpus answer engine whose internal seams correspond to evaluation seams: representation quality, retrieval quality, context quality, answer quality, provenance quality, and abstention quality. That is the right compatibility point with the workflow and the query contract.  

## 2. Topology

I would keep query lifecycle in the same service codebase as document lifecycle, but as a separate domain/module set. The document side remains responsible for producing stable, provenance-bearing retrieval units and a strict `READY` predicate. The query side consumes only those `READY` units and never reaches into pre-ready artifacts.  

```text
+---------------------------------------------------------------+
| Local Docker node                                             |
|                                                               |
|  +------------------- FastAPI ------------------------------+ |
|  |                                                         | |
|  |  Document endpoints     Query endpoints                 | |
|  |  /documents/*           /queries                        | |
|  |                         /queries/{id}                   | |
|  |                         /queries/{id}/citations         | |
|  |                         /queries/{id}/trace             | |
|  +------------------------------+--------------------------+ |
|                                 |                            |
|                                 v                            |
|                    +-----------------------------+           |
|                    | QueryLifecycleService       |           |
|                    |-----------------------------|           |
|                    | Interpret                   |           |
|                    | Retrieve                    |           |
|                    | Select / Rerank             |           |
|                    | Build Evidence Sets         |           |
|                    | Assemble Context            |           |
|                    | Assess Support              |           |
|                    | Decide Answer Mode          |           |
|                    | Generate                    |           |
|                    | Render Citations            |           |
|                    +-------------+---------------+           |
|                                  |                           |
|          +-----------------------+------------------------+  |
|          |                                                |  |
|          v                                                v  |
|  +--------------------+                         +--------------------+
|  | PostgreSQL         |                         | Model adapters     |
|  | documents/chunks   |                         | embeddings / LLM   |
|  | query traces       |                         | structured calls   |
|  | vectors / metadata |                         +--------------------+
|  +--------------------+                                        |
|                                                                |
|     Filesystem artifacts remain on document-lifecycle side     |
+---------------------------------------------------------------+
```

This keeps the service boundary simple while preserving internal stage boundaries that are inspectable and testable, which both the workflow and query requirements treat as mandatory.  

## 3. Primary bounded contexts

I would split the code internally into four bounded areas.

**Document Read Model**
Read-only query-facing access to `Document`, `Section`, `Chunk`, `IndexEntry`, provenance metadata, and readiness. This is an adapter over the existing document-lifecycle persistence model, not a second source of truth. The document design already establishes those durable entities and the meaning of `READY`.  

**Query Lifecycle**
Owns stage orchestration for interpretation, retrieval, evidence selection, support assessment, answer-mode decision, generation, and citation rendering. This is the semantic center of the runtime path defined by the query contract. 

**Inference Adapters**
Embeddings for query vectorization, optional reranking model later, and one main LLM for structured interpretation/support/generation calls. The contract does not prescribe providers, only that outputs remain inspectable and stage-separated. 

**Query Trace / Review Surface**
Persists stage outputs, timings, diagnostics, and evidence-to-answer linkage. The query contract explicitly requires enough traceability in logs, traces, or review outputs to reconstruct why an answer was returned. 

## 4. Internal runtime flow

A synchronous `/queries` request should execute this exact chain:

1. validate workspace/corpus boundary and request shape;
2. interpret query into structured retrieval intent;
3. retrieve passage candidates from `READY` corpus only;
4. rerank and group candidates into explicit evidence sets;
5. assemble deterministic budgeted context;
6. assess support against requested answer shape;
7. choose answer mode from support state;
8. generate answer under that mode;
9. render citations from preserved provenance;
10. persist complete trace and return result.    

The critical point is that support is assessed against the requested answer shape, not topic similarity, and that retrieval success does not imply sufficient support. That rule should be enforced in code, not merely described in prompts. 

## 5. Core domain objects

I would add these query-side objects.

**QueryRequest**
`query_id, workspace_id, user_text, policy_config, requested_answer_shape`

**InterpretedQuery**
`normalized_text, query_type, scope_flags, retrieval_plan, answer_shape, specificity, source_navigation_target?`

The interpretation stage must preserve distinctions such as direct factual lookup, section-scoped explanation, one-document synthesis, cross-document synthesis, source navigation, and unsupported question type. It does not need a heavyweight classifier, but it cannot erase those distinctions. 

**RetrievedCandidate**
`candidate_id, doc_id, chunk_id, section_id, score, heading_path, page_start, page_end, ordinal, text, metadata`

This matches the query requirement that retrieval operate on evidence-bearing units with stable identity and recoverable provenance, preserving the `DOCUMENT -> SECTION -> PASSAGE` hierarchy while using passages as the default retrieval unit. 

**EvidenceUnit**
Usually a passage plus optional structural enrichments such as heading path or neighbor linkage. This corresponds directly to the query contract’s evidence-unit definition. 

**EvidenceSet**
`evidence_set_id, purpose, units[], supporting_claims[], completeness_score, conflict_flags`

This should be explicit because the contract allows support to come from one or more evidence units, sometimes across documents, and the system must not assume that isolated top-k passages alone are the answerable unit. 

**ContextManifest**
`ordered_items[], dropped_items[], token_budget, assembly_reasons, truncation_reasons`

The contract requires deterministic ordering, intentional truncation, and preservation of crucial evidence under budget.  

**SupportAssessment**
`support_state, rationale, supported_subquestions[], unsupported_gaps[], conflicting_sources[], required_citation_shape`

The canonical support states are `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED_IN_CORPUS`, `UNSUPPORTED_QUESTION_TYPE`, and `AMBIGUOUS_OR_CONFLICTING`.  

**AnswerModeDecision**
`mode, allowed_scope, qualification_rules, abstention_kind, citation_requirement`

This enforces the required mapping from support state to answer posture. 

**AnswerDraft**
`text, fragment_links[], visible_limitations[]`

**CitationBundle**
`fragments -> anchors[]`, where anchors resolve to document identity plus source-type-appropriate locator. PDF should include at least page; Markdown should include heading or section path.  

## 6. Stage implementations

### 6.1 Interpret

Use a structured LLM call with a strict schema, then deterministic normalization. The output should decide at least:

* query type,
* answer-shape expectation,
* whether the user wants explanation vs location,
* whether synthesis is required,
* whether the question appears outside MVP capability. 

I would not put retrieval reformulation, support judgment, and answer phrasing in the same call. That would recreate the opaque step the contract explicitly forbids. 

### 6.2 Retrieve

Dense-first passage retrieval over `READY` chunks only, filtered by workspace and active corpus boundary. Retrieval should return stable chunk identity plus section/path/page metadata for later citation and inspection. Neighbor context should not be the retrieval unit; it should be attached later if needed.  

### 6.3 Select / Rerank

For MVP I would use an explicit reranking layer that is initially heuristic, not cross-encoder. It should optimize for answerable support, not just semantic similarity. Primary signals:

* heading/path match,
* locality around likely answer passage,
* diversity across docs when synthesis is requested,
* duplicate suppression,
* completeness of support for the interpreted answer shape,
* source-navigation precision when the query asks “where.”

That preserves inspectability and determinism while leaving room for a model reranker later. The workflow explicitly distinguishes retrieval quality from context quality and answer quality, so selection needs its own observable surface.  

### 6.4 Evidence-set builder

This should convert ranked candidates into one or more explicit evidence sets. Examples:

* single-passage factual set,
* passage + neighboring passage explanatory set,
* multi-passage same-document synthesis set,
* cross-document synthesis set,
* conflicting-source set.

This is the seam where you avoid treating “top passages” as equivalent to “supporting evidence.”  

### 6.5 Context assembler

Assemble a deterministic, ordered, budgeted context from evidence sets, preserving structural metadata. Truncation should drop low-value evidence sets first rather than clipping selected evidence arbitrarily. The contract requires deterministic ordering, explicit tie-breaking, duplicate suppression, and intentional truncation.  

### 6.6 Support assessment

This should be a dedicated structured decision stage. I would implement it as hybrid:

* deterministic pre-checks for obvious unsupported question type and obvious provenance gaps;
* structured LLM judgment over interpreted query + evidence sets + context manifest;
* deterministic post-rules that can only narrow, never widen, the support state.

The contract is explicit that support assessment must evaluate evidence sufficiency against requested answer shape and must not be left implicit inside generation. 

### 6.7 Answer-mode decision

Translate support state into executable posture:

* `SUPPORTED` -> direct answer,
* `PARTIALLY_SUPPORTED` -> narrowed answer and/or explicit qualification,
* `UNSUPPORTED_IN_CORPUS` -> abstain,
* `UNSUPPORTED_QUESTION_TYPE` -> explicit capability-boundary response,
* `AMBIGUOUS_OR_CONFLICTING` -> conflict-visible answer.  

This stage must also choose among the abstention-compatible behaviors the spec requires: full abstention, scoped abstention, or qualified uncertainty.  

### 6.8 Generate

Generation should consume answer mode plus supportable evidence only. It may paraphrase and synthesize when the evidence permits, but it must not fill unsupported gaps from priors or flatten conflict into consensus. It should also emit fragment-to-evidence linkage for citation rendering. 

### 6.9 Cite

Citation rendering should use preserved provenance, not LLM-invented anchors. Minimum output should be document identity plus page for PDFs and document identity plus heading/section locator for Markdown. Mixed-format synthesis should expose all materially contributing sources.  

## 7. Persistence model

I would add query-side tables alongside existing document tables.

**query_run**
One row per request: workspace, user text, timestamps, final status.

**query_interpretation**
Structured output of QL-1.

**query_retrieval_candidate**
All returned candidates with rank, score, and provenance-bearing metadata.

**query_evidence_set** and **query_evidence_set_member**
Explicit evidence-set persistence.

**query_context_manifest** and **query_context_item**
Budget, ordering, dropped items, truncation reasons.

**query_support_assessment**
Support state, rationale, unsupported gaps, conflict notes.

**query_answer_mode**
Chosen posture and allowed scope.

**query_answer**
Final text plus visible limitations.

**query_answer_fragment_link**
Maps answer fragments to evidence units.

**query_citation**
Rendered citation bundles.

**query_failure**
Primary failure label and secondary diagnostics for review/eval.

This design is justified by the traceability standard and the failure-handling contract, which require enough artifacts to localize failures such as `U1/U2/A1/A2/P1/P2/I1/S1` instead of letting fluency hide them.   

## 8. FastAPI surface

For MVP I would keep the HTTP surface internal and simple.

`POST /queries`
Runs the full synchronous query lifecycle and returns:

* answer text,
* support state,
* answer mode,
* citations,
* visible limitations,
* trace id / query id.

`GET /queries/{query_id}`
Returns stored result summary.

`GET /queries/{query_id}/trace`
Returns stage outputs for debugging/review.

`GET /queries/{query_id}/citations`
Returns normalized citation objects.

`POST /queries/{query_id}/replay`
Optional operator endpoint to rerun the request against the same corpus and config for regression/debugging.

Keeping these internal matches the existing document-lifecycle choice to avoid premature public API commitments while still supporting runtime and operator workflows. 

## 9. Package layout

I would extend the existing package layout rather than creating a separate repo.

```text
src/parity/
  app/
    api.py
    deps.py
    settings.py

  query/
    service.py
    contracts.py
    errors.py

  query_stages/
    interpret.py
    retrieve.py
    rerank.py
    evidence_sets.py
    context.py
    assess_support.py
    decide_answer_mode.py
    generate.py
    citations.py

  query_domain/
    query.py
    interpreted_query.py
    evidence.py
    context_manifest.py
    support.py
    answer.py
    citation.py

  query_persistence/
    models.py
    repositories.py

  query_eval/
    failure_labels.py
    diagnostics.py

  readmodels/
    documents.py
    chunks.py
    provenance.py

  inference/
    embeddings.py
    llm.py
    schemas.py
```

This follows the same design intent as the document-lifecycle package layout: stable internal concepts in domain modules, stage-local logic in stage modules, persistence separated cleanly, and thin API entry points. 

## 10. Determinism rules

I would make these non-optional at implementation level:

* stable tie-breaks in retrieval and reranking,
* explicit duplicate suppression,
* deterministic context ordering,
* stable answer-mode mapping from support-state input,
* persisted config snapshot per run.

Those are direct consequences of the query contract’s determinism and stability requirements. 

## 11. Failure handling

The query path should fail locally and explicitly.

Examples:

* retrieval miss should remain visible as retrieval miss and usually drive abstention rather than unsupported answering;
* unsupported question type should route to explicit scope-boundary behavior;
* provenance failure should block or weaken supported-answer posture rather than allowing decorative citations;
* partial support should not be rendered as complete answer.   

At the trace level, I would store both one primary user-visible failure label and secondary diagnostic causes. That matches the critical-failures model and keeps evals aligned with the real trust break rather than an arbitrary internal cause. 

## 12. Immediate implementation sequence

I would implement in this order:

**Phase A — query intake + retrieval**
Create query endpoint, interpreted-query schema, dense retrieval over `READY` chunks, candidate trace persistence. This matches the delivery sequencing appendix and gives you real evidence-bearing retrieval quickly. 

**Phase B — selection + evidence sets + context assembly**
Add reranking, evidence-set builder, deterministic context manifest, budget handling, and trace visibility. 

**Phase C — support assessment + answer mode**
Make support-state judgment explicit and enforce posture mapping before generation. This is the highest-value trust seam.  

**Phase D — grounded generation + citations**
Add answer rendering, fragment linkage, and inspectable citation bundles.  

**Phase E — eval hardening**
Add scenario tests and failure-label mapping for direct lookup, scoped explanation, one-doc synthesis, cross-doc synthesis, source navigation, partial support, conflicting support, and unsupported question type. 

## 13. Bottom line

The correct MVP architecture is not a generic RAG chain and not a second service. It is a query domain inside the existing single-node FastAPI service with explicit stage contracts, dense-first passage retrieval over `READY` documents, explicit evidence sets, deterministic context assembly, explicit support assessment, explicit answer-mode enforcement, grounded generation, provenance-safe citation rendering, and persisted query traces for review and regression. That is the smallest architecture that remains compatible with the document-lifecycle design while satisfying the query-lifecycle invariants you have fixed.   

Next step should be converting this into concrete internal contracts: Python dataclasses/Pydantic models for each stage plus the Postgres schema for query traces.
