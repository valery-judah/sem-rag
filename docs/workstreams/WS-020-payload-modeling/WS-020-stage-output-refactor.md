# WS-020 Stage Output Refactor

## Summary
Split canonical replay artifacts from operational stage traces.

After this refactor:
- `query_stage_traces` remains the durable review/debug surface used by `QueryReviewService` and `/queries/{query_id}/trace`.
- `query_stage_outputs` becomes the canonical replay surface used by `QueryReplayService`.
- replay is no longer reconstructed from trace payloads.

## Architecture
### New persistence seam
- add `query_stage_outputs` keyed by `(query_id, stage_name)`
- persist `schema_version`, `payload_json`, and `created_at`
- write one row per successful stage
- overwrite deterministically when the same query/stage pair is saved again

### Canonical replay models
`src/doc_forge/query/stage_outputs.py` defines the replay contract:
- `InterpretStageOutput`
- `RetrieveStageOutput`
- `SelectStageOutput`
- `AssembleContextStageOutput`
- `AssessSupportStageOutput`
- `DecideAnswerModeStageOutput`
- `GenerateStageOutput`
- `QueryStageOutputsBundle`

The bundle intentionally excludes `render_citations`; final citations remain sourced from `query_answers`.

### Service orchestration
Each successful stage now returns:
- the existing domain result
- the existing `QueryStageTrace`
- a typed stage-output model

`QueryService` persists the trace and stage output together through a small helper. The refactor does not introduce a generic pipeline runner; it only removes duplicated persistence wiring.

### Replay behavior
`QueryReplayService` now builds bundles from:
- `query_runs`
- `query_snapshots`
- `query_stage_outputs`
- `query_answers`

Missing stage outputs resolve to partial replay state. There is no fallback to trace payloads.

## Interfaces
### Stable HTTP surface
No changes:
- `/queries/{query_id}/trace`
- `QueryTraceReview`
- `QueryTraceBundle`

### Internal Python surface
- `QueryService.__init__` accepts `stage_output_store`
- `QueryReplayService.__init__` requires `stage_output_store`
- `QueryReplayBundle` now exposes `stage_outputs` instead of `trace_bundle`

## Validation
The change should be covered by:
- stage-output persistence round trips
- replay reconstruction from canonical stage outputs
- replay resilience when trace payloads are mutated
- partial replay behavior when stage outputs are missing
- unchanged trace review behavior
- context bundle serialization using the new replay asset shape
