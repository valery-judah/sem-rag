# Stage 4 Design: Selection and Evidence-Set Construction

**Status:** Implemented  
**Applies to:** WS-006 / MVP / Stage 4  
**Last updated:** 2026-03-11

## Purpose

This document records the repo-facing Stage 4 design as implemented in `doc_forge`.

Stage 4 implements the first explicit post-retrieval transformation from raw candidate rankings into supportable evidence structures.
It is where the query subsystem stops behaving like "top-k passages plus a prompt" and starts behaving like an evidence-driven runtime.

Stage 4 does not implement context assembly, support assessment, answer-mode selection, answer generation, or citation rendering.
It earns the selection boundary and the evidence-set objects that later stages depend on.

## Authority and scope

This design is subordinate to:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
3. `docs/evergreen/api-contracts.md`
4. `docs/evergreen/eval-support-semantics.md`
5. [`04_query-lifecycle-requirements-final.md`](./04_query-lifecycle-requirements-final.md)
6. [`07_design.md`](./07_design.md)
7. [`13_stage-3-retrieval-foundation-design.md`](./13_stage-3-retrieval-foundation-design.md)
8. [`query_subsystem_staged_implementation_plan.md`](./query_subsystem_staged_implementation_plan.md)

This document describes internal repo shape and current implementation truth only.
It does not create a stable public API.

## Outcome

Stage 4 is implemented with:

- deterministic selection helpers in [selection.py](src/doc_forge/query/selection.py);
- an executable `select` stage in [select.py](src/doc_forge/query/stages/select.py);
- strengthened Stage 4 evidence contracts in [contracts.py](src/doc_forge/query/contracts.py);
- Stage 4 runtime state and orchestration in [domain.py](src/doc_forge/query/domain.py) and [service.py](src/doc_forge/query/service.py);
- internal route integration in [api.py](src/doc_forge/app/api.py) and [deps.py](src/doc_forge/app/deps.py);
- tests covering duplicate suppression, same-document grouping, selection traces, and route behavior.

## Design constraints resolved in Stage 4

Stage 4 had to fit the repo as it existed after Stage 3.

The relevant constraints were:

- Stage 1 already owned stable snapshot capture and `READY`-only queryability;
- Stage 2 already owned deterministic `InterpretedQuery` creation and durable `interpret` traces;
- Stage 3 already owned snapshot-scoped dense retrieval and durable `retrieve` traces;
- `src/doc_forge/query/contracts.py` already exposed `EvidenceGroupingMode`, `DuplicateSuppressionMode`, `EvidenceUnit`, and `EvidenceSet`, but those contracts were too thin for executable selection behavior;
- `src/doc_forge/query/policies.py` already exposed the Stage 4 policy levers: `evidence_set_cap`, `neighbor_expansion_*`, and `duplicate_suppression_mode`;
- `src/doc_forge/readmodels/documents.py` already exposed snapshot-scoped chunk records with `ordinal`, `heading_path`, pages, and source offsets;
- `doc_forge._contracts.SourceReference` already provided the inspectable provenance shape that Stage 4 should reuse;
- `query_stage_traces` already existed and needed to remain the single durable stage-trace surface.

The implemented consequence is pragmatic:

- Stage 4 stays deterministic and local;
- it reuses snapshot read models rather than joining lifecycle tables directly from stage code;
- it strengthens internal query contracts instead of inventing prompt-side implicit structure;
- it preserves divergence structurally instead of attempting support-stage reconciliation early.

## Implemented shape

### Selection helper seam

[selection.py](src/doc_forge/query/selection.py) now exposes:

- `SnapshotSelectionIndex`
- `SelectionDecision`
- `NeighborExpansionRecord`
- `SelectionResult`
- `QuerySelector`
- `DeterministicQuerySelector`

The implemented selector owns:

- reranking signal calculation;
- deterministic duplicate suppression;
- bounded neighbor expansion;
- evidence-unit hydration from snapshot read models;
- evidence-set grouping.

### Strengthened Stage 4 contracts

[contracts.py](src/doc_forge/query/contracts.py) now extends the evidence objects used downstream.

`EvidenceUnit` now carries:

- `unit_rank`
- `added_by_neighbor_expansion`
- `selection_reason`

`EvidenceSet` now carries:

- `purpose`
- `coverage_notes`
- `conflict_flags`
- `assembly_reason`

[domain.py](src/doc_forge/query/domain.py) also now tracks:

- `selected_candidates`
- `evidence_sets`

This keeps raw retrieval output distinct from Stage 4-selected support structures.

### Snapshot-local selection index

The selector now builds an in-memory snapshot-local index from the existing read model methods:

- `list_ready_documents(workspace_id)` filtered to `snapshot.eligible_doc_ids`
- `list_chunks_for_snapshot(snapshot)`

That index provides:

- `documents_by_id`
- `chunks_by_id`
- `chunks_by_doc_and_ordinal`

No Stage 4 code reads raw artifacts or joins lifecycle persistence directly.

### Deterministic reranking and duplicate suppression

The implemented selector reranks retrieved candidates using deterministic signals derived from:

- retrieval score and rank;
- interpreted request type and specificity;
- scope-hint overlap with heading paths;
- source-navigation precision;
- local coherence potential;
- provenance completeness.

Duplicate suppression remains tied to `QueryPolicy.duplicate_suppression_mode`.
The current implementation supports:

- `EXACT_SPAN`
- `HEADING_AND_LOCATOR`

Suppression is deterministic and document-local.
Dropped duplicates are preserved in the `select` trace with explicit reasons.

### Neighbor expansion and grouping

Neighbor expansion is now:

- bounded by `neighbor_expansion_enabled` and `neighbor_expansion_cap`;
- limited to adjacent ordinals in the same document;
- constrained to the same `section_id` when available, otherwise the same `heading_path`;
- marked explicitly on `EvidenceUnit.added_by_neighbor_expansion`.

Evidence grouping now supports the MVP families already defined in the contracts:

- `SINGLE_PASSAGE`
- `PASSAGE_WITH_NEIGHBOR`
- `SAME_DOCUMENT_MULTI_PASSAGE`
- `MULTI_DOCUMENT`

The current grouping behavior is conservative:

- same-document explanation queries can group multiple passages from one document;
- source-navigation and narrow fact cases stay atomic unless a neighbor materially improves coherence;
- synthesis-intended queries preserve small cross-document support sets instead of collapsing back to one source.

### Executable `select` stage and traces

[select.py](src/doc_forge/query/stages/select.py) now runs a real Stage 4 selection step.

The stage:

- accepts `query_id`, `QueryRequest`, `CorpusSnapshot`, `InterpretedQuery`, retrieved candidates, `QueryPolicy`, and an injected selector;
- returns structured Stage 4 output;
- emits a `QueryStageTrace` for `select`;
- persists selected candidates, drop reasons, grouping output, duplicate suppression notes, and neighbor-expansion notes as structured payload.

### Query service and route behavior

[service.py](src/doc_forge/query/service.py) now supports:

- `execute_until_selection()`

That method now performs:

1. Stage 1 query preparation
2. Stage 2 interpretation and `interpret` trace persistence
3. Stage 3 retrieval and `retrieve` trace persistence
4. Stage 4 selection and `select` trace persistence
5. return of `QueryRuntimeState` with `selected_candidates` and `evidence_sets`

[api.py](src/doc_forge/app/api.py) now exposes internal `POST /queries` with Stage 4 behavior.

It now returns:

- `query_id`
- `workspace_id`
- `status`
- `snapshot`
- `interpreted_query`
- `retrieved_candidates`
- `selected_candidates`
- `evidence_sets`
- `message`

The route still stops explicitly before context assembly and answer behavior.

### App wiring

[deps.py](src/doc_forge/app/deps.py) now wires:

- `DeterministicQuerySelector`
- Stage 4-ready `QueryService`

The runtime default remains deterministic and local.
No learned reranker or provider-backed LLM is required to execute Stage 4.

## Validation coverage

Stage 4 is covered by:

- [test_query_selection.py](tests/query/test_query_selection.py)
- [test_query_service_retrieve.py](tests/query/test_query_service_retrieve.py)
- [test_runtime_api.py](tests/app/test_runtime_api.py)
- [test_query_contract_models.py](tests/contract/test_query_contract_models.py)

The current coverage locks the key Stage 4 invariants:

- duplicate suppression is deterministic;
- same-document explanation queries can build multi-passage evidence sets;
- empty snapshots still produce valid empty Stage 4 output;
- each query run persists a durable `select` trace after `retrieve`;
- the internal `/queries` route returns Stage 4 evidence output rather than stopping at raw retrieval.

## Deferred from Stage 4

Stage 4 still does not implement:

- token-budgeted context assembly
- support-state judgment
- answer-mode policy enforcement
- grounded answer generation
- citation rendering
- neural reranking
- deep semantic contradiction resolution
