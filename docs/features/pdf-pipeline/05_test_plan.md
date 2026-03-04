# Test Plan: Hybrid PDF Pipeline Wiring

**Status:** Draft
**Last updated:** 2026-03-04

## CI-safe tests (no real engines)
- Default parser stream-drain safety:
  - Ensure bytes are not lost on pipeline error.
- Pipeline assembly from fake engine outputs:
  - Given synthetic Marker/MinerU raw JSON, adapters produce candidates and pipeline assembles
    intermediate.
- Placeholder policy:
  - Both engines fail for a page: deterministic placeholder emitted.
- Artifact determinism:
  - With fixed inputs and fake outputs, emitted artifacts are byte-identical across runs.

## Local-only validation (real engines)
- Manual smoke run against a small local PDF set.
- Validate:
  - engine logs captured
  - selection log emitted
  - extracted + parsed JSON emitted
  - parsed document validates under strict invariants

