# Stage 2 Design: Interpretation Foundation

**Status:** Implemented  
**Applies to:** WS-006 / MVP / Stage 2  
**Last updated:** 2026-03-11

## Purpose

This document records the repo-facing Stage 2 design as implemented in `parity`.

Stage 2 does not implement retrieval, support assessment, or answer generation.
It implements the first semantic query stage after Stage 1 corpus-boundary capture:

- every query is interpreted explicitly before retrieval exists;
- interpretation output is structured enough for downstream retrieval and support logic;
- unsupported capability boundaries are surfaced early instead of being deferred into generation;
- interpretation artifacts are persisted as durable stage traces.

## Authority and scope

This document is subordinate to:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
3. `docs/evergreen/api-contracts.md`
4. `docs/evergreen/eval-support-semantics.md`
5. [`04_query-lifecycle-requirements-final.md`](./04_query-lifecycle-requirements-final.md)
6. [`07_design.md`](./07_design.md)
7. [`11_stage-1-queryable-corpus-boundary-design.md`](./11_stage-1-queryable-corpus-boundary-design.md)
8. [`query_subsystem_staged_implementation_plan.md`](./query_subsystem_staged_implementation_plan.md)

This document describes internal repo shape and current implementation truth only.
It does not create a stable public API.

## Outcome

Stage 2 is implemented with:

- a stronger `InterpretedQuery` contract in [contracts.py](src/parity/query/contracts.py);
- deterministic interpretation and normalization helpers in [interpretation.py](src/parity/query/interpretation.py);
- an executable `interpret` stage in [interpret.py](src/parity/query/stages/interpret.py);
- durable query stage traces through [persistence.py](src/parity/query/persistence.py);
- a new migration [0005_query_stage_traces.py](src/parity/persistence/migrations/versions/0005_query_stage_traces.py);
- Stage 2 service wiring in [service.py](src/parity/query/service.py);
- internal route integration in [api.py](src/parity/app/api.py) and [deps.py](src/parity/app/deps.py).

## Design constraints resolved in Stage 2

Stage 2 had to fit the repo that exists today.

The relevant constraints were:

- Stage 1 already owns query run creation and stable snapshot capture;
- the repo has no shared LLM adapter package yet;
- the repo needs deterministic tests without external model dependency;
- the query trace model existed, but persistence for stage traces did not;
- the internal `/queries` route remained developer-facing and could evolve without public contract promotion.

The implemented consequence is pragmatic:

- Stage 2 uses a narrow interpreter seam under `src/parity/query/` instead of a broad inference subsystem;
- the default runtime interpreter is deterministic and schema-driven;
- interpretation traces persist through a generic stage-trace table rather than a one-off interpretation table;
- the route now executes through interpretation and stops there explicitly.

## Implemented shape

### Strengthened `InterpretedQuery` contract

[contracts.py](src/parity/query/contracts.py) now defines:

- `QuerySpecificity`
- `SynthesisMode`
- `UnsupportedCapability`

`InterpretedQuery` now carries:

- `normalized_question`
- `request_type`
- `answer_shape`
- `specificity`
- `scope_hints`
- `requires_synthesis`
- `synthesis_mode`
- `requires_source_navigation`
- `unsupported_capability_flags`
- `normalization_notes`

This keeps Stage 2 aligned with QL-1 by preserving distinctions among factual lookup, explanation, synthesis, source navigation, comparison, and unsupported question shapes.

### Deterministic interpreter seam

[interpretation.py](src/parity/query/interpretation.py) now exposes:

- `QueryInterpreter`
- `RawInterpretedQuery`
- `InterpreterMetadata`
- `QueryInterpretationResult`
- `DeterministicQueryInterpreter`

The implemented runtime path is:

1. normalize the raw user question deterministically;
2. classify request type, specificity, synthesis intent, and source-navigation intent;
3. detect obvious MVP capability-boundary failures;
4. normalize the result into the stable `InterpretedQuery` contract;
5. attach interpreter metadata for trace persistence.

The current deterministic classifier is phrase- and heuristic-driven.
It specifically handles:

- source-navigation phrases such as section/page/location requests;
- explanation phrases such as `explain`, `how does`, and `summarize`;
- comparison phrases such as `compare`, `contrast`, and `difference between`;
- cross-document synthesis phrases such as `these documents` and `across sources`;
- unsupported capability cues such as `figure`, `diagram`, `table`, `ocr`, and obvious external-knowledge requests.

This implementation does not add live model-provider wiring yet.
Instead, it earns the interpretation contract and service seam first, while preserving a narrow place where a structured LLM-backed interpreter can be added later.
The interpreter receives the Stage 1 `CorpusSnapshot`, but the current deterministic implementation uses it only as a stage boundary input, not as a semantic signal source.

### Interpretation stage execution

[interpret.py](src/parity/query/stages/interpret.py) now runs a real Stage 2 interpretation step.

The stage:

- accepts `query_id`, `QueryRequest`, `CorpusSnapshot`, and an injected interpreter;
- returns normalized interpretation output;
- emits a `QueryStageTrace` for `interpret`;
- persists both interpreted payload and interpreter metadata in the trace payload.

Interpretation remains distinct from support assessment.
Stage 2 records request-shape and capability-boundary signals only.

### Durable query stage traces

[persistence.py](src/parity/query/persistence.py) now includes:

- `query_stage_traces_table`
- `SqlQueryTraceStore`

[0005_query_stage_traces.py](src/parity/persistence/migrations/versions/0005_query_stage_traces.py) creates:

- `query_stage_traces`

Each row stores:

- `query_id`
- `stage_name`
- `stage_status`
- `started_at`
- `finished_at`
- `payload_json`

The `interpret` trace payload currently includes:

- normalized `interpreted_query`
- interpreter metadata with implementation name, schema version, and normalization version

### Query service behavior

[service.py](src/parity/query/service.py) now supports Stage 2 execution through:

- `prepare_query()`
- `execute_until_interpretation()`

`prepare_query()` remains the Stage 1 boundary method and still captures a stable snapshot.

`execute_until_interpretation()` now performs:

1. Stage 1 query preparation
2. in-memory and persisted query run status update to `RUNNING`
3. interpretation stage execution
4. durable interpretation trace persistence
5. return of `QueryRuntimeState` with `run`, `snapshot`, and `interpreted_query`

`execute()` still stops after the currently implemented stage boundary and raises once later stages would be required.
If no query corpus read model is configured, `execute()` still follows the Stage 0 initialization path and does not attempt interpretation.

### Internal API surface

[api.py](src/parity/app/api.py) now exposes internal `POST /queries` with Stage 2 behavior.

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
- `message`

The route remains intentionally thin:

- it calls `QueryService.execute_until_interpretation()`
- it returns a developer-visible payload
- it states explicitly that downstream stages remain unimplemented

This route remains internal-only.
It does not promote a stable public API contract.

### App wiring

[deps.py](src/parity/app/deps.py) now wires:

- `SqlQueryTraceStore`
- `DeterministicQueryInterpreter`
- Stage 2-ready `QueryService`

The runtime default remains deterministic.
No provider-backed LLM configuration is required to execute Stage 2 locally.

## Validation coverage

Stage 2 is covered by:

- [test_query_contract_models.py](tests/contract/test_query_contract_models.py)
- [test_interpretation.py](tests/query/test_interpretation.py)
- [test_query_service_prepare.py](tests/query/test_query_service_prepare.py)
- [test_query_service_interpret.py](tests/query/test_query_service_interpret.py)
- [test_runtime_api.py](tests/app/test_runtime_api.py)
- [test_postgres_migrations.py](tests/persistence/test_postgres_migrations.py)

The current coverage locks the key Stage 2 invariants:

- interpretation runs even when the snapshot is empty;
- equivalent requests normalize to the same interpreted semantics;
- unsupported capability boundaries are surfaced explicitly;
- normalization notes may differ for equivalent raw inputs, but the interpreted semantic payload remains stable;
- query runs advance to `RUNNING` when semantic execution begins;
- one durable `interpret` stage trace is persisted per Stage 2 execution;
- the internal `/queries` route returns interpreted output rather than a Stage 1 stub.

## Deferred from Stage 2

Stage 2 still does not implement:

- retrieval or reranking
- evidence-set construction
- context assembly
- support assessment
- answer-mode decisions
- answer generation
- citation rendering
- public API promotion
- authenticated workspace existence or ACL enforcement
- provider-backed structured LLM interpretation

Those remain for later stages.

## Evergreen Review

Stable base reviewed during Stage 2:

- `docs/evergreen/mvp.md`
- `docs/evergreen/architecture.md`
- `docs/evergreen/agent-routing.md`
- `docs/evergreen/api-contracts.md`
- `docs/evergreen/eval-support-semantics.md`

Promoted or worthy of promotion from Stage 2:

- deterministic interpreted-query contract and normalization as internal architecture
- durable query stage traces as internal architecture
- internal `/queries` route now executing through interpretation and stopping there explicitly

Not promoted to stable public contract:

- interpreted-query payload shape
- stage trace payload schema
- internal route response fields

Why:

- Stage 2 earned implemented internal seams and tests
- the route and contracts are still intended to evolve before any public compatibility promise

## Current Routes

Start with the stable query context base in `docs/harness-maintain/context-building-playbook.md`.
Then use the Stage 2-specific route below.

1. [11_stage-1-queryable-corpus-boundary-design.md](docs/workstreams/WS-006-query-lifecycle/11_stage-1-queryable-corpus-boundary-design.md)
2. [contracts.py](src/parity/query/contracts.py)
3. [interpretation.py](src/parity/query/interpretation.py)
4. [interpret.py](src/parity/query/stages/interpret.py)
5. [service.py](src/parity/query/service.py)
6. [persistence.py](src/parity/query/persistence.py)
7. [api.py](src/parity/app/api.py)
8. [deps.py](src/parity/app/deps.py)

Then confirm in tests:

1. [test_interpretation.py](tests/query/test_interpretation.py)
2. [test_query_service_interpret.py](tests/query/test_query_service_interpret.py)
3. [test_runtime_api.py](tests/app/test_runtime_api.py)
4. [test_postgres_migrations.py](tests/persistence/test_postgres_migrations.py)

## Context Building

Stage 2 reuses the stable context-building base and the Stage 1 route, then adds only interpretation-specific discovery.

Use the following order:

1. stable context-building base from `docs/harness-maintain/context-building-playbook.md`
2. Stage 1 implemented note to inherit the already-earned query boundary
3. Stage 2 workstream note for interpretation-specific intent
4. `src/parity/query/interpretation.py` and `src/parity/query/stages/interpret.py`
5. `src/parity/query/service.py` and `src/parity/query/persistence.py`
6. proving tests for interpretation semantics and trace persistence

Supported by repo truth in Stage 2:

- interpretation is now a real executable stage
- interpretation artifacts persist as durable stage traces
- `/queries` executes through interpretation before stopping

Inference due to missing seam in Stage 2:

- provider-backed LLM interpretation remains deferred because the repo still has no shared inference adapter boundary
- interpretation currently uses snapshot input as a stage boundary artifact rather than a semantic signal source

## Log

- 2026-03-11: drafted the Stage 2 repo-facing design to make interpretation an explicit executable stage after Stage 1 snapshot capture.
- 2026-03-11: implemented stronger interpretation contracts and deterministic normalization helpers.
- 2026-03-11: added durable `query_stage_traces` persistence plus migration `0005_query_stage_traces.py`.
- 2026-03-11: wired `QueryService.execute_until_interpretation()` and updated internal `POST /queries`.
- 2026-03-11: added Stage 2 tests for interpretation semantics, trace persistence, route behavior, and migration coverage.
