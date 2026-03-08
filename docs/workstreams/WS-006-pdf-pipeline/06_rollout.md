# Rollout: Hybrid PDF Pipeline Wiring

**Status:** Draft
**Last updated:** 2026-03-04

## Rollout steps
1. Keep `enable_hybrid_pdf_pipeline=False` by default.
2. Enable locally for development and debugging.
3. Optionally introduce shadow mode later (emit artifacts, do not index) if needed.

## Monitoring
- Track:
  - engine run status distribution (ok/partial/error/timeout)
  - placeholder page rate
  - parse latency per engine
- Use emitted artifacts for reproducible debugging on regressions.

