# WS-005 Docker Hardening Plan

**Date:** 2026-03-12  
**Status:** proposed  
**Scope of this note:** follow-on Docker hardening plan for the current split runtime described in `docs/workstreams/WS-005-docker/31_status.md`.

## Summary

This note records a productionizing and container-hardening follow-on for the Docker layer that now exists in the repo.

The plan is intentionally scoped to the current runtime shape:

* keep separate `db`, `migrate`, `api`, and `worker` services
* keep one shared application image
* keep `python -m parity.runtime` as the container entrypoint

This is not a plan to collapse the runtime into a single web container, and it does not promote any stable public FastAPI contract.

## Context

As of `2026-03-11`, `docs/workstreams/WS-005-docker/31_status.md` records a verified Docker-backed local runtime and a passing Docker-backed e2e suite for the internal document lifecycle.

That status note proves the current stack is real and useful. The next Docker-oriented work is not a new runtime topology. The next useful slice is to harden the existing image, compose configuration, and operator workflow so the local stack is more repeatable and more production-like without changing the repo's current architecture.

## Decision

The hardening pass should preserve the current split runtime.

Keep:

* `db`
* `migrate`
* `api`
* `worker`

Do not introduce in this pass:

* a single-container `alembic upgrade head && uvicorn ...` startup model
* a claim that the internal FastAPI app is now a stable public service API
* a deployment-model refactor aimed at a future public FastAPI surface

## Reusable Ideas To Adopt

The following ideas from the reference snippets are compatible with the current repo shape and are worth adopting now:

* frozen lockfile-based dependency installation with `uv`
* layer ordering that copies dependency metadata before application source
* `--no-dev` installation in runtime images
* bytecode compilation and explicit `uv` cache location for container builds
* clearer Docker operator commands in `Makefile`
* Compose defaults that are closer to a durable local operator workflow

These ideas should be translated into current repo terminology and layout:

* package and runtime name remains `parity`
* environment variables remain `DATABASE_URL`, `PARITY_ARTIFACT_ROOT`, and `PORT`
* runtime commands remain `api`, `worker`, and `migrate`

## Deferred Or Rejected Ideas

The following reference ideas should wait for later work and should not be applied in this hardening pass:

* replacing the shared runtime entrypoint with a single `uvicorn` command
* chaining Alembic migration execution into API startup
* switching to a single-service application model
* renaming the app around a future public FastAPI package or route layout
* treating this hardening work as a production-grade deployment architecture

Those choices belong to a later runtime/API decision, not to the current Docker hardening slice.

## Implementation Plan

### Dockerfile

Update the image build to harden the current shared runtime image without changing its command model.

Planned changes:

* keep the official `uv` Python base-image path already used by the repo
* add container-oriented env defaults such as:
  * `PYTHONUNBUFFERED=1`
  * `PYTHONDONTWRITEBYTECODE=1`
  * `UV_COMPILE_BYTECODE=1`
  * `UV_CACHE_DIR=/tmp/.uv-cache`
* split dependency installation into two stages within the Docker layer order:
  * copy `pyproject.toml`, `uv.lock`, `README.md`, and `alembic.ini`
  * run `uv sync --frozen --no-dev --no-install-project`
  * copy `src/`
  * run `uv sync --frozen --no-dev`
* keep `ENTRYPOINT ["python", "-m", "parity.runtime"]`
* keep `CMD ["api"]`
* add a dedicated non-root runtime user and ensure `/app` and `/artifacts` are usable by that user

### docker-compose.yml

Harden the local Compose stack while preserving the proven service graph.

Planned changes:

* keep `db`, `migrate`, `api`, and `worker`
* keep `migrate` as a one-shot service that runs before `api` and `worker`
* add environment interpolation for local operator defaults such as:
  * `POSTGRES_DB`
  * `POSTGRES_USER`
  * `POSTGRES_PASSWORD`
  * `PORT`
* derive service `DATABASE_URL` values from those Compose variables
* keep `PARITY_ARTIFACT_ROOT=/artifacts`
* add a named Postgres volume for database persistence
* keep the artifact bind mount for the current filesystem-backed workflow
* add `init: true` and sensible restart policy for long-lived services
* add an `api` healthcheck using `/readyz`
* keep `migrate` as `restart: "no"`

### Makefile And Operator Workflow

Expand the operator surface without changing the meaning of existing Python-oriented targets.

Planned changes:

* keep existing targets such as:
  * `make run`
  * `make run-api`
  * `make run-worker`
  * `make migrate`
  * `make test-e2e`
* add explicit Docker operator targets such as:
  * `make docker-build`
  * `make docker-up`
  * `make docker-up-build`
  * `make docker-down`
  * `make docker-ps`
  * `make docker-logs`
  * `make docker-db-shell`
  * `make docker-smoke`
* define `make docker-smoke` as a small compose-path readiness check over the existing stack rather than as a new product test layer

### Docs

Update the operator-facing docs to match the hardened Docker workflow once implemented.

Planned doc updates:

* update `docs/evergreen/runbook.md` with the hardened Docker operator commands and expectations
* keep `docs/evergreen/architecture.md` unchanged unless implementation truth actually changes
* keep `docs/evergreen/api-contracts.md` unchanged because this work does not create a stable public API
* retain this note under `docs/workstreams/WS-005-docker/` as planning/proposal material rather than evergreen truth

## Validation Plan

Recommended validation for the eventual implementation:

* `make fmt-check`
* `make lint`
* `make type`
* `make test`
* `make test-e2e`

Manual compose-path checks:

* `make docker-up-build`
* `make docker-ps`
* `curl http://127.0.0.1:8000/readyz`
* confirm the container runtime user is non-root

The acceptance goal is that the hardened image and Compose stack preserve the current e2e proof surface while improving repeatability and operator ergonomics.

## Assumptions

This proposal assumes:

* no stable public API change is intended in this pass
* no deployment-model refactor is intended in this pass
* the shared runtime entrypoint remains the correct seam for `api`, `worker`, and `migrate`
* the Docker work remains local-runtime hardening, not a claim of production-grade deployment completion
