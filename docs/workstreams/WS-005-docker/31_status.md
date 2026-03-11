# WS-005 Status

**Date:** 2026-03-11  
**Scope of this note:** status after implementing the initial Docker runtime and Docker-backed e2e suite for the internal document lifecycle.

## What was completed

The repo now has a working Docker path for the internal lifecycle runtime plus a real containerized e2e suite.

Completed changes:

* added a shared runtime entrypoint:
  * `src/parity/runtime.py`
* added Docker runtime assets:
  * `Dockerfile`
  * `.dockerignore`
  * `docker-compose.yml`
* added a Docker-backed pytest layer:
  * `tests/e2e/conftest.py`
  * `tests/e2e/test_markdown_stack_smoke.py`
  * `tests/e2e/test_real_markdown_docs.py`
  * `tests/e2e/test_stack_failures.py`
* added repo wiring for the e2e suite:
  * `pyproject.toml` marker `e2e`
  * default pytest exclusion for `e2e`
  * `make test-e2e`
* updated operating docs:
  * `docs/evergreen/runbook.md`

## What the Docker e2e suite now proves

The active Docker e2e suite validates all of the following against real containers:

* Markdown upload reaches `READY`
* the API and worker run as separate processes
* Alembic migrations execute before the stack serves requests
* real repo Markdown documents can be uploaded and indexed
* persisted artifact files exist for raw, extracted, and normalized stages
* Postgres contains persisted `chunks`, `chunk_embeddings`, and `index_entries`
* embedding payloads are non-empty JSON vectors with a stored embedding model
* retrieval stays document-scoped across multiple uploaded Markdown docs
* persisted chunks retain heading-path plus coarse provenance fields
* explicit unsupported PNG upload is rejected over the real HTTP stack

## Real Markdown docs used in the suite

The Docker e2e suite currently uploads and validates these repo docs:

* `docs/workstreams/WS-004-document-lifecycle/21-design-exploration.md`
* `docs/workstreams/WS-004-document-lifecycle/22-staged.md`
* `docs/evergreen/mvp.md`

The suite also keeps one small synthetic Markdown smoke fixture for quick feedback:

* `tests/e2e/fixtures/smoke.md`

## Validation completed

The following checks were run successfully during implementation:

* `uv run pytest tests/e2e --collect-only -m e2e -o addopts=-q`
* `uv run pytest tests/e2e -m e2e -o addopts=-q`

Observed result after the latest additions:

* `6 passed in 42.02s`

Manual runtime verification was also completed:

* `docker compose up --build`
* `docker compose ps`
* `GET /readyz` returned `200 {"status":"ok"}`

## What was intentionally not implemented

The following were deliberately left out of this Docker slice:

* PDF `READY` e2e coverage
* malformed PDF failure-path e2e coverage
* retry recovery under injected index-publication failure
* new HTTP inspection routes just for e2e
* a separate external vector database

## Why those items were deferred

This workstream was scoped to deliver the first practical Docker path with the least additional runtime surface:

* Markdown is the strongest current input path
* the existing Postgres-backed indexing seam is sufficient for explicit vector persistence checks
* retry/fault-injection e2e needs a clearer, intentional failure seam to avoid brittle container-only hacks

## Current repo state relevant to the next agent

Important current facts:

* the Docker e2e suite is additive and excluded from default pytest runs
* the active vector persistence proof uses existing Postgres tables:
  * `chunks`
  * `chunk_embeddings`
  * `index_entries`
* Docker Desktop socket auto-detection was needed locally because the daemon socket is under `~/.docker/run/docker.sock` rather than `/var/run/docker.sock`

## Recommended next step

If this workstream continues, pick one of these next slices:

1. PDF-focused Docker e2e:
   upload a supported PDF fixture, assert `READY`, and validate page-oriented provenance fields.
2. Retry/failure Docker e2e:
   add a controlled fault-injection seam for index publication and prove retry recovery without duplicate persisted vectors/index entries.
