# WS-005 Docker Hardening Plan

**Date:** 2026-03-12  
**Status:** implemented  
**Scope of this note:** implemented Docker hardening follow-on for the current split runtime described in `docs/workstreams/WS-005-docker/31_status.md`.

## Summary

This note records the Docker hardening pass implemented on top of the initial split-runtime Docker slice.

The hardening work remained intentionally scoped to the current runtime shape:

* keep separate `db`, `migrate`, `api`, and `worker` services
* keep one shared application image
* keep `python -m parity.runtime` as the container entrypoint

This was not a runtime-topology refactor, and it does not promote any stable public FastAPI contract.

## Context

As of `2026-03-11`, `docs/workstreams/WS-005-docker/31_status.md` recorded a verified Docker-backed local runtime and a passing Docker-backed e2e suite for the internal document lifecycle.

That status note proved the current stack was real and useful. The next Docker-oriented slice was therefore not a new runtime topology. The useful follow-on was to harden the existing image, compose configuration, readiness behavior, and operator workflow so the local stack became more repeatable and more production-like without changing the repo's current architecture.

## Decision

The implemented hardening pass preserves the current split runtime.

Keep:

* `db`
* `migrate`
* `api`
* `worker`

Do not introduce in this pass:

* a single-container `alembic upgrade head && uvicorn ...` startup model
* a claim that the internal FastAPI app is now a stable public service API
* a deployment-model refactor aimed at a future public FastAPI surface

Those choices belong to a later runtime/API decision, not to the current Docker hardening slice.

## Reusable Ideas Adopted

The following ideas from the reference snippets were compatible with the current repo shape and were adopted in implementation:

* frozen lockfile-based dependency installation with `uv`
* layer ordering that copies dependency metadata before application source
* `--no-dev` installation in runtime images
* bytecode compilation and explicit `uv` cache location for container builds
* clearer Docker operator commands in `Makefile`
* Compose defaults that are closer to a durable local operator workflow

These ideas were translated into current repo terminology and layout:

* package and runtime name remains `parity`
* runtime environment variables remain `DATABASE_URL`, `PARITY_ARTIFACT_ROOT`, `PORT`, and `PARITY_WORKER_POLL_SECONDS`
* local Compose operator variables may additionally expose `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`, `PARITY_UID`, and `PARITY_GID`
* runtime commands remain `api`, `worker`, and `migrate`

## Deferred Or Rejected Ideas

The following reference ideas still wait for later work and were not applied in this hardening pass:

* replacing the shared runtime entrypoint with a single `uvicorn` command
* chaining Alembic migration execution into API startup
* switching to a single-service application model
* renaming the app around a future public FastAPI package or route layout
* treating this hardening work as a production-grade deployment architecture

Those choices still belong to a later runtime/API decision, not to the current Docker hardening slice.

## Implemented Changes

### Dockerfile

The shared runtime image was hardened without changing its command model.

Implemented changes:

* keep the official `uv` Python base-image path already used by the repo
* add container-oriented env defaults:
  * `PYTHONUNBUFFERED=1`
  * `PYTHONDONTWRITEBYTECODE=1`
  * `UV_COMPILE_BYTECODE=1`
  * `UV_CACHE_DIR=/tmp/.uv-cache`
* split dependency installation into two cache-friendly steps:
  * copy `pyproject.toml`, `uv.lock`, `README.md`, and `alembic.ini`
  * run `uv sync --frozen --no-dev --no-install-project`
  * copy `src/`
  * run `uv sync --frozen --no-dev`
* clear the uv cache after each sync step
* keep `ENTRYPOINT ["python", "-m", "parity.runtime"]`
* keep `CMD ["api"]`
* add a dedicated non-root runtime user in the image
* keep `/app` plus image-local `/artifacts` owned by that user

### docker-compose.yml

The local Compose stack was hardened while preserving the proven service graph.

Implemented changes:

* keep `db`, `migrate`, `api`, and `worker`
* keep `migrate` as a one-shot service that runs before `api` and `worker`
* add environment interpolation for local operator defaults:
  * `POSTGRES_DB`
  * `POSTGRES_USER`
  * `POSTGRES_PASSWORD`
  * `POSTGRES_PORT`
  * `PORT`
  * `PARITY_WORKER_POLL_SECONDS`
  * `PARITY_UID`
  * `PARITY_GID`
* derive service `DATABASE_URL` values from those Compose variables
* keep `PARITY_ARTIFACT_ROOT=/artifacts`
* add a named Postgres volume for database persistence
* keep the artifact bind mount for the current filesystem-backed workflow
* add `init: true`
* add restart policies for the long-lived `db`, `api`, and `worker` services
* keep `migrate` as `restart: "no"`
* run `api`, `worker`, and `migrate` with a host UID/GID override strategy so the bind-mounted `./data` path remains writable in normal local use
* add an `api` healthcheck using `/readyz`

### Readiness Behavior

The readiness semantics were tightened before `/readyz` was used as the main container health signal.

Implemented changes:

* `/readyz` now verifies database connectivity instead of only constructing runtime dependencies
* `/readyz` now verifies that `PARITY_ARTIFACT_ROOT` exists and is writable
* the filesystem artifact store gained a small write probe used by readiness checks
* `make docker-smoke` is now meaningful as a compose-path readiness check because it depends on the tighter `/readyz` behavior

### Makefile And Operator Workflow

The operator surface was expanded without changing the meaning of the existing Python-oriented targets.

Implemented changes:

* keep existing targets such as:
  * `make run`
  * `make run-api`
  * `make run-worker`
  * `make migrate`
  * `make test-e2e`
* add explicit Docker operator targets:
  * `make docker-build`
  * `make docker-up`
  * `make docker-up-build`
  * `make docker-down`
  * `make docker-ps`
  * `make docker-logs`
  * `make docker-db-shell`
  * `make docker-smoke`
* define `make docker-smoke` as a small compose-path readiness check over the existing stack rather than as a new product test layer

### E2E Diagnostics

The Docker-backed e2e harness also gained better diagnostics while this hardening slice was active.

Implemented changes:

* failed e2e tests now emit a fuller stack failure report with container state, artifact-tree detail, tracked-document diagnostics, lifecycle events, vector snapshot detail, and container logs
* `PARITY_E2E_VERBOSE=1` now enables step-by-step e2e progress logs during Docker-backed runs

### Docs

Operator-facing docs were updated to match the implemented workflow.

Implemented doc updates:

* update `docs/evergreen/runbook.md` with the hardened Docker operator commands and expectations
* keep `docs/evergreen/architecture.md` unchanged because implementation truth did not change at the topology/API-boundary level
* keep `docs/evergreen/api-contracts.md` unchanged because this work does not create a stable public API
* retain this note under `docs/workstreams/WS-005-docker/` as workstream history rather than evergreen truth

## Validation Completed

The following validation was completed against the implemented hardening slice:

* `uv run pytest tests/app/test_runtime_api.py`
* `uv run ruff check tests/e2e/conftest.py tests/e2e/test_markdown_stack_smoke.py tests/e2e/test_pdf_stack.py tests/e2e/test_real_markdown_docs.py tests/e2e/test_stack_failures.py`
* `make test-e2e`

Observed results during implementation:

* `tests/app/test_runtime_api.py`: `21 passed`
* `make test-e2e`: `8 passed`

Manual compose-path verification target:

* `make docker-up-build`
* `make docker-ps`
* `make docker-smoke`
* confirm the container runtime user is non-root
* confirm the local bind-mounted artifact root remains writable under the configured UID/GID override strategy

Notes on broader validation:

* repo-wide `make fmt-check`, `make lint`, and `make type` were not good acceptance gates for this slice because the repo already had unrelated baseline failures outside the Docker hardening changes

The implemented result preserves the current e2e proof surface while improving repeatability, readiness truthfulness, failure visibility, and operator ergonomics.

## Assumptions

This implementation assumes:

* no stable public API change is intended in this pass
* no deployment-model refactor is intended in this pass
* the shared runtime entrypoint remains the correct seam for `api`, `worker`, and `migrate`
* the Docker work remains local-runtime hardening, not a claim of production-grade deployment completion
