# WS-005 Status

**Date:** 2026-03-11  
**Scope of this note:** current status of the Docker runtime and Docker-backed end-to-end suite for the internal document lifecycle.

## What is currently in place

The repo has a working Docker path for the internal lifecycle runtime and a passing Docker-backed e2e suite.

Current repo assets:

* shared runtime entrypoint:
  * `src/parity/runtime.py`
* Docker runtime assets:
  * `Dockerfile`
  * `.dockerignore`
  * `docker-compose.yml`
* Docker-backed e2e suite:
  * `tests/e2e/conftest.py`
  * `tests/e2e/test_markdown_stack_smoke.py`
  * `tests/e2e/test_pdf_stack.py`
  * `tests/e2e/test_real_markdown_docs.py`
  * `tests/e2e/test_stack_failures.py`
* repo wiring for the e2e suite:
  * `pyproject.toml` marker `e2e`
  * default pytest exclusion for `e2e`
  * `make test-e2e`
* operating docs:
  * `docs/evergreen/runbook.md`

## What the Docker e2e suite currently proves

The active e2e suite validates the following against real containers:

* Markdown upload reaches `READY`
* PDF upload reaches `READY`
* malformed PDF upload reaches `FAILED` without published retrieval artifacts
* unsupported PNG upload is rejected over the real HTTP stack
* the API and worker run as separate processes
* migrations run before the stack serves requests
* real repo Markdown documents can be uploaded and indexed
* persisted artifact files exist for raw, extracted, and normalized stages
* Postgres contains persisted `chunks`, `chunk_embeddings`, and `index_entries`
* embedding payloads are non-empty JSON vectors with a stored embedding model
* retrieval stays document-scoped across multiple uploaded docs
* persisted chunks retain heading-path plus coarse provenance fields
* PDF chunks retain page-oriented provenance

## Documents and fixtures used in the suite

Real repo Markdown docs used in e2e coverage:

* `docs/workstreams/WS-004-document-lifecycle/21-design-exploration.md`
* `docs/workstreams/WS-004-document-lifecycle/22-staged.md`
* `docs/evergreen/mvp.md`

Synthetic fixtures used in e2e coverage:

* `tests/e2e/fixtures/smoke.md`
* `tests/e2e/fixtures/ready_text_pdf.pdf`
* `tests/e2e/fixtures/malformed.pdf`

## Validation confirmed on 2026-03-11

The following checks were confirmed against the current repo:

* `uv run pytest tests/e2e --collect-only -m e2e -o addopts=-q`
* `make test-e2e`

Observed result:

* `8 passed in 45.49s`

Manual compose-path verification was also completed:

* `docker compose up --build -d`
* `docker compose ps`
* `/readyz` returned `{"status":"ok"}`

## Current shape of the local Docker stack

The compose stack currently defines:

* `db`
* `migrate`
* `api`
* `worker`

Important runtime facts:

* `api` and `worker` both depend on a healthy database plus successful `migrate`
* the stack uses Postgres plus a bind-mounted artifact root at `./data`
* the Docker e2e suite is additive and excluded from default pytest runs
* the vector persistence proof uses the existing Postgres tables:
  * `chunks`
  * `chunk_embeddings`
  * `index_entries`
* local Docker Desktop socket auto-detection exists in `tests/e2e/conftest.py` for environments where the daemon socket is under `~/.docker/run/docker.sock`

## What is still not covered by this Docker slice

The current Docker layer still does not prove all desired failure and recovery behavior.

Not covered today:

* retry recovery under injected index-publication failure
* idempotency guarantees across worker retries after partial indexing failure
* any external vector database integration

## Recommended next step

The next useful slice is retry and recovery coverage:

1. add a controlled fault-injection seam around index publication
2. prove worker retry recovery in Docker without duplicate persisted vectors or index entries

Follow-on planning for Docker image and Compose hardening now lives in `docs/workstreams/WS-005-docker/32_docker-hardening-plan.md`.
