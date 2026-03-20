---
artifact_kind: workstream
id: WS-025
title: Api Decoupling
work_type: refactor
status: active
owner:
created: 2026-03-20
updated: 2026-03-20
---

# Summary
Refactor the FastAPI boundary so `src/doc_forge/app/api.py` becomes app assembly only, stable HTTP DTO ownership moves into the app layer, and endpoint orchestration/logging/error translation live behind thin routers.


## Current status
- PR 1 has been executed: router modules have been successfully extracted and `api.py` reduced to app assembly.
- All stable route definitions are now located inside `src/doc_forge/app/routers/` while maintaining current functionality and OpenAPI specs.

## Next step
- Execute PR 2 from `[docs/workstreams/WS-025-api-decoupling/WS-025-plan.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-025-api-decoupling/WS-025-plan.md)`: introduce the app-layer orchestration seam to remove business logging and error translation from routers.
