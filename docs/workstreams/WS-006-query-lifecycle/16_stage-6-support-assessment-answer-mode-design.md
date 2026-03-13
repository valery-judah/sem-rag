# Stage 6 Design: Support Assessment and Answer-Mode Policy

**Status:** Implemented  
**Applies to:** WS-006 / MVP / Stage 6  
**Last updated:** 2026-03-11

## Purpose

This document records the repo-facing Stage 6 design as implemented in `doc_forge`.

Stage 6 is the trust-critical boundary between:

- "the system assembled some model-facing context"; and
- "the system is actually allowed to answer in a given posture."

It introduces two explicit executable stages:

- `assess_support`
- `decide_answer_mode`

Stage 6 does not implement grounded generation or citation rendering.
It earns the semantic control point that keeps later answer text from widening beyond what the evidence supports.

## Authority and scope

This document is subordinate to:

1. `docs/evergreen/mvp.md`
2. `docs/evergreen/architecture.md`
4. `docs/evergreen/api-contracts.md`
5. `docs/evergreen/eval-support-semantics.md`
6. `docs/evergreen/eval-failure-taxonomy.md`
7. [`04_query-lifecycle-requirements-final.md`](./04_query-lifecycle-requirements-final.md)
8. [`07_design.md`](./07_design.md)
9. [`15_stage-5-deterministic-context-assembly-design.md`](./15_stage-5-deterministic-context-assembly-design.md)
10. [`query_subsystem_staged_implementation_plan.md`](./query_subsystem_staged_implementation_plan.md)

This document describes internal repo shape and current implementation truth only.
It does not create a stable public API.

## Current repo fit

As of 2026-03-11, the repo now has the Stage 6 runtime implemented:

- [contracts.py](src/doc_forge/query/contracts.py) now defines `SupportQualifierReason` and strengthened `SupportAssessment` and `AnswerModeDecision` contracts;
- [policies.py](src/doc_forge/query/policies.py) now carries Stage 6 policy-version and support-ceiling flags in `QueryPolicy`;
- [support_assessment.py](src/doc_forge/query/support_assessment.py) now owns hybrid support assessment and the default deterministic support judge;
- [answer_mode_policy.py](src/doc_forge/query/answer_mode_policy.py) now owns deterministic answer-mode selection and downgrade-only enforcement;
- [assess_support.py](src/doc_forge/query/stages/assess_support.py) and [decide_answer_mode.py](src/doc_forge/query/stages/decide_answer_mode.py) are now executable Stage 6 entrypoints rather than placeholders;
- [service.py](src/doc_forge/query/service.py) now executes through Stage 6 with `execute_until_answer_mode()`;
- [api.py](src/doc_forge/app/api.py) now returns `support_assessment` and `answer_mode_decision` on the internal `POST /queries` route;
- [deps.py](src/doc_forge/app/deps.py) now wires Stage 6-ready query service dependencies.

Stage 6 extends the existing Stage 5 runtime without implying that Stage 7 answer generation or citation rendering already exists.

## Outcome

Stage 6 is implemented with:

- hybrid support-assessment helpers in [support_assessment.py](src/doc_forge/query/support_assessment.py);
- deterministic answer-mode policy helpers in [answer_mode_policy.py](src/doc_forge/query/answer_mode_policy.py);
- strengthened Stage 6 contracts in [contracts.py](src/doc_forge/query/contracts.py);
- executable `assess_support` and `decide_answer_mode` stages in [assess_support.py](src/doc_forge/query/stages/assess_support.py) and [decide_answer_mode.py](src/doc_forge/query/stages/decide_answer_mode.py);
- Stage 6 runtime wiring in [service.py](src/doc_forge/query/service.py);
- internal route integration in [api.py](src/doc_forge/app/api.py) and [deps.py](src/doc_forge/app/deps.py);
- tests covering unsupported-question, empty-evidence, conflict, cross-document coverage, service traces, and route behavior.

That outcome is enough to earn explicit support-state judgment and policy-selected answer posture before Stage 7 generation exists.

## Design constraints resolved in Stage 6

Stage 6 had to fit the repo exactly as it existed after Stage 5.

The relevant constraints were:

- Stage 1 already owned stable snapshot capture and `READY`-only queryability;
- Stage 2 already owned interpreted-query structure, including unsupported-capability flags and request-type distinctions;
- Stage 4 already owned explicit evidence sets, including `conflict_flags`;
- Stage 5 already owned the model-facing `ContextManifest`, token budget decisions, and inspectable per-item provenance scaffold;
- evergreen support semantics were canonical and used three support states rather than the older five-state workstream split;
- the repo still did not justify a general-purpose inference package or provider-specific LLM layer;
- `query_stage_traces` already existed and needed to remain the single durable stage-trace surface;
- the internal `POST /queries` route remained a developer/operator seam, not a public contract.

The implemented consequence is deliberate:

- Stage 6 keeps support state to the evergreen three-state contract;
- unsupported question type, conflict, provenance weakness, and scope narrowing are represented as qualifying reasons rather than extra support states;
- answer-mode selection stays deterministic and local;
- the current Stage 6 runtime uses an injectable deterministic support judge rather than a provider-backed model call;
- the internal route still stops before Stage 7 and returns an explicit incomplete-state message.

## Implemented contract changes

Stage 0 intentionally left `SupportAssessment` and `AnswerModeDecision` thin.
Stage 6 strengthens those contracts without turning them into a table-shaped persistence model.

### Stable reason-code layer

[contracts.py](src/doc_forge/query/contracts.py) now defines `SupportQualifierReason` with these current reason codes:

- `unsupported_question_type`
- `no_evidence_available`
- `missing_material_coverage`
- `scope_narrowing_required`
- `material_conflict`
- `provenance_too_weak`
- `source_navigation_locator_missing`

These reason codes are the deterministic policy surface between support assessment and answer-mode selection.

### Strengthened `SupportAssessment`

The implemented `SupportAssessment` now carries:

- `support_state`
- `qualifying_reason_codes`
- `trust_failure_labels`
- `summary`
- `unsupported_gaps`
- `conflicting_evidence_notes`
- `provenance_warnings`

This keeps Stage 6 compact enough for trace JSON while being explicit enough for answer-mode policy and later visible-limitation rendering.

### Strengthened `AnswerModeDecision`

The implemented `AnswerModeDecision` now carries:

- `answer_mode`
- `rationale`
- `based_on_support_state`
- `required_qualifying_reason_codes`
- `allowed_scope_summary`
- `must_surface_conflict`

This keeps the artifact policy-oriented rather than generation-oriented.
It tells Stage 7 what the answer layer is allowed to do, not how the prose should be phrased.

## Implemented policy additions

[QueryPolicy](src/doc_forge/query/policies.py) now includes the minimum additional Stage 6 policy levers:

- `support_assessment_policy_version`
- `answer_mode_policy_version`
- `source_navigation_requires_locator`
- `conflict_caps_support_at_partial`
- `provenance_weakness_caps_support_at_partial`

These remain explicit resolved policy values rather than hidden constants inside the stage modules.

The default policy versions are:

- `support_assessment.deterministic.v1`
- `answer_mode_policy.deterministic.v1`

## Implemented helper seams

### Support-assessment helper seam

[support_assessment.py](src/doc_forge/query/support_assessment.py) now owns the Stage 6 support-assessment helper seam.

It exposes:

- `SupportAssessmentPrecheck`
- `StructuredSupportJudgment`
- `SupportAssessmentResult`
- `SupportJudge` protocol
- `DeterministicSupportJudge`
- `HybridSupportAssessor`

The implemented helper owns:

- deterministic precheck evaluation;
- injectable support-judge behavior;
- deterministic post-rule narrowing;
- provisional Stage 6 trust-failure hooks.

The current default runtime uses `DeterministicSupportJudge`.
It does not perform a provider-backed model call.

### Answer-mode policy helper seam

[answer_mode_policy.py](src/doc_forge/query/answer_mode_policy.py) now owns the Stage 6 answer-policy helper seam.

It exposes:

- `AnswerModePolicyDecision`
- `AnswerModePolicy` protocol
- `DeterministicAnswerModePolicy`

The helper owns:

- baseline support-state to answer-mode mapping;
- qualifying-reason override precedence;
- downgrade-only enforcement;
- policy-version labeling for traces.

## Implemented support-assessment behavior

Stage 6 support assessment is implemented as a hybrid stage:

1. deterministic prechecks
2. one injectable structured support judgment
3. deterministic post-rules that preserve or narrow, but never widen

### Deterministic prechecks

The implemented precheck layer handles:

1. unsupported capability:
   - `unsupported_capability_flags` terminate the stage at `INSUFFICIENT` with `unsupported_question_type`
2. empty evidence:
   - no selected evidence or no included context items terminate the stage at `INSUFFICIENT` with `no_evidence_available`
3. source-navigation locator failure:
   - source-navigation requests without locators or heading-path scaffold terminate at `INSUFFICIENT` with `source_navigation_locator_missing`
4. cross-document coverage ceiling:
   - cross-document synthesis with only one contributing document caps support at `PARTIAL` with `missing_material_coverage`
5. conflict ceiling:
   - included evidence-set `conflict_flags` cap support at `PARTIAL` with `material_conflict`
6. provenance weakness ceiling:
   - missing inspectable provenance scaffold caps support at `PARTIAL` with `provenance_too_weak`

Prechecks are always persisted structurally in the Stage 6 trace payload, even when they do not terminate the stage.

### Current structured support judgment

The current default judge is deterministic rather than provider-backed.

`DeterministicSupportJudge` currently:

- returns `SUFFICIENT` for ordinary supported fact-lookup and source-navigation cases;
- returns `PARTIAL` for cross-document synthesis requests lacking multi-document support;
- returns `PARTIAL` for some broad non-fact requests when only one evidence set remains;
- returns `INSUFFICIENT` for unsupported request types or no included evidence.

The helper still treats the judge as injectable.
That keeps the Stage 6 seam ready for a later structured model call without changing the stage contract.

### Deterministic post-rules

The implemented post-rule layer:

- normalizes the final state to `SUFFICIENT`, `PARTIAL`, or `INSUFFICIENT`;
- unions reason codes and supporting notes from prechecks and the judge output;
- applies the most restrictive support ceiling when one exists;
- adds `scope_narrowing_required` when a partial-support result still contains material unsupported gaps;
- refuses to widen an `INSUFFICIENT` or `PARTIAL` case into `SUFFICIENT`.

The support ceiling order remains:

- `SUFFICIENT` may narrow to `PARTIAL` or `INSUFFICIENT`
- `PARTIAL` may narrow to `INSUFFICIENT`
- `INSUFFICIENT` may not widen

### Provisional trust-failure hooks

Stage 6 currently attaches sparse provisional trust-failure labels only when the evidence is clear:

- `unsupported_question_type` -> `S1`
- `provenance_too_weak` or `source_navigation_locator_missing` -> `P1`
- `missing_material_coverage` in a partial-support case -> `U2`
- `no_evidence_available` in an insufficient-support case -> `A2`

Stage 6 intentionally does not assign `U1`, `A1`, or `P2`.
Those require downstream answer or citation behavior that does not yet exist in the runtime.

## Implemented answer-mode policy behavior

Stage 6 answer-mode selection is fully deterministic.

It consumes:

- the final `SupportAssessment`
- the `InterpretedQuery`
- the resolved query policy

It does not call a model.

### Baseline mapping

The baseline support-state mapping in [policies.py](src/doc_forge/query/policies.py) remains:

- `SUFFICIENT` -> `DIRECT_ANSWER`
- `PARTIAL` -> `QUALIFIED_ANSWER`
- `INSUFFICIENT` -> `FULL_ABSTENTION`

### Implemented override precedence

The current `DeterministicAnswerModePolicy` applies overrides in this order:

1. unsupported-question-type handling
2. empty-evidence abstention
3. source-navigation locator failure handling
4. material-conflict handling
5. weak source-navigation provenance handling
6. explicit scope-narrowing handling

### Current default behavior

The implemented policy currently yields:

| Support input | Current answer mode |
|---|---|
| `INSUFFICIENT` + `unsupported_question_type` | `FULL_ABSTENTION` |
| `INSUFFICIENT` + `no_evidence_available` | `FULL_ABSTENTION` |
| `INSUFFICIENT` + `source_navigation_locator_missing` | `SCOPED_ABSTENTION` |
| `PARTIAL` + `material_conflict` | `QUALIFIED_UNCERTAINTY` |
| `PARTIAL` + `provenance_too_weak` on source-navigation requests | `SCOPED_ABSTENTION` |
| `PARTIAL` + `scope_narrowing_required` on precise fact/source-navigation requests | `NARROWED_ANSWER` |
| `PARTIAL` with no stronger override | `QUALIFIED_ANSWER` |
| `SUFFICIENT` with no narrowing reason | `DIRECT_ANSWER` |

The helper also returns:

- the baseline answer mode;
- the applied rule names;
- the policy version.

Those values are persisted in the Stage 6 trace payload and exercised by focused tests.

### Downgrade-only rule

The answer-mode stage is implemented as downgrade-only.

It may:

- preserve the baseline posture;
- narrow it;
- abstain more conservatively.

It must not:

- convert `PARTIAL` into `DIRECT_ANSWER`;
- convert `INSUFFICIENT` into a non-abstaining mode;
- ignore `material_conflict`, `unsupported_question_type`, or provenance-blocking qualifiers.

## Implemented stage traces

Stage 6 continues using [query_stage_traces](src/doc_forge/query/persistence.py) rather than introducing new normalized persistence tables.

### `assess_support` trace payload

The current Stage 6 support trace includes:

- `interpreted_query`
- `snapshot_doc_ids`
- `evidence_set_ids`
- `included_evidence_set_ids`
- `precheck_results`
- `support_ceiling`
- `structured_judgment`
- `qualifying_reason_codes`
- `summary`
- `unsupported_gaps`
- `conflicting_evidence_notes`
- `provenance_warnings`
- `trust_failure_labels`
- `final_support_state`
- `support_assessment_policy_version`

### `decide_answer_mode` trace payload

The current Stage 6 answer-mode trace includes:

- `based_on_support_state`
- `qualifying_reason_codes`
- `baseline_answer_mode`
- `applied_override_rules`
- `final_answer_mode`
- `allowed_scope_summary`
- `must_surface_conflict`
- `policy_version`

The full resolved `QueryPolicy` still lives on the persisted `QueryRun`.
Stage 6 traces only record the policy slice needed to explain the decision.

## Executable stage design

### `assess_support` stage

[assess_support.py](src/doc_forge/query/stages/assess_support.py) is now the executable Stage 6 support-assessment entrypoint.

It accepts:

- `query_id`
- `request`
- `snapshot`
- `interpreted_query`
- `evidence_sets`
- `context_manifest`
- `policy`
- injected support assessor

It returns:

- a structured Stage 6 result containing the `SupportAssessment`
- a `QueryStageTrace` for `assess_support`

### `decide_answer_mode` stage

[decide_answer_mode.py](src/doc_forge/query/stages/decide_answer_mode.py) is now the executable answer-policy entrypoint.

It accepts:

- `query_id`
- `request`
- `snapshot`
- `interpreted_query`
- `support_assessment`
- `policy`
- injected answer-mode policy helper

It returns:

- a structured Stage 6 result containing the `AnswerModeDecision`
- a `QueryStageTrace` for `decide_answer_mode`

Neither Stage 6 entrypoint synthesizes answer text, citations, or visible limitation prose.

## Query service and route behavior

### Query service

[service.py](src/doc_forge/query/service.py) now exposes:

- `execute_until_answer_mode()`

That method performs:

1. Stage 1 query preparation
2. Stage 2 interpretation and `interpret` trace persistence
3. Stage 3 retrieval and `retrieve` trace persistence
4. Stage 4 selection and `select` trace persistence
5. Stage 5 context assembly and `assemble_context` trace persistence
6. Stage 6 support assessment and `assess_support` trace persistence
7. Stage 6 answer-mode decision and `decide_answer_mode` trace persistence
8. return of `QueryRuntimeState` with `support_assessment` and `answer_mode_decision`

`execute()` still stops after answer-mode selection and raises that later stages are not implemented.

Query-run status remains `RUNNING` at this stage.
The repo still has no final answer artifact, so the run is not marked `SUCCEEDED` before Stage 7 exists.

### Internal API surface

[api.py](src/doc_forge/app/api.py) now extends the internal `POST /queries` response with:

- `support_assessment`
- `answer_mode_decision`

The route now calls `QueryService.execute_until_answer_mode()` and returns the developer-visible message:

- `query support assessment completed; grounded generation and citation rendering are not implemented yet`

This remains an internal operator/developer surface only.
It does not create a stable external API.

### App wiring

[deps.py](src/doc_forge/app/deps.py) now wires:

- `HybridSupportAssessor`
- `DeterministicAnswerModePolicy`

Tests can still inject a fake or alternate support judge by replacing the assessor dependency at the service layer.

## Validation coverage

Stage 6 is covered by:

- [test_query_stage6.py](tests/query/test_query_stage6.py);
- expanded [test_query_service_retrieve.py](tests/query/test_query_service_retrieve.py);
- expanded [test_runtime_api.py](tests/app/test_runtime_api.py);
- expanded [test_query_contract_models.py](tests/contract/test_query_contract_models.py);
- expanded [test_query_policy_defaults.py](tests/contract/test_query_policy_defaults.py).

The current coverage locks these Stage 6 invariants:

- unsupported question types never yield non-abstaining answer modes;
- empty evidence never yields `SUFFICIENT` support or `DIRECT_ANSWER`;
- material conflict caps support and forces `QUALIFIED_UNCERTAINTY`;
- cross-document synthesis with only one contributing document cannot yield `SUFFICIENT`;
- the answer-mode policy remains downgrade-only relative to support state;
- service execution persists both Stage 6 traces;
- the internal `/queries` route returns Stage 6 artifacts and still stops before Stage 7.

## Deferred from Stage 6

Stage 6 still does not implement:

- final answer text generation;
- final citation rendering;
- final answer persistence;
- query-run completion beyond `RUNNING`;
- stable public service or package API;
- provider-backed support-judge integration.

## Acceptance gate

Stage 6 is done in the repo because:

- support assessment is executable and explicit rather than hidden inside answer generation;
- support state uses the evergreen three-state contract;
- unsupported question type, conflict, provenance weakness, and scope narrowing are represented as qualifying reasons rather than extra support states;
- answer posture is selected by deterministic policy logic;
- Stage 6 traces are durable and inspectable in `query_stage_traces`;
- the internal `POST /queries` route returns Stage 6 state with an explicit stop before Stage 7.
