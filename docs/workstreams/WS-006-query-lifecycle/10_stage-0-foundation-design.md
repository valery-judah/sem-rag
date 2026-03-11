# Stage 0 Design: Query Contracts and Scaffolding

**Status:** Draft  
**Applies to:** WS-006 / MVP / Stage 0  
**Last updated:** 2026-03-11

## Purpose

This document turns Stage 0 of [`query_subsystem_staged_implementation_plan.md`](./query_subsystem_staged_implementation_plan.md) into a concrete internal design for the current `parity` repo.

Its job is to define the minimum query-domain scaffolding that should exist before Stage 1 starts wiring queryable corpus boundaries and before any retrieval or generation logic is implemented.

Stage 0 is not a user-facing query feature. It is a repo-shaping step that makes later stages harder to distort.

## Authority and scope

This design is subordinate to:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
3. `docs/evergreen/api-contracts.md`
4. [`07_design.md`](./07_design.md)
5. [`query_subsystem_staged_implementation_plan.md`](./query_subsystem_staged_implementation_plan.md)

This document defines internal repo shape and contract seams only.
It does not create a stable public API.

## Stage 0 outcome

At the end of Stage 0, the repo should have:

- a dedicated internal `query` package;
- explicit semantic contracts for the query lifecycle;
- one canonical query policy object with defaults;
- placeholder stage modules that encode the intended runtime backbone;
- contract tests that lock enum values and object invariants;
- no real retrieval, interpretation, support assessment, or answer generation yet.

If Stage 0 accidentally produces an end-to-end `/queries` implementation, it has failed.

## Design constraints from the current repo

Stage 0 must fit the current repo rather than assume a greenfield service.

The design must respect the following facts from `docs/evergreen/architecture.md`:

- `parity` is one FastAPI application with one Postgres-backed persistence layer and filesystem artifacts already owned by the document lifecycle;
- `src/parity/_contracts/` already contains internal corpus contracts for documents, sections, chunks, retrieval hits, and answers;
- `src/parity/app/` owns the current internal runtime wiring;
- `src/parity/persistence/` already owns durable metadata persistence and migrations;
- `docs/evergreen/api-contracts.md` explicitly says there is no earned public API yet.

So Stage 0 should add internal seams, not public promises.

## Main design decisions

### 1. Add a dedicated `src/parity/query/` package

The query subsystem needs its own internal home instead of being spread across `app/`, `retrieval.py`, and ad hoc future modules.

Recommended initial layout:

```text
src/parity/query/
  __init__.py
  contracts.py
  domain.py
  errors.py
  policies.py
  persistence.py
  service.py
  trace.py
  stages/
    __init__.py
    interpret.py
    retrieve.py
    select.py
    evidence_sets.py
    context.py
    assess_support.py
    decide_answer_mode.py
    generate.py
    render_citations.py
```

This package should own query semantics only.
It should not absorb document-lifecycle code.

### 2. Add a narrow `src/parity/readmodels/` adapter for query-facing document reads

Stage 0 should reserve a query-facing document read surface now so Stage 1 has a clear place to implement `READY`-only snapshot reads.

Recommended initial layout:

```text
src/parity/readmodels/
  __init__.py
  documents.py
```

This adapter should remain read-only from the query subsystem's perspective.
It should shield `query/` from raw lifecycle persistence details.

### 3. Do not introduce a public query API in Stage 0

Stage 0 is internal scaffolding only.

That means:

- no stable `/queries` contract in evergreen docs;
- no public package API;
- no final request/response schema promises;
- no user-facing answer DTOs.

Internal Pydantic models are allowed.
Public contract promotion is not.

### 4. Keep inference seams narrow and internal

The repo already has embedding-related code under `src/parity/indexing/`.
Stage 0 should not force a broad new `inference/` package unless implementation pressure proves it necessary.

Instead:

- query contracts may define protocol-like expectations for embedding and LLM calls;
- concrete adapters can be supplied later via `app/deps.py` or nearby wiring;
- extraction of a shared inference package should wait until there are at least two real consumers with stable overlap.

This keeps Stage 0 aligned with the current repo shape.

### 5. Reserve explicit stage modules now, even if they are placeholders

The runtime path from [`07_design.md`](./07_design.md) is binding:

`Interpret -> Retrieve -> Select -> Assemble Context -> Assess Support -> Decide Answer Mode -> Generate -> Cite or Abstain`

Stage 0 should encode that structure in module boundaries before behavior exists.

That is the main defense against a future implementation collapsing into:

`retrieve -> prompt -> answer`

## Internal contract set

Stage 0 should define the following query-domain objects as internal Pydantic models.

### 1. Request and run envelope

- `QueryRequest`
  - natural-language question text
  - workspace or corpus boundary identifier
  - optional internal policy override object
- `QueryRun`
  - `query_id`
  - owning workspace id
  - received timestamp
  - run status
  - active policy snapshot reference or inline policy snapshot

### 2. Corpus boundary object

- `CorpusSnapshot`
  - workspace id
  - query start timestamp
  - eligible `doc_id` list
  - optional readiness/index version markers

This contract should exist in Stage 0 even though Stage 1 is where it becomes populated from the lifecycle read model.

### 3. Query interpretation object

- `InterpretedQuery`
  - normalized user intent
  - request type
  - answer-shape implications
  - synthesis intent flag
  - source-navigation intent flag
  - unsupported-question-type signal when applicable

The exact field set may evolve, but the object itself should exist from Stage 0 onward.

### 4. Retrieval and evidence objects

- `RetrievedCandidate`
  - `doc_id`
  - `chunk_id`
  - optional `section_id`
  - heading path
  - source-local locator data
  - retrieval score
  - retrieval rank
- `EvidenceUnit`
  - the minimal provenance-bearing support unit used in evidence grouping
- `EvidenceSet`
  - explicit grouping of one or more evidence units
  - grouping mode
  - rationale metadata

### 5. Context, support, and answer objects

- `ContextManifest`
  - ordered evidence set ids
  - inclusion and exclusion reasons
  - budget accounting
- `SupportAssessment`
  - support state
  - qualifying reasons
  - risk/failure hints
- `AnswerModeDecision`
  - allowed answer posture
  - downgrade explanation when applicable
- `AnswerDraft`
  - generated answer text plus limitation metadata
- `CitationBundle`
  - provenance-derived citation structures tied to evidence or answer spans

## Enum set to freeze in Stage 0

Stage 0 should freeze names for the following enum families.

### Query run status

Use a minimal set:

- `PENDING`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`

### Query stage name

Use the semantic stages directly:

- `INTERPRET`
- `RETRIEVE`
- `SELECT`
- `ASSEMBLE_CONTEXT`
- `ASSESS_SUPPORT`
- `DECIDE_ANSWER_MODE`
- `GENERATE`
- `RENDER_CITATIONS`

If intake or snapshot capture need trace entries later, add them as separate technical stage events without weakening the semantic path.

### Support state

Freeze the values from the current query design:

- `SUFFICIENT`
- `PARTIAL`
- `INSUFFICIENT`

Stage 0 must not invent alternate wording here because downstream eval semantics already depend on this family.

### Answer mode

Freeze a policy-facing family aligned to Stage 6 of the staged plan:

- `DIRECT_ANSWER`
- `NARROWED_ANSWER`
- `QUALIFIED_ANSWER`
- `FULL_ABSTENTION`
- `SCOPED_ABSTENTION`
- `QUALIFIED_UNCERTAINTY`

### Trust-failure label

Reserve a string enum or constant family for at least:

- `U1`
- `U2`
- `A1`
- `A2`
- `P1`
- `P2`
- `S1`

The meanings stay owned by the evergreen eval docs.
Stage 0 only reserves the code family so later policy and trace code do not invent ad hoc labels.

## Query policy design

Stage 0 should add exactly one canonical policy object under `src/parity/query/policies.py`.

Recommended shape:

- `QueryPolicyDefaults`
- `QueryPolicy`

`QueryPolicyDefaults` should provide the default values.
`QueryPolicy` should be the validated runtime object used by query orchestration.

### Policy fields to freeze now

- retrieval candidate cap
- evidence-set cap
- neighbor expansion enablement and cap
- duplicate suppression mode
- context token budget
- deterministic tie-break order
- support-state to answer-mode mapping
- citation rendering defaults

### Policy rules

- policy values must be explicit, not embedded in prompt templates;
- policy should be serializable for trace persistence;
- policy overrides should be internal-only in MVP;
- later stages may read policy, but stage modules should not own their own hidden defaults.

## Service and orchestration seam

Stage 0 should create `src/parity/query/service.py` with orchestration responsibility only.

Responsibilities:

- accept internal `QueryRequest`;
- coordinate the stage sequence;
- attach policy defaults;
- create or update `QueryRun`;
- hand off to stage modules when later stages are implemented.

Non-responsibilities:

- raw SQL access;
- embedding or LLM provider details;
- response formatting as a public API contract;
- document lifecycle mutation.

`service.py` should become the narrow query-domain entrypoint for future route wiring.

## Trace seam

Stage 0 should create `src/parity/query/trace.py` for structured stage trace payloads.

It should define internal trace shapes, not storage tables yet.

Minimum trace contracts:

- `QueryStageTrace`
  - `query_id`
  - stage name
  - started/finished timestamps
  - stage status
  - structured payload
- `QueryTraceBundle`
  - run envelope plus ordered stage traces

Stage 0 does not need to persist these to Postgres yet.
It does need the payload shapes so later stages stop inventing one-off trace blobs.

## Persistence seam

Stage 0 should create `src/parity/query/persistence.py`, but only as an internal seam definition.

This file should define repository interfaces or storage models for:

- query runs;
- query stage traces;
- final query answers;
- citations.

It should not yet force a migration unless implementation immediately needs one.

That keeps Stage 0 small while preventing Stage 1 and Stage 8 from improvising incompatible persistence shapes.

## Error model

Stage 0 should add `src/parity/query/errors.py` for query-domain exceptions.

Minimum error families:

- invalid query request
- workspace or corpus boundary unavailable
- stage contract violation
- unsupported internal policy override

Do not use transport-layer `HTTPException` inside the query package.
Transport translation belongs at the app boundary.

## Contract relationship to existing `_contracts`

The existing `src/parity/_contracts/` package already owns document, section, chunk, provenance, and lifecycle primitives.

Stage 0 should not duplicate those semantics blindly.

Use this rule:

- keep document-side truth in `_contracts`;
- create query-specific contracts in `query/contracts.py`;
- reference document-side identifiers and provenance-bearing fields rather than cloning whole lifecycle models into query.

This keeps query contracts explicit without creating a second source of truth for document semantics.

## Stage 0 test plan

Stage 0 should add focused contract tests, not end-to-end query behavior tests.

Recommended test slices:

- `tests/contract/test_query_contract_models.py`
  - serialization and invariant coverage for query-domain objects
- `tests/contract/test_query_policy_defaults.py`
  - default presence and answer-mode mapping coverage
- `tests/contract/test_query_stage_enums.py`
  - locked enum names and stage ordering assumptions

Stage 0 should not yet add retrieval-quality, support-quality, or answer-quality tests.
Those belong to later stages.

## Acceptance criteria

Stage 0 is done when all of the following are true:

- `src/parity/query/` exists with the planned internal module skeleton;
- query-domain contracts serialize cleanly and reject invalid shapes;
- query stage names, support states, answer modes, and trust-failure label families are frozen in code;
- there is one canonical query policy object with explicit defaults;
- the repo has tests that lock those contracts;
- no public API contract has been promoted prematurely;
- no retrieval-plus-generation shortcut exists under the name of Stage 0.

## Explicit non-goals

Stage 0 does not:

- implement `/queries`;
- read from `READY` documents yet;
- capture corpus snapshots;
- call an embedding model;
- call an LLM;
- retrieve passages;
- assess support;
- generate answers;
- render citations;
- persist real query traces.

Those are all later-stage concerns.

## Recommended implementation order inside Stage 0

1. Add `src/parity/query/` and placeholder `stages/` modules.
2. Add `src/parity/readmodels/` placeholders.
3. Define enums and query-domain Pydantic models in `query/contracts.py`.
4. Define `QueryPolicyDefaults` and `QueryPolicy`.
5. Add trace payload contracts.
6. Add repository seam definitions.
7. Add contract tests.
8. Stop.

The stop point matters.
If Stage 0 keeps going into retrieval or route wiring, the stage boundary has been violated.
