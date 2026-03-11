# Stage 5 Design: Deterministic Context Assembly

**Status:** Implemented  
**Applies to:** WS-006 / MVP / Stage 5  
**Last updated:** 2026-03-11

## Purpose

This document records the repo-facing design for Stage 5 deterministic context assembly in `parity`.

Stage 5 is the first stage that defines the actual model-facing input surface.
It turns Stage 4 evidence sets into an inspectable, policy-bounded `ContextManifest` without collapsing support semantics into prompt text or generation-time improvisation.

Stage 5 does not implement support assessment, answer-mode selection, answer generation, or citation rendering.
It earns the boundary between "selected evidence exists" and "this is the precise context the model is allowed to see."

## Authority and scope

This document is subordinate to:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
3. `docs/evergreen/agent-routing.md`
4. `docs/evergreen/api-contracts.md`
5. `docs/evergreen/eval-support-semantics.md`
6. [`04_query-lifecycle-requirements-final.md`](./04_query-lifecycle-requirements-final.md)
7. [`07_design.md`](./07_design.md)
8. [`14_stage-4-selection-evidence-set-construction-design.md`](./14_stage-4-selection-evidence-set-construction-design.md)
9. [`query_subsystem_staged_implementation_plan.md`](./query_subsystem_staged_implementation_plan.md)

This document describes internal repo shape and current implementation truth only.
It does not create a stable public API.

## Current repo fit

As of 2026-03-11, the repo now has the Stage 5 runtime implemented:

- [contracts.py](../../../../../src/parity/query/contracts.py) already defines `ContextManifest` and `QueryStageName.ASSEMBLE_CONTEXT`;
- [domain.py](../../../../../src/parity/query/domain.py) already reserves `QueryRuntimeState.context_manifest`;
- [policies.py](../../../../../src/parity/query/policies.py) already defines `QueryPolicy.context_token_budget`;
- [context_assembly.py](../../../../../src/parity/query/context_assembly.py) now owns deterministic context rendering and budget decisions;
- [context.py](../../../../../src/parity/query/stages/context.py) now executes `assemble_context` and persists Stage 5 traces;
- [service.py](../../../../../src/parity/query/service.py) now executes through Stage 5 with `execute_until_context_assembly()`;
- [api.py](../../../../../src/parity/app/api.py) now returns `context_manifest` in the internal debug response;
- evergreen architecture now records context assembly as implemented internal architecture.

Stage 5 extends the existing Stage 4 runtime without implying that any later answering behavior already exists.

## Outcome

Stage 5 is implemented with:

- deterministic context-assembly helpers in a new [context_assembly.py](../../../../../src/parity/query/context_assembly.py);
- an executable `assemble_context` stage in [context.py](../../../../../src/parity/query/stages/context.py);
- a strengthened `ContextManifest` contract in [contracts.py](../../../../../src/parity/query/contracts.py);
- Stage 5 runtime wiring in [service.py](../../../../../src/parity/query/service.py);
- internal route integration in [api.py](../../../../../src/parity/app/api.py) and [deps.py](../../../../../src/parity/app/deps.py);
- tests covering deterministic ordering, budget overflow behavior, exclusion reasons, and route behavior.

## Design constraints resolved in Stage 5

Stage 5 has to fit the repo exactly as it exists after Stage 4.

The relevant constraints are:

- Stage 1 already owns stable snapshot capture and `READY`-only queryability;
- Stage 2 already owns deterministic interpreted-query structure;
- Stage 3 already owns snapshot-scoped retrieval candidates with provenance-bearing locators;
- Stage 4 already owns deterministic evidence-set construction and durable `select` traces;
- the repo already exposes the minimum useful policy lever for this stage through `QueryPolicy.context_token_budget`;
- the read model already exposes chunk text, heading paths, ordinals, pages, and offsets, so Stage 5 does not reopen raw artifacts;
- `query_stage_traces` already exists and remains the single durable stage-trace surface;
- the internal `POST /queries` route is still a developer-visible seam and may expose Stage 5 state, but it must remain explicitly internal-only.

The design consequence is pragmatic:

- Stage 5 stays deterministic and local;
- it reuses Stage 4 evidence objects instead of rebuilding context from raw retrieval hits;
- it records all keep/drop decisions structurally rather than burying them in prompt strings;
- it prepares model-facing text blocks, but it does not perform any model call.

## Implemented shape

### Context-assembly helper seam

[context_assembly.py](../../../../../src/parity/query/context_assembly.py) now owns the deterministic helper seam for Stage 5.

It exposes:

- `ContextAssemblyDecision`
- `ContextAssemblyResult`
- `ContextAssembler`
- `DeterministicContextAssembler`
- reuse of `ContextItem` from [contracts.py](../../../../../src/parity/query/contracts.py) as the rendered manifest item shape

The helper owns:

- rendering one inspectable context item per evidence set;
- deterministic evidence-set ordering;
- duplicate suppression across already selected support;
- budget accounting;
- keep/drop decisions with explicit reasons;
- final `ContextManifest` construction.

### Strengthened `ContextManifest`

Stage 5 extends `ContextManifest` so it carries both manifest-level summary and inspectable per-item structure.

The implemented Stage 5 shape now includes:

- `ordered_evidence_set_ids`
- `included_evidence_set_ids`
- `dropped_evidence_set_ids`
- `inclusion_reasons`
- `exclusion_reasons`
- `token_budget`
- `token_budget_used`
- `context_items`
- `duplicate_suppression_notes`

`context_items` is a list of structured rendered units rather than one opaque prompt string.
Each item references exactly one `evidence_set_id` and includes:

- the rendered text forwarded to later model-facing stages;
- contributing document ids;
- heading-path scaffold when present;
- locators or page labels when present;
- estimated token count;
- assembly order.

The contract also now validates that:

- `token_budget_used` never exceeds `token_budget`;
- `context_items` line up exactly with `included_evidence_set_ids`;
- included and dropped evidence-set ids are disjoint;
- inclusion and exclusion reason maps cover the corresponding evidence-set ids exactly.

### Deterministic assembly unit

The unit of inclusion and truncation remains the evidence set, not arbitrary text clipping through the middle of already selected support.

Each included evidence set renders into one ordered `ContextItem` with:

1. a heading line derived from document title, evidence purpose, and recovered heading path;
2. one or more evidence-unit snippets in deterministic `unit_rank` order;
3. minimal provenance scaffold such as page label or passage anchor when available.

The implementation renders directly from Stage 4 `SourceReference` fields:

- `document_title`
- `heading_path`
- `page_label`
- `passage_anchor`
- `snippet`

It does not invent new provenance or attempt final citation formatting.

### Ordering policy

The implemented Stage 5 ordering policy is intentionally conservative:

1. preserve Stage 4 evidence-set order as the primary priority;
2. preserve evidence-unit `unit_rank` order inside each evidence set;
3. break unit ties by stable candidate identifiers already carried by the evidence units.

Stage 4 already applied the main reranking and grouping judgment.
Stage 5 preserves that meaning unless the context budget forces exclusions.

### Duplicate suppression in context assembly

Stage 4 already suppresses retrieval duplicates, but Stage 5 still applies a narrower duplicate check at render time because different evidence sets may carry overlapping support scaffolding.

The implemented duplicate suppression remains conservative:

- the primary evidence unit of an included evidence set is not dropped;
- repeated support units inside one rendered item are suppressed by snippet-plus-locator-plus-document identity;
- later evidence sets are dropped when their fully rendered context text duplicates an earlier included item;
- all of these suppressions are recorded in `duplicate_suppression_notes`.

This keeps the model-facing context dense without silently mutating Stage 4 evidence semantics.

### Budget estimation

Stage 5 needs deterministic budget accounting before any provider-specific prompt call exists.

For MVP, token accounting is an internal approximation based on rendered text length.
The implementation uses `_estimate_token_count()` in [context_assembly.py](../../../../../src/parity/query/context_assembly.py), which estimates tokens as `ceil(len(text) / 4)`.

This remains intentionally simple, deterministic, and local.
No provider-backed tokenizer is required to execute Stage 5.

### Inclusion and drop policy

The inclusion policy is deterministic and evidence-set-aware.

The implemented algorithm is:

1. render evidence sets into candidate context items in deterministic order;
2. include an item when the cumulative token budget still fits;
3. drop that whole evidence set when the rendered item would overflow the budget;
4. continue evaluating later evidence sets, which allows a smaller later item to fit even if an earlier lower-priority item was dropped over budget;
5. never partially clip an already selected evidence set.

This preserves the staged-plan commitment that the normal unit of truncation is the lower-value evidence set rather than arbitrary clipping.

### Keep/drop reasons

The runtime now captures structured reasons rather than free-form trace prose.

The current implementation uses:

- `included_within_budget`
- `included_primary_support_priority`
- `dropped_over_budget`
- `dropped_duplicate_rendering`
- `dropped_empty_rendering`

These values are persisted both in the manifest maps and in `ContextAssemblyDecision` records.

### Empty and degraded cases

The current implementation preserves honest degraded behavior:

- empty evidence input produces a valid empty `ContextManifest`;
- an evidence set that renders to empty content is excluded with `dropped_empty_rendering`;
- a very small budget may yield zero included items and only exclusion reasons;
- unsupported-query flags from Stage 2 do not bypass Stage 5;
- no fallback summary text is synthesized.

## Executable stage design

### `assemble_context` stage

[context.py](../../../../../src/parity/query/stages/context.py) is now the executable Stage 5 entrypoint.

The stage accepts:

- `query_id`
- `request`
- `snapshot`
- `interpreted_query`
- `evidence_sets`
- `policy`
- injected `ContextAssembler`

The stage returns:

- a structured Stage 5 result containing the `ContextManifest`;
- a `QueryStageTrace` for `assemble_context`.

### Trace payload

The Stage 5 trace payload remains structural and compact.

It currently includes:

- `interpreted_query`
- `snapshot_doc_ids`
- `evidence_set_ids`
- `token_budget`
- `token_budget_used`
- `included_evidence_set_ids`
- `dropped_evidence_set_ids`
- `inclusion_reasons`
- `exclusion_reasons`
- `duplicate_suppression_notes`
- `context_items`
- `decisions`

This keeps later debugging and eval work aligned with the local-failure principle from the requirements.

## Query service and route behavior

### Query service

[service.py](../../../../../src/parity/query/service.py) now exposes:

- `execute_until_context_assembly()`

That method performs:

1. Stage 1 query preparation
2. Stage 2 interpretation and `interpret` trace persistence
3. Stage 3 retrieval and `retrieve` trace persistence
4. Stage 4 selection and `select` trace persistence
5. Stage 5 context assembly and `assemble_context` trace persistence
6. return of `QueryRuntimeState` with `context_manifest`

`execute()` still stops before Stage 6 and raises that later stages are not yet implemented.

### Internal API surface

[api.py](../../../../../src/parity/app/api.py) now extends the internal `POST /queries` response with:

- `context_manifest`

The route now calls `QueryService.execute_until_context_assembly()` and returns the developer-visible message:

- `query context assembly completed; downstream stages are not implemented yet`

This remains an internal operator/developer surface only.
It does not create a stable external API.

### App wiring

[deps.py](../../../../../src/parity/app/deps.py) now wires:

- `DeterministicContextAssembler`
- Stage 5-ready `QueryService`

No provider-backed LLM or tokenizer is required to execute Stage 5.

## Validation coverage

Stage 5 is covered by:

- [test_query_context_assembly.py](../../../../../tests/query/test_query_context_assembly.py);
- expanded [test_query_service_retrieve.py](../../../../../tests/query/test_query_service_retrieve.py);
- expanded [test_runtime_api.py](../../../../../tests/app/test_runtime_api.py);
- expanded [test_query_contract_models.py](../../../../../tests/contract/test_query_contract_models.py).

The current coverage locks these Stage 5 invariants:

- context ordering is deterministic;
- evidence-unit order inside one rendered item is deterministic;
- budget overflow drops lower-priority evidence sets first;
- `token_budget_used` never exceeds `token_budget`;
- every included context item references an included evidence set id;
- every dropped evidence set receives an exclusion reason;
- empty evidence input still produces a valid `assemble_context` trace;
- the internal `/queries` route returns `context_manifest` and still stops before support assessment.

## Deferred from Stage 5

Stage 5 still does not implement:

- support-state judgment;
- answer-mode decision logic;
- any LLM call;
- final grounded answer generation;
- final citation rendering;
- provider-specific prompt-template commitments;
- semantic contradiction reconciliation across sources.

## Acceptance gate

Stage 5 is done in the repo because:

- the repo has an executable `assemble_context` stage;
- `ContextManifest` is a structured inspectable artifact rather than a thin summary shell;
- context inclusion and exclusion decisions are persisted in `query_stage_traces`;
- the internal `POST /queries` route returns Stage 5 state with an explicit stop before Stage 6.
