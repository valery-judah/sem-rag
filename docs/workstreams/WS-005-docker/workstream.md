---
artifact_kind: workstream
id: WS-005
title: Docker
work_type: feature
status: active
owner:
created: 2026-03-11
updated: 2026-03-12
---

# Summary
Add a real Docker-backed local runtime and e2e test layer for the internal document lifecycle so engineers can validate the staged pipeline against real containers, Postgres, filesystem artifacts, and actual Markdown documents.

## Objective
Deliver a Markdown-first Docker workflow where:

- `docker compose up --build` starts the internal lifecycle stack locally
- `pytest -m e2e` exercises the real API, worker, Postgres, migrations, and artifact store
- `READY` is validated through persisted artifacts, persisted vector records, and real retrieval smoke behavior

## Non-goals
- PDF-specific Docker e2e scenarios
- retry/fault-injection Docker e2e scenarios
- public API stabilization
- a separate production-grade deployment architecture
- introducing a new vector backend beyond the current Postgres-backed indexing seam

## Current status
- A Docker runtime image now exists and supports `api`, `worker`, and one-shot `migrate` commands.
- A local `docker-compose.yml` stack now runs `db`, `migrate`, `api`, and `worker` services with shared artifact storage.
- The repo now has a Docker-backed `e2e` pytest marker and `make test-e2e` target.
- The Docker e2e suite validates:
  - Markdown upload to `READY`
  - real repo Markdown docs reaching `READY`
  - explicit persistence of `chunks`, `chunk_embeddings`, and `index_entries`
  - non-empty stored embedding payloads
  - document-scoped retrieval isolation across multiple documents
  - persisted chunk provenance via heading path plus coarse location fields
  - explicit unsupported PNG rejection over the real HTTP stack
- Docker Desktop socket auto-detection was added for local testcontainers runs on this machine layout.
- Remaining work, if this workstream continues, is follow-on coverage such as PDF Docker e2e and retry/failure injection scenarios.
- A follow-on hardening proposal now exists in `docs/workstreams/WS-005-docker/32_docker-hardening-plan.md` for improving the current split-runtime image, Compose defaults, and Docker operator workflow without changing the runtime topology.

## Next step
- Add the next Docker-backed slice only if needed: either PDF e2e coverage or a controlled retry/fault-injection scenario for index failure recovery.
- If the repo needs better container ergonomics before more e2e depth, implement the hardening proposal in `docs/workstreams/WS-005-docker/32_docker-hardening-plan.md`.

## Relevant context
- paths:
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `src/parity/runtime.py`
- `tests/e2e/`
- `docs/evergreen/runbook.md`
- `Makefile`
- `pyproject.toml`
- `docs/workstreams/WS-005-docker/31_status.md`
- components:
- internal FastAPI lifecycle app
- lifecycle worker loop
- Alembic migration path
- Postgres-backed indexing persistence
- filesystem artifact store
- Docker/testcontainers e2e harness
- constraints:
- do not add new product routes just for e2e
- keep the first Docker e2e slice Markdown-first
- keep e2e additive; do not slow down the default `make test` path
- verify vector persistence explicitly through existing Postgres tables rather than claiming it implicitly
- read first:
- `docs/evergreen/runbook.md`
- `docs/evergreen/architecture.md`
- `docs/workstreams/WS-004-document-lifecycle/21-design-exploration.md`
- `docs/workstreams/WS-004-document-lifecycle/22-staged.md`

## Workflow steps
1. Add a shared runtime entrypoint and Docker image for the internal lifecycle stack.
2. Add a manual compose stack for local operator use.
3. Add a pytest-managed Docker e2e harness using testcontainers.
4. Validate Markdown documents through `READY`, retrieval smoke, and persisted vector/index state.
5. Add focused Docker e2e scenarios for scope isolation, provenance, and unsupported input behavior.

## Validation
- `uv run ruff check tests/e2e/...`
- `uv run pytest tests/e2e --collect-only -m e2e -o addopts=-q`
- `uv run pytest tests/e2e -m e2e -o addopts=-q`
- `docker compose up --build`
- `GET /readyz` returning `200 {"status":"ok"}` from the compose API container
- explicit Postgres assertions for `chunks`, `chunk_embeddings`, and `index_entries`

## Linked artifacts
- `docs/workstreams/WS-005-docker/31_status.md`
- `docs/workstreams/WS-005-docker/32_docker-hardening-plan.md`
- `docs/evergreen/runbook.md`
- `docs/evergreen/architecture.md`
- `docs/workstreams/WS-004-document-lifecycle/21-design-exploration.md`
- `docs/workstreams/WS-004-document-lifecycle/22-staged.md`
