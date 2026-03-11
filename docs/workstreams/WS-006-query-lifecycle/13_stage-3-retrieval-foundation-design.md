# Stage 3 Design: Retrieval Foundation with Provenance-Preserving Candidates

**Status:** Implemented  
**Applies to:** WS-006 / MVP / Stage 3  
**Last updated:** 2026-03-11

## Purpose

This document records the repo-facing Stage 3 design as implemented in `parity`.

Stage 3 does not implement evidence selection, support assessment, or answer generation.
It implements the first real evidence-discovery stage after Stage 2 interpretation:

- retrieval is now executable rather than deferred;
- retrieval is explicitly downstream of `InterpretedQuery`;
- retrieval is bounded to the query-time snapshot rather than live workspace state;
- retrieved candidates preserve enough identity and provenance for later stages and trace review.

## Authority and scope

This document is subordinate to:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
3. `docs/evergreen/agent-routing.md`
4. `docs/evergreen/api-contracts.md`
5. `docs/evergreen/eval-support-semantics.md`
6. [`04_query-lifecycle-requirements-final.md`](./04_query-lifecycle-requirements-final.md)
7. [`07_design.md`](./07_design.md)
8. [`11_stage-1-queryable-corpus-boundary-design.md`](./11_stage-1-queryable-corpus-boundary-design.md)
9. [`12_stage-2-interpretation-foundation-design.md`](./12_stage-2-interpretation-foundation-design.md)
10. [`query_subsystem_staged_implementation_plan.md`](./query_subsystem_staged_implementation_plan.md)

This document describes internal repo shape and current implementation truth only.
It does not create a stable public API.

## Outcome

Stage 3 is implemented with:

- retrieval-ready embedded chunk projections in [documents.py](src/parity/readmodels/documents.py);
- deterministic retrieval-query construction and dense retrieval helpers in [retrieval.py](src/parity/query/retrieval.py);
- an executable `retrieve` stage in [retrieve.py](src/parity/query/stages/retrieve.py);
- Stage 3 service wiring in [service.py](src/parity/query/service.py);
- internal route integration in [api.py](src/parity/app/api.py) and [deps.py](src/parity/app/deps.py);
- tests covering snapshot scoping, provenance-bearing candidate output, durable retrieval traces, and route behavior.

## Design constraints resolved in Stage 3

Stage 3 had to fit the repo that exists today.

The relevant constraints were:

- Stage 1 already owns stable snapshot capture and persisted `eligible_doc_ids`;
- Stage 2 already owns deterministic interpretation and durable `interpret` traces;
- lifecycle indexing already persists chunk embeddings and index publication records through the `READY` path;
- the existing `SqlVectorStore` smoke query path is document-scoped operator infrastructure, not the workspace query runtime;
- the repo still needs deterministic local execution without provider-backed embedding dependencies;
- `query_stage_traces` already exists and should remain the single durable trace surface for semantic query stages.

The implemented consequence is pragmatic:

- Stage 3 reuses persisted chunk embeddings rather than creating a second retrieval store;
- retrieval stays in-process and deterministic;
- snapshot-scoped retrieval happens through the query read model rather than direct repository joins inside stage code;
- retrieval traces reuse the existing stage-trace table rather than introducing retrieval-specific persistence.

## Implemented shape

### Retrieval-ready read model extension

[documents.py](src/parity/readmodels/documents.py) now exposes:

- `QueryableEmbeddedChunkRecord`
- `list_embedded_chunks_for_snapshot(snapshot)`

`QueryableEmbeddedChunkRecord` extends the Stage 1 chunk projection with:

- `embedding_model`
- `embedding_vector`

The read model behavior is:

- read only `snapshot.eligible_doc_ids`;
- keep the Stage 1 provenance-bearing chunk filter;
- join persisted embeddings by `chunk_id` within each snapshot document;
- omit chunks that have no active embedding vector.

This keeps retrieval bounded to the captured corpus snapshot while preserving the existing query-facing read boundary.

### Deterministic retrieval-query representation

[retrieval.py](src/parity/query/retrieval.py) now exposes:

- `RetrievalQueryRepresentation`
- `QueryRetrievalResult`
- `DenseQueryRetriever`
- `SnapshotDenseQueryRetriever`
- `build_retrieval_query_representation()`

The current retrieval-query representation carries:

- `query_text`
- `normalized_question`
- `request_type`
- `specificity`
- `scope_hints`
- `requires_source_navigation`
- `synthesis_mode`
- `diagnostic_raw_question`

The implemented behavior is intentionally narrow:

- retrieval embeds `interpreted_query.normalized_question`;
- raw question text is retained only as diagnostics in the representation;
- no second model call is used to reformulate retrieval input.

This preserves the Stage 2 contract instead of allowing retrieval to silently fall back to raw-query semantics as the primary path.

### Snapshot-scoped dense retriever

`SnapshotDenseQueryRetriever` now performs the real Stage 3 retrieval path:

1. build `RetrievalQueryRepresentation` from `InterpretedQuery`;
2. embed `representation.query_text` through an injected `EmbeddingAdapter`;
3. load `QueryableEmbeddedChunkRecord` values for the captured snapshot;
4. compute cosine similarity against each chunk embedding;
5. sort with the query policy tie-break order;
6. cap by `QueryPolicy.retrieval_candidate_cap`;
7. map the ranked hits into `RetrievedCandidate`.

The default runtime implementation is:

- dense-only;
- cosine similarity;
- deterministic local embeddings through `DeterministicEmbeddingAdapter`;
- no reranking;
- no duplicate suppression;
- no neighbor expansion;
- no evidence grouping.

### `RetrievedCandidate` population

Stage 3 keeps the existing `RetrievedCandidate` contract in [contracts.py](src/parity/query/contracts.py) as the retrieval-stage output shape.

The runtime now populates it with:

- `doc_id`
- `chunk_id`
- `section_id`
- `heading_path`
- `locator`
- `retrieval_score`
- `retrieval_rank`

Locator rendering is deterministic and provenance-derived:

- `p. N` or `pp. N-M` when page metadata exists;
- `offset N` or `offsets N-M` when source offsets exist;
- `section <section_id>` as the fallback.

This is not final citation rendering.
It is the minimum retrieval-stage locator surface needed to keep later stages and traces inspectable.

### Retrieval stage execution

[retrieve.py](src/parity/query/stages/retrieve.py) now runs a real Stage 3 retrieval step.

The stage:

- accepts `query_id`, `QueryRequest`, `CorpusSnapshot`, `InterpretedQuery`, `QueryPolicy`, and an injected retriever;
- returns structured retrieval output;
- emits a `QueryStageTrace` for `retrieve`;
- persists retrieval payload rather than collapsing the output into prompt text.

The current retrieval trace payload includes:

- `interpreted_query`
- `retrieval_query_representation`
- `embedding_model`
- `retrieval_backend`
- `snapshot_doc_ids`
- `retrieval_candidate_cap`
- `retrievable_chunk_count`
- `candidates`

### Query service behavior

[service.py](src/parity/query/service.py) now supports Stage 3 execution through:

- `prepare_query()`
- `execute_until_interpretation()`
- `execute_until_retrieval()`

`execute_until_retrieval()` now performs:

1. Stage 1 query preparation
2. query run status update to `RUNNING`
3. Stage 2 interpretation and `interpret` trace persistence
4. Stage 3 retrieval and `retrieve` trace persistence
5. return of `QueryRuntimeState` with `run`, `snapshot`, `interpreted_query`, and `retrieved_candidates`

`execute()` still stops after the deepest implemented stage boundary and raises once later stages would be required.

### Internal API surface

[api.py](src/parity/app/api.py) now exposes internal `POST /queries` with Stage 3 behavior.

It accepts:

- `question`
- `workspace_id`
- optional `policy_overrides`

It now returns:

- `query_id`
- `workspace_id`
- `status`
- `snapshot`
- `interpreted_query`
- `retrieved_candidates`
- `message`

The route remains intentionally thin:

- it calls `QueryService.execute_until_retrieval()`;
- it returns developer-visible retrieval output;
- it states explicitly that downstream stages remain unimplemented.

This route remains internal-only.
It does not promote a stable public API contract.

### App wiring

[deps.py](src/parity/app/deps.py) now wires:

- `SqlQueryableCorpusReadModel` with `SqlChunkEmbeddingRepository`
- `SnapshotDenseQueryRetriever`
- `DeterministicEmbeddingAdapter`
- Stage 3-ready `QueryService`

The runtime default remains deterministic and local.
No provider-backed embedder configuration is required to execute Stage 3.

## Validation coverage

Stage 3 is covered by:

- [test_queryable_corpus_read_model.py](tests/readmodels/test_queryable_corpus_read_model.py)
- [test_query_service_prepare.py](tests/query/test_query_service_prepare.py)
- [test_query_service_interpret.py](tests/query/test_query_service_interpret.py)
- [test_query_retrieval.py](tests/query/test_query_retrieval.py)
- [test_query_service_retrieve.py](tests/query/test_query_service_retrieve.py)
- [test_runtime_api.py](tests/app/test_runtime_api.py)

The current coverage locks the key Stage 3 invariants:

- retrieval never returns a chunk outside the captured snapshot;
- embedded-chunk reads include only snapshot chunks with active embeddings;
- retrieval returns an empty candidate list for an empty but valid snapshot;
- candidates preserve provenance-bearing fields and deterministic locator rendering;
- interpretation still executes before retrieval and persists its own stage trace;
- one durable `retrieve` stage trace is persisted per Stage 3 execution;
- the internal `/queries` route returns retrieved candidates rather than stopping at interpretation.

## Deferred from Stage 3

Stage 3 still does not implement:

- heuristic reranking
- duplicate suppression
- neighbor expansion
- evidence-set construction
- context assembly
- support assessment
- answer-mode decisions
- answer generation
- citation rendering
- public API promotion
- authenticated workspace existence or ACL enforcement
- provider-backed embedding retrieval
- hybrid or external retrieval

Those remain for later stages.

## Evergreen review

Stable base reviewed during Stage 3:

- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/evergreen/agent-routing.md`
- `docs/evergreen/api-contracts.md`
- `docs/evergreen/eval-support-semantics.md`

Promoted or worthy of promotion from Stage 3:

- snapshot-scoped dense retrieval as implemented internal architecture
- retrieval-ready embedded chunk reads as part of the query-facing read model
- internal `/queries` route now executing through retrieval and stopping there explicitly

Not promoted to stable public contract:

- retrieval candidate payload shape
- retrieval trace payload schema
- internal route response fields

Why:

- Stage 3 earned implemented internal seams and tests;
- the route and contracts are still intended to evolve before any public compatibility promise.

## Current routes

Start with the stable query context base in `docs/harness-maintain/context-building-playbook.md`.
Then use the Stage 3-specific route below.

1. [12_stage-2-interpretation-foundation-design.md](docs/workstreams/WS-006-query-lifecycle/12_stage-2-interpretation-foundation-design.md)
2. [documents.py](src/parity/readmodels/documents.py)
3. [contracts.py](src/parity/query/contracts.py)
4. [retrieval.py](src/parity/query/retrieval.py)
5. [retrieve.py](src/parity/query/stages/retrieve.py)
6. [service.py](src/parity/query/service.py)
7. [persistence.py](src/parity/query/persistence.py)
8. [api.py](src/parity/app/api.py)
9. [deps.py](src/parity/app/deps.py)

Then confirm in tests:

1. [test_queryable_corpus_read_model.py](tests/readmodels/test_queryable_corpus_read_model.py)
2. [test_query_retrieval.py](tests/query/test_query_retrieval.py)
3. [test_query_service_retrieve.py](tests/query/test_query_service_retrieve.py)
4. [test_runtime_api.py](tests/app/test_runtime_api.py)

## Context building

Stage 3 reuses the stable context-building base plus the already-earned Stage 1 and Stage 2 seams, then adds retrieval-specific discovery.

Use the following order:

1. stable context-building base from `docs/harness-maintain/context-building-playbook.md`
2. Stage 1 implemented note for snapshot and queryable-corpus invariants
3. Stage 2 implemented note for interpretation contracts and traces
4. `src/parity/readmodels/documents.py`
5. `src/parity/query/retrieval.py` and `src/parity/query/stages/retrieve.py`
6. `src/parity/query/service.py` and `src/parity/app/api.py`
7. proving tests for retrieval behavior and trace persistence

Supported by repo truth in Stage 3:

- retrieval is now a real executable stage
- retrieval artifacts persist as durable stage traces
- `/queries` executes through retrieval before stopping

Inference due to missing seam in Stage 3:

- retrieval remains dense-only and deterministic because no learned reranker or provider-backed retrieval adapter has been introduced yet
- selection, support, and answer-layer behavior remain downstream work and should not be inferred from the existence of retrieval candidates

## Log

- 2026-03-11: drafted the initial Stage 3 repo-facing retrieval design.
- 2026-03-11: implemented snapshot-scoped dense retrieval over persisted chunk embeddings.
- 2026-03-11: added retrieval-ready embedded chunk reads plus deterministic retrieval-query construction.
- 2026-03-11: wired `QueryService.execute_until_retrieval()` and updated internal `POST /queries`.
- 2026-03-11: added Stage 3 tests for snapshot scoping, retrieval behavior, trace persistence, and route output.
