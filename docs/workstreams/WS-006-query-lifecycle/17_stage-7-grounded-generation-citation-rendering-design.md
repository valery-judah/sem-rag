# Stage 7 Design: Grounded Generation and Citation Rendering

**Status:** Implemented  
**Applies to:** WS-006 / MVP / Stage 7  
**Last updated:** 2026-03-11

## Purpose

This document records the repo-facing Stage 7 design as implemented in `parity`.

Stage 7 is the first stage that produces the final user-visible answer.
It completes the internal query lifecycle after Stage 6 by:

- rendering answer text under the explicit Stage 6 support ceiling;
- rendering inspectable citations from stored provenance only;
- persisting final answer artifacts durably;
- marking the query run terminal only after final persistence succeeds.

Stage 7 does not redesign support assessment, answer-mode policy, review endpoints, or public API boundaries.
Those remain owned by Stage 6, Stage 8, and the evergreen API contract.

## Authority and scope

This document is subordinate to:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
3. `docs/evergreen/agent-routing.md`
4. `docs/evergreen/api-contracts.md`
5. `docs/evergreen/eval-support-semantics.md`
6. `docs/evergreen/eval-failure-taxonomy.md`
7. [`04_query-lifecycle-requirements-final.md`](./04_query-lifecycle-requirements-final.md)
8. [`07_design.md`](./07_design.md)
9. [`16_stage-6-support-assessment-answer-mode-design.md`](./16_stage-6-support-assessment-answer-mode-design.md)
10. [`query_subsystem_staged_implementation_plan.md`](./query_subsystem_staged_implementation_plan.md)

This document describes internal repo shape and current implementation truth only.
It does not create a stable public API.

## Current repo fit

As of 2026-03-11, the repo now has the Stage 7 runtime implemented:

- [contracts.py](../../../../../src/parity/query/contracts.py) now strengthens `AnswerDraft`, `CitationRecord`, and `CitationBundle`, and adds `FinalQueryArtifacts`;
- [answer_generation.py](../../../../../src/parity/query/answer_generation.py) now owns deterministic grounded answer generation;
- [citation_rendering.py](../../../../../src/parity/query/citation_rendering.py) now owns provenance-only citation rendering;
- [stages/generate.py](../../../../../src/parity/query/stages/generate.py) and [stages/render_citations.py](../../../../../src/parity/query/stages/render_citations.py) are now executable Stage 7 entrypoints rather than placeholders;
- [persistence.py](../../../../../src/parity/query/persistence.py) now defines `query_answers`, `SqlQueryAnswerStore`, and round-trip persistence for final answer artifacts;
- [0006_query_answers.py](../../../../../src/parity/persistence/migrations/versions/0006_query_answers.py) now creates the durable final-answer table;
- [service.py](../../../../../src/parity/query/service.py) now executes through Stage 7 with `execute_until_answer()`;
- [api.py](../../../../../src/parity/app/api.py) now returns final answer text, visible limitations, and citations on the internal `POST /queries` route;
- [deps.py](../../../../../src/parity/app/deps.py) now wires final-answer persistence through `SqlQueryAnswerStore`.

Stage 7 extends the existing Stage 6 runtime without implying that Stage 8 review and replay surfaces already exist.

## Outcome

Stage 7 is implemented with:

- deterministic answer generation in [answer_generation.py](../../../../../src/parity/query/answer_generation.py);
- deterministic citation rendering in [citation_rendering.py](../../../../../src/parity/query/citation_rendering.py);
- executable `generate` and `render_citations` stages in [generate.py](../../../../../src/parity/query/stages/generate.py) and [render_citations.py](../../../../../src/parity/query/stages/render_citations.py);
- final answer persistence in [persistence.py](../../../../../src/parity/query/persistence.py) and [0006_query_answers.py](../../../../../src/parity/persistence/migrations/versions/0006_query_answers.py);
- Stage 7 runtime wiring in [service.py](../../../../../src/parity/query/service.py);
- internal route integration in [api.py](../../../../../src/parity/app/api.py) and [deps.py](../../../../../src/parity/app/deps.py);
- tests covering direct-answer generation, honest abstention, citation fail-closed behavior, cross-document citation completeness, final persistence, and route behavior.

That outcome is enough to earn end-to-end internal answering over `READY` documents with durable final artifacts, while still leaving review endpoints and stable public contracts for later stages.

## Design constraints resolved in Stage 7

Stage 7 had to fit the repo exactly as it existed after Stage 6.

The relevant constraints were:

- Stage 6 already owned canonical `support_state`, qualifying reasons, and answer posture;
- later stages could preserve or narrow posture, but could not widen it;
- `ContextManifest` and `EvidenceSet` already formed the inspectable evidence boundary for the answer layer;
- citations had to derive from stored `SourceReference` provenance on evidence units rather than model-written locators;
- `query_stage_traces` already existed and needed to remain the canonical stage-trace surface;
- the internal `POST /queries` route remained a developer/operator seam rather than a public contract.

The implemented consequence is deliberate:

- Stage 7 generation consumes Stage 6 outputs as a ceiling rather than as hints;
- visible limitations are deterministic artifacts, not optional prompt flourish;
- citations are rendered after generation from provenance-bearing evidence objects;
- non-abstaining answers fail closed when citations cannot be rendered;
- the current Stage 7 runtime remains deterministic rather than provider-backed.

## Implemented contract changes

Stage 0 intentionally left answer and citation artifacts thin.
Stage 7 strengthens those contracts so final answer persistence and Stage 8 review work have a durable surface.

### Strengthened `AnswerDraft`

The implemented `AnswerDraft` now carries:

- `answer_text`
- `visible_limitations`
- `should_render_citations`
- `grounded_evidence_set_ids`
- `generator_version`

`grounded_evidence_set_ids` is the ordered subset of included evidence sets that the generated answer is grounded on.
That keeps citation rendering tied to inspectable support rather than to answer-text parsing.

### Strengthened `CitationRecord`

The implemented `CitationRecord` now carries:

- `evidence_set_id`
- `source_reference`
- `support_role`

That keeps final citations connected to the Stage 4 and Stage 5 evidence surfaces.

### Strengthened `CitationBundle`

The implemented `CitationBundle` now carries:

- `citations`
- `material_doc_ids`
- `renderer_version`

`material_doc_ids` is the deterministic document-level summary used by tests and later review surfaces to check cross-document citation completeness.

### New `FinalQueryArtifacts`

The implemented `FinalQueryArtifacts` now carries:

- `answer`
- `citations`
- `support_state`
- `qualifying_reason_codes`
- `answer_mode`
- `trust_failure_labels`
- `created_at`

This is the persistence-facing Stage 7 artifact.
It lets the final-answer store persist the user-visible outcome without reconstructing it from stage traces.

## Implemented helper seams

### Grounded-generation helper seam

[answer_generation.py](../../../../../src/parity/query/answer_generation.py) now owns the Stage 7 grounded-generation seam.

It exposes:

- `GroundedAnswerGenerator` protocol
- `GroundedGenerationResult`
- `DeterministicGroundedAnswerGenerator`

The current implementation is deterministic and template-driven.
It does not call a provider-backed model.

The helper currently accepts:

- `QueryRequest`
- `CorpusSnapshot`
- `InterpretedQuery`
- `ContextManifest`
- `SupportAssessment`
- `AnswerModeDecision`
- resolved `QueryPolicy`

It returns:

- the final `AnswerDraft`
- deterministic `visible_limitations`
- `generator_version`

### Citation-rendering helper seam

[citation_rendering.py](../../../../../src/parity/query/citation_rendering.py) now owns the Stage 7 citation-rendering seam.

It exposes:

- `CitationRenderer` protocol
- `CitationRenderingResult`
- `DeterministicCitationRenderer`

The helper currently accepts:

- `InterpretedQuery`
- `EvidenceSet` list
- `ContextManifest`
- `SupportAssessment`
- `AnswerModeDecision`
- `AnswerDraft`
- resolved `QueryPolicy`

It returns:

- final `CitationBundle`
- `provenance_warnings`
- `renderer_version`

The renderer does not inspect answer text to invent locators.
It derives citations only from stored `SourceReference` values already carried on evidence units.

## Implemented generation behavior

The current Stage 7 generator is answer-mode aware and deterministic.
It derives `visible_limitations` first and then renders answer text that stays inside the allowed posture.

### Direct answer

For `DIRECT_ANSWER`, the current implementation:

- renders answer text from assembled support snippets;
- preserves the Stage 6 support ceiling;
- does not add visible limitations by default;
- requires citations downstream.

### Narrowed answer

For `NARROWED_ANSWER`, the current implementation:

- answers only the supported narrower scope;
- prefixes the answer with an explicit narrowing cue;
- includes visible limitation language;
- requires citations downstream.

### Qualified answer

For `QUALIFIED_ANSWER`, the current implementation:

- answers from supported snippets;
- appends qualification language when required;
- keeps unsupported scope visible through `visible_limitations`;
- requires citations downstream.

### Full abstention

For `FULL_ABSTENTION`, the current implementation:

- returns explicit insufficient-support language;
- leaves `grounded_evidence_set_ids` empty;
- sets `should_render_citations` to `False`;
- allows an empty citation bundle.

### Scoped abstention

For `SCOPED_ABSTENTION`, the current implementation:

- declines the full request explicitly;
- preserves any narrower supported text that exists;
- includes visible limitation language;
- requires citations for the supported material it does present.

### Qualified uncertainty

For `QUALIFIED_UNCERTAINTY`, the current implementation:

- surfaces the first conflict note when one exists;
- avoids flattening conflict into a false direct answer;
- includes visible limitation language;
- requires citations downstream.

## Implemented visible-limitations behavior

Visible limitations are constructed deterministically before final answer text is returned.

The current generator derives them from:

- `AnswerModeDecision.allowed_scope_summary` for non-direct modes;
- `qualifying_reason_codes`;
- `unsupported_gaps`;
- `conflicting_evidence_notes`;
- `provenance_warnings`.

The current implementation deduplicates those messages and persists them separately on `AnswerDraft`.
They are also returned separately on the internal `/queries` route.

## Implemented citation-rendering behavior

Citation rendering now happens after answer generation, but it does not depend on answer text for provenance.

### Citation source of truth

The renderer uses only:

- `AnswerDraft.grounded_evidence_set_ids`
- evidence units in those grounded evidence sets
- their attached `SourceReference` objects
- citation policy toggles for heading-path and locator inclusion

If `grounded_evidence_set_ids` is empty for a cited answer, the renderer raises `QueryStageContractViolationError`.

### Citation completeness rules

The current implementation enforces these behaviors:

- non-abstaining answers must produce at least one citation;
- full abstention may return an empty citation bundle;
- cross-document synthesis must cite every materially contributing document in grounded evidence;
- citations are deduplicated only by document plus local locator shape, not by document alone.

### Locator rules

The renderer stays inside the repo’s current provenance model:

- PDFs prefer `page_label` when present;
- Markdown may use `heading_path`, `section_id`, or `passage_anchor`;
- heading-path and locator inclusion honor the resolved query policy;
- page labels, section ids, heading paths, and passage anchors are never fabricated.

### Fail-closed behavior

For non-abstaining answers, the current implementation fails closed when:

- no grounded evidence set ids are available for citation rendering;
- no usable citations can be derived from grounded provenance;
- a synthesis answer omits a materially contributing document from the final citation bundle.

Those failures currently surface as `QueryStageContractViolationError` and cause the query run to finish as `FAILED`.
Stage 7 does not yet add a new dedicated failure artifact or failure-specific Stage 7 trust label.

## Implemented stage traces

Stage 7 continues using [query_stage_traces](../../../../../src/parity/query/persistence.py) rather than introducing new normalized trace tables.

### `generate` trace payload

The current `generate` trace includes:

- `based_on_support_state`
- `based_on_answer_mode`
- `visible_limitations`
- `grounded_evidence_set_ids`
- `answer_text`
- `should_render_citations`
- `generator_version`

### `render_citations` trace payload

The current `render_citations` trace includes:

- `grounded_evidence_set_ids`
- `citation_count`
- `citation_doc_ids`
- `citation_support_roles`
- `provenance_warnings`
- `renderer_version`

Stage 7 persists those traces only on successful stage completion.
Fail-closed rendering currently aborts execution before a successful Stage 7 citation trace is appended.

## Implemented final persistence

Stage 7 now adds a concrete SQL-backed final-answer store in [persistence.py](../../../../../src/parity/query/persistence.py).

### `query_answers`

The current `query_answers` table stores:

- `query_id`
- `answer_text`
- `visible_limitations_json`
- `should_render_citations`
- `grounded_evidence_set_ids_json`
- `support_state`
- `qualifying_reason_codes_json`
- `answer_mode`
- `citations_json`
- `trust_failure_labels_json`
- `generator_version`
- `renderer_version`
- `created_at`

This shape is intentionally JSON-forward and compact.
It is enough for final answer replay, Stage 8 review work, and persistence of terminal user-visible artifacts without reconstructing them from traces.

### `SqlQueryAnswerStore`

The current concrete store:

- persists final answer artifacts transactionally per query id;
- overwrites any existing final-answer row for the same query id;
- round-trips `FinalQueryArtifacts` back into internal models for tests and later review surfaces.

## Executable stage design

### `generate` stage

[generate.py](../../../../../src/parity/query/stages/generate.py) is now the executable Stage 7 grounded-generation entrypoint.

It accepts:

- `query_id`
- `request`
- `snapshot`
- `interpreted_query`
- `context_manifest`
- `support_assessment`
- `answer_mode_decision`
- `policy`
- injected generator

It returns:

- a structured result containing the `AnswerDraft`
- a `QueryStageTrace` for `generate`

### `render_citations` stage

[render_citations.py](../../../../../src/parity/query/stages/render_citations.py) is now the executable Stage 7 citation-rendering entrypoint.

It accepts:

- `query_id`
- `request`
- `snapshot`
- `interpreted_query`
- `evidence_sets`
- `context_manifest`
- `support_assessment`
- `answer_mode_decision`
- `answer_draft`
- `policy`
- injected renderer

It returns:

- a structured result containing the `CitationBundle`
- a `QueryStageTrace` for `render_citations`

## Query service and route behavior

### Query service

[service.py](../../../../../src/parity/query/service.py) now exposes:

- `execute_until_answer()`

That method currently performs:

1. Stage 1 query preparation
2. Stage 2 interpretation and `interpret` trace persistence
3. Stage 3 retrieval and `retrieve` trace persistence
4. Stage 4 selection and `select` trace persistence
5. Stage 5 context assembly and `assemble_context` trace persistence
6. Stage 6 support assessment and `assess_support` trace persistence
7. Stage 6 answer-mode decision and `decide_answer_mode` trace persistence
8. Stage 7 grounded generation and `generate` trace persistence
9. Stage 7 citation rendering and `render_citations` trace persistence
10. final answer persistence in `query_answers`
11. query-run status update to `SUCCEEDED`

If Stage 7 fails after the run has started, the service updates `query_runs.status` to `FAILED` before surfacing the error.

`execute()` now delegates to `execute_until_answer()` when final-answer persistence is configured.

### Internal API surface

[api.py](../../../../../src/parity/app/api.py) now returns the internal Stage 7 response shape on `POST /queries`.

The route now returns:

- `query_id`
- `workspace_id`
- `status`
- `answer`
- `support_state`
- `answer_mode`
- `visible_limitations`
- `citations`

Because the route remains internal and non-contractual, it also continues returning debug artifacts such as:

- snapshot
- interpreted query
- retrieved candidates
- selected candidates
- evidence sets
- context manifest
- support assessment
- answer-mode decision

The route status is now `200 OK`.
The developer-visible message is now:

- `query answer completed with grounded generation and rendered citations`

### App wiring

[deps.py](../../../../../src/parity/app/deps.py) now wires:

- Stage 1 through Stage 6 dependencies as before
- concrete `SqlQueryAnswerStore`

`QueryService` itself now provides deterministic Stage 7 defaults for:

- `DeterministicGroundedAnswerGenerator`
- `DeterministicCitationRenderer`

That keeps the local runtime executable without introducing a provider dependency into repo truth.

## Validation coverage

Stage 7 is covered by:

- [test_query_stage7.py](../../../../../tests/query/test_query_stage7.py);
- expanded [test_query_service_retrieve.py](../../../../../tests/query/test_query_service_retrieve.py);
- expanded [test_runtime_api.py](../../../../../tests/app/test_runtime_api.py);
- expanded [test_query_contract_models.py](../../../../../tests/contract/test_query_contract_models.py);
- expanded [test_query_stage_enums.py](../../../../../tests/contract/test_query_stage_enums.py);
- expanded [test_postgres_migrations.py](../../../../../tests/persistence/test_postgres_migrations.py).

The current coverage locks these Stage 7 invariants:

- direct answers carry grounded evidence set ids and rendered citations;
- full abstention remains honest and returns no citations;
- cited answers cannot complete without grounded evidence set ids;
- cross-document synthesis must cite every materially contributing document;
- final answer artifacts persist in `query_answers`;
- service execution persists both Stage 7 traces on success;
- the internal `/queries` route returns final Stage 7 artifacts instead of the Stage 6 placeholder message.

## Deferred from Stage 7

Stage 7 still does not implement:

- public API stabilization;
- Stage 8 review and replay endpoints;
- claim-span or sentence-level citation alignment;
- provider-backed generator integration as runtime truth;
- dedicated Stage 7 failure traces for closed citation-rendering failures;
- richer user-facing citation presentation beyond the current stored provenance shape.

## Acceptance gate

Stage 7 is done in the repo because:

- the system now answers end to end over `READY` documents through the internal query path;
- answer text is generated under the explicit Stage 6 support ceiling rather than by free-form post-support behavior;
- visible limitations are persisted and returned as first-class artifacts;
- citations are rendered only from stored provenance;
- non-abstaining answers fail closed on unusable provenance;
- final answer artifacts are durably persisted;
- query runs become terminal only after final Stage 7 completion.
