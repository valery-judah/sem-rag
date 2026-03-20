---
artifact_kind: workstream
id: WS-022
title: Api Docs
work_type: refactor
status: active
owner:
created: 2026-03-20
updated: 2026-03-20
---

# Summary
Enrich FastAPI endpoint and Pydantic model documentation with `json_schema_extra` to improve the local Swagger UI experience, ensuring every model has realistic examples and every endpoint has standard metadata (`summary`, `description`, `responses`).

## Current status
Most endpoints and response models are well-documented following the standards established in WS-010. However, several core models (e.g., `QueryAnswerResponse`, `DocumentDetailResponse`, `ErrorResponse`) and system endpoints (`/healthz`, `/readyz`) lack rich examples and metadata in `src/doc_forge/app/api.py`.

## Next step
- Update Pydantic models in `src/doc_forge/app/api.py` with `json_schema_extra` examples and update the system endpoint decorators.
