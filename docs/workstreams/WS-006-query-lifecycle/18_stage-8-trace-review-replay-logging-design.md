# Stage 8 Design: Review Surfaces, Replay Foundation, and Structured JSON Logging

**Status:** Proposed  
**Applies to:** WS-006 / MVP / Stage 8  
**Last updated:** 2026-03-11

## Purpose

This document records the repo-facing Stage 8 design for the next query-subsystem step after Stage 7.

Stage 8 is not another answer-quality stage.
It is the inspection and operations stage that makes the existing Stage 1-7 runtime reviewable, replayable, and observable enough for debugging and evaluation.

It introduces four related outcomes:

- internal read surfaces for prior query runs;
- replay primitives built from persisted artifacts rather than live corpus state;
- failure-localization helpers for operators and tests;
- structured JSON logs for live operational observability.

Stage 8 does not redesign:

- corpus-boundary capture;
- interpretation, retrieval, selection, or context assembly semantics;
- Stage 6 support-state and answer-mode policy;
- Stage 7 grounded-answer and citation-rendering policy;
- the evergreen public API boundary.

## Authority and scope

This document is subordinate to:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
3. `docs/evergreen/agent-routing.md`
4. `docs/evergreen/api-contracts.md`
5. `docs/evergreen/eval-support-semantics.md`
6. `docs/evergreen/eval-failure-taxonomy.md`
7. [`07_design.md`](./07_design.md)
8. [`16_stage-6-support-assessment-answer-mode-design.md`](./16_stage-6-support-assessment-answer-mode-design.md)
9. [`17_stage-7-grounded-generation-citation-rendering-design.md`](./17_stage-7-grounded-generation-citation-rendering-design.md)
10. [`query_subsystem_staged_implementation_plan.md`](./query_subsystem_staged_implementation_plan.md)

This document describes the intended next repo step.
It does not create a stable public API.

## Current repo fit

As of 2026-03-11, the repo already has the persistence needed to support most Stage 8 review work:

- [persistence.py](../../../../../src/parity/query/persistence.py) persists `query_runs`, `query_snapshots`, `query_stage_traces`, and `query_answers`;
- [trace.py](../../../../../src/parity/query/trace.py) already defines the ordered stage-trace surface;
- [service.py](../../../../../src/parity/query/service.py) already executes through Stage 7 and writes durable traces and final answer artifacts;
- [api.py](../../../../../src/parity/app/api.py) already exposes the internal `POST /queries` route, but no review routes yet;
- [test_runtime_api.py](../../../../../tests/app/test_runtime_api.py) already proves that successful query runs persist snapshots, ordered stage traces, and final answer artifacts.

What the repo still lacks is the read side and observability layer over that persisted state:

- no internal `GET /queries/{query_id}` summary route;
- no internal `GET /queries/{query_id}/trace` route;
- no internal `GET /queries/{query_id}/citations` route;
- no replay service that reconstructs prior run inputs from persisted artifacts;
- no structured JSON logging contract for live query execution.

## Proposed outcome

Stage 8 should add:

- one internal review service that hydrates persisted query artifacts into operator-facing models;
- one internal replay service that reconstructs stage inputs from persisted state without consulting current corpus state;
- three internal review endpoints backed by persisted state only;
- one structured JSON logging setup shared by app startup, HTTP handling, query execution, and failure reporting.

The design bias is deliberate:

- durable traces remain the canonical review artifact;
- logs remain the canonical live operations stream;
- review endpoints read persisted state and do not recompute answers;
- replay reconstructs prior inputs and can optionally re-execute deterministic stages, but is not yet a public HTTP capability.

## Design constraints resolved in Stage 8

Stage 8 has to fit the repo as it exists after Stage 7.

The relevant constraints are:

- query persistence already exists, so Stage 8 should extend a read side rather than re-found persistence from scratch;
- `query_stage_traces.payload_json` already carries the heavy structured artifacts and should remain the main review surface;
- `query_answers.citations_json` already holds the final citation bundle, so Stage 8 should not immediately split citations into a second normalized table without concrete pressure;
- internal query routes are still operator and test seams rather than evergreen public API;
- future provider-backed inference may make byte-for-byte replay unstable, so replay must distinguish artifact reconstruction from full semantic equivalence;
- operational logs must not duplicate full trace payloads or leak raw source text by default.

The result is a split-responsibility design:

- persistence tables hold durable query truth;
- review models compose that truth for humans and tests;
- replay bundles reconstruct past execution inputs;
- logs emit bounded operational facts and correlation metadata.

## Proposed persistence posture

Stage 8 should build on the current persistence model rather than replace it.

### Keep as the canonical durable artifacts

These existing tables remain primary:

- `query_runs`
- `query_snapshots`
- `query_stage_traces`
- `query_answers`

### Add only small terminal-state extensions

Stage 8 should add only the minimal extra fields that improve summary and failed-run inspection:

- `query_runs.completed_at`:
  - nullable terminal timestamp for both success and failure;
- `query_runs.terminal_failure_json`:
  - nullable structured summary for terminal failures that occur before `query_answers` exists.

`terminal_failure_json` should stay compact and sanitized.
Its intended shape is:

```json
{
  "error_code": "query_stage_failed",
  "error_class": "QueryStageContractViolationError",
  "stage_name": "render_citations",
  "message": "non-abstaining answers must carry citations",
  "trust_failure_labels": ["P1"]
}
```

This is a summary surface, not a replacement for stage traces.

### Do not add new normalized review tables yet

Stage 8 should explicitly avoid creating `query_citations`, `query_retrieval_candidates`, or `query_failures` tables unless review pressure proves the JSON trace shape insufficient.

The current repo already has:

- durable stage traces for detailed inspection;
- durable final-answer artifacts for final review;
- deterministic ordering and payload schemas that tests can depend on.

That is enough for MVP Stage 8 if the read side is clean.

## Proposed review contracts

Stage 8 should introduce a small review-model layer in `src/parity/query/` rather than leaking raw SQL rows into routes.

### `QueryRunReviewSummary`

This should be the payload behind `GET /queries/{query_id}`.

It should include:

- `query_id`
- `workspace_id`
- `question`
- `status`
- `submitted_at`
- `completed_at`
- `policy_snapshot`
- `snapshot_summary`
- `support_state`
- `answer_mode`
- `trust_failure_labels`
- `visible_limitations`
- `has_answer`
- `terminal_failure`
- stage-count and timing summary

### `QueryTraceReview`

This should be the payload behind `GET /queries/{query_id}/trace`.

It should include:

- run summary;
- captured corpus snapshot;
- ordered `QueryStageTrace` list;
- per-stage timing summary;
- final answer artifacts when present.

This route should return persisted stage payloads as stored.
It should not regenerate intermediate objects from live services.

### `QueryCitationReview`

This should be the payload behind `GET /queries/{query_id}/citations`.

It should include:

- `query_id`
- `support_state`
- `answer_mode`
- citation bundle loaded from persisted answer artifacts

This route must read from persisted answer state only.
It must not rerun citation rendering.

### `QueryReplayBundle`

This is an internal service/test model rather than an HTTP payload.

It should include:

- the original request envelope reconstructed from `query_runs`;
- the persisted `CorpusSnapshot`;
- the ordered `QueryStageTrace` list;
- final answer artifacts when present;
- the policy snapshot used by the original run.

The bundle is the frozen replay input.

## Review service design

Stage 8 should add a dedicated review-oriented service seam, for example `src/parity/query/review.py`.

It should own:

- loading one query run plus snapshot, traces, and answer artifacts;
- composing review summaries;
- building stage-timing summaries;
- mapping missing persisted artifacts into clear operator errors.

Suggested core methods:

- `get_query_summary(query_id: str) -> QueryRunReviewSummary`
- `get_query_trace_review(query_id: str) -> QueryTraceReview`
- `get_query_citations(query_id: str) -> QueryCitationReview`

This service should be read-only.
It should not mutate query state or rerun stages.

## Internal review endpoints

Stage 8 should add these internal routes in [api.py](../../../../../src/parity/app/api.py):

### `GET /queries/{query_id}`

Purpose:

- operator summary;
- test-harness lookup;
- fast inspection of answer vs abstention outcome.

Behavior:

- return a 404 when the query run does not exist;
- return persisted terminal-state information even for failed runs;
- avoid returning the full stage-trace payload by default.

### `GET /queries/{query_id}/trace`

Purpose:

- deep debugging;
- failure localization;
- regression triage.

Behavior:

- return the ordered persisted trace chain;
- include snapshot and final answer artifacts when present;
- include stage timing summary derived from trace timestamps.

### `GET /queries/{query_id}/citations`

Purpose:

- citation inspection;
- review-tool integration;
- source-provenance validation.

Behavior:

- load citations from persisted answer artifacts only;
- return 404 when the run or answer artifacts do not exist;
- return an empty citation bundle only for persisted abstention cases that recorded one.

These routes remain internal.
They do not update the evergreen API contract.

## Replay foundation design

Stage 8 replay should start as an internal service and test seam, for example `src/parity/query/replay.py`.

Its first job is reconstruction, not immediate full rerun.

### Replay levels

Stage 8 should distinguish three replay levels:

1. `hydrate_only`
   - load persisted run, snapshot, traces, and final artifacts into a `QueryReplayBundle`;
2. `reconstruct_inputs`
   - rebuild the stage-to-stage input objects from persisted trace payloads;
3. `reexecute_deterministic`
   - optionally rerun deterministic stages against the frozen replay bundle for regression checks.

Only levels 1 and 2 are mandatory for Stage 8.
Level 3 should be implemented only where the current deterministic helpers make it cheap and stable.

### Replay invariants

Replay must:

- use the persisted corpus snapshot rather than current workspace readiness state;
- use the persisted policy snapshot rather than current defaults;
- preserve original stage order and recorded outputs;
- refuse to silently widen a failed or incomplete run into a synthetic success;
- keep artifact reconstruction separate from any later provider-backed re-execution.

### Replay comparison posture

For deterministic stages already in the repo, replay may compare:

- structured payload equality;
- stage count and ordering;
- support state and answer mode;
- citation material-document coverage.

For future provider-backed stages, Stage 8 should compare:

- schema validity;
- policy conformance;
- support ceiling preservation;
- citation and trust-failure semantics;

not byte-for-byte answer text equality.

## Structured JSON logging design

Stage 8 should add live operational logging as a separate concern from durable traces.

### Recommended framework

The recommended logging stack is:

- `structlog` as the structured logging facade;
- standard-library `logging` as the sink and compatibility layer;
- JSON line output to stdout for all app and query-runtime logs.

`structlog` is the right fit here because it:

- integrates cleanly with FastAPI and Uvicorn;
- preserves standard logging interoperability;
- supports `contextvars` for request and query correlation;
- makes JSON output and field-level processors straightforward;
- avoids the global-magic tradeoffs of `loguru`.

Stage 8 should not introduce a separate bespoke logging abstraction.

### Logging output contract

Every log line should be one JSON object.
The base fields should be:

- `ts`
- `level`
- `event`
- `logger`
- `service`
- `environment`
- `request_id`
- `query_id`
- `workspace_id`
- `stage_name`
- `duration_ms`
- `status`

Error logs should additionally include:

- `error_class`
- `error_code`
- `message`

where `message` is sanitized and bounded.

### Event taxonomy

The first event families should be:

- `http.request.started`
- `http.request.completed`
- `query.run.started`
- `query.stage.started`
- `query.stage.completed`
- `query.run.completed`
- `query.run.failed`
- `review.query.loaded`
- `review.trace.loaded`
- `replay.bundle.built`

Event names should stay stable.
Free-form prose in `event` should be avoided.

### Correlation model

Stage 8 should bind:

- `request_id` in FastAPI middleware;
- `query_id` and `workspace_id` once a query run is created;
- `stage_name` inside stage-execution wrappers;
- optionally `doc_id` for lifecycle-side logs when helpful.

This should use `structlog.contextvars` rather than manual argument threading.

### Privacy and payload limits

Logs should not carry:

- raw document chunk text;
- full context manifests;
- full stage trace payloads;
- full question text by default;
- final answer text by default.

Instead, logs should carry compact diagnostics such as:

- `question_chars`
- `question_sha256`
- candidate, evidence-set, and citation counts
- support-state and answer-mode values
- top-level reason codes

The durable trace store already holds the detailed artifacts.
Logs should point to them with `query_id`, not duplicate them.

### Uvicorn and app integration

Stage 8 should route both app logs and Uvicorn access logs through the same JSON formatter so local runs and container logs stay machine-readable.

Suggested repo shape:

- `src/parity/app/logging.py`:
  - logger configuration and JSON processors;
- `src/parity/app/api.py`:
  - request-id middleware and route-level binding;
- [service.py](../../../../../src/parity/query/service.py):
  - query-run and stage lifecycle events;
- future review/replay modules:
  - read-side and replay events.

### Relationship between traces and logs

The contract should stay explicit:

- traces are durable, query-scoped, and inspection-grade;
- logs are streaming, operational, and bounded;
- traces answer "what evidence and policy produced this answer";
- logs answer "what is happening right now and where should I look".

Stage 8 should not treat logs as a substitute for persisted traces.

## Validation coverage

Stage 8 should add tests for:

- `GET /queries/{query_id}` returns persisted summary for successful runs;
- `GET /queries/{query_id}` returns persisted terminal failure information for failed runs;
- `GET /queries/{query_id}/trace` returns ordered persisted traces without recomputation;
- `GET /queries/{query_id}/citations` returns persisted citation bundles only;
- replay bundle construction reconstructs request, snapshot, policy, traces, and final artifacts from persisted state;
- replay uses persisted snapshot data rather than current corpus state;
- structured logs emit JSON objects with required correlation keys;
- query stage logs do not include oversized trace payloads or raw chunk text.

For the logging tests, validate parsed JSON fields rather than exact string formatting.

## Deferred from Stage 8

Stage 8 should explicitly defer:

- a public replay HTTP endpoint;
- OpenTelemetry export plumbing;
- log shipping configuration for specific vendors;
- SQL-normalized citation and retrieval-debug tables;
- a user-facing review UI;
- semantic diff tooling across replay runs.

## Acceptance gate

Stage 8 is done when:

- a reviewer can inspect a prior query run without recomputing it;
- failed and successful runs have inspectable persisted summary surfaces;
- replay can reconstruct frozen run inputs from persisted artifacts;
- live query execution emits correlated JSON logs suitable for local debugging and later aggregation;
- the subsystem is reviewable and observable enough to support Stage 9 evaluation hardening.
