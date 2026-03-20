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
- PR 2 has been executed and committed: app services now own endpoint orchestration, logging, exception translation, and API response shaping behind thin routers.
- PR 3 has been implemented in the current worktree and passes verification, but it is not yet committed.
- All stable route definitions are located inside `src/doc_forge/app/routers/`, and the app boundary cleanup is now in its final internal-model hardening phase.

## Next step
- Review and commit PR 3 from `[docs/workstreams/WS-025-api-decoupling/WS-025-plan.md](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-025-api-decoupling/WS-025-plan.md)`: finish the internal service-model cleanup and boundary hardening already staged in the worktree.
