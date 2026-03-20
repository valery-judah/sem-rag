---
artifact_kind: workstream
id: WS-020
title: Payload Modeling
work_type: feature
status: completed
owner: 
created: 2026-03-20
updated: 2026-03-20
---

# Summary
Introduce structured Pydantic models for the `interpret` (Stage 2) and `retrieve` (Stage 3) trace payloads. This eliminates the need for manual `dict` parsing and `# pyright: ignore` pragmas in `QueryReplayService`, strictly aligning the pipeline boundaries with the repository's domain modeling conventions.

## Current status
The workstream has been fully executed. `InterpretationTracePayload` and `RetrievalTracePayload` are now standard Pydantic models in the pipeline, and `QueryReplayService` properly relies on boundary validation via `.model_validate()`. All `# pyright: ignore` overrides were removed, and the `uv run poe type` check runs cleanly. The 292-test suite continues to pass, proving backwards-compatible structural serialization.

## Next step
- Close the workstream.
- See `WS-020-stage-output-refactor.md` for the follow-up clean-slate replay architecture.
