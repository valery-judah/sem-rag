---
artifact_kind: workstream
id: WS-009
title: Alembic Migration
work_type: feature
status: active
owner:
created: 2026-03-11
updated: 2026-03-12
---

# Summary
The repo moved from a dedicated Compose `migrate` service to Alembic-owned runtime startup migration. Startup migration is now coordinated with a PostgreSQL advisory lock so `api` and `worker` can start concurrently without racing, while Alembic remains the single schema authority.

## Objective
Simplify Docker DB startup while keeping Alembic as the single schema authority.

## Non-goals
- Replace Alembic with another migration framework.
- Introduce SQL schema bootstrap via `docker-entrypoint-initdb.d`.
- Change any public API contract.

## Current status
Implementation is complete for the main runtime and operator path.

- Added a lock-protected migration helper in `src/doc_forge/persistence/migrations/__init__.py`.
- Added runtime bootstrap through `DOC_FORGE_AUTO_MIGRATE` in `src/doc_forge/runtime.py`.
- Removed the dedicated Compose `migrate` service and simplified startup flow in `docker-compose.yml`.
- Hardened `make docker-smoke` in `Makefile` so it waits for API health and probes `/readyz` from inside the container.
- Added validation coverage in persistence and runtime-entrypoint tests.

The change was made to remove migration-container orchestration complexity, avoid concurrent startup migration races, keep Alembic as the only schema framework, and make Docker smoke validation depend on container health instead of immediate host-side curl timing.

## Next step
- Decide whether to harden the repo-wide `make fmt-check`, `make lint`, and `make type` baselines as separate follow-up work outside this workstream.

## Relevant context
- paths:
  - `src/doc_forge/persistence/migrations/__init__.py`
  - `src/doc_forge/runtime.py`
  - `docker-compose.yml`
  - `Makefile`
- components:
  - Alembic migration bootstrap
  - Runtime entrypoint
  - Docker startup flow
  - Smoke verification
- constraints:
  - Alembic remains canonical for schema changes.
  - Containerized `api` and `worker` may start concurrently.
  - Startup checks must not race API readiness.
- read first:
  - `docs/evergreen/runbook.md`
  - `docs/evergreen/architecture.md`

## Workflow steps
1. Compared the current repo with reference Alembic and Postgres-init patterns.
2. Chose Alembic-owned runtime migration instead of a separate migration service.
3. Implemented lock-protected startup migration plus Compose and smoke-path updates.

## Validation
- `make test` passed.
- Targeted Ruff checks on the changed files passed.
- `make docker-smoke` passed after it was changed to wait for API health and probe `/readyz` from inside the container.
- Repo-wide `make fmt-check`, `make lint`, and `make type` still have unrelated pre-existing failures outside this workstream.

## Linked artifacts
- `docs/evergreen/runbook.md`
- `docs/evergreen/architecture.md`
- Implementation evidence: `src/doc_forge/persistence/migrations/__init__.py`, `src/doc_forge/runtime.py`, `docker-compose.yml`, `Makefile`
