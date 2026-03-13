# API Contracts

**Status:** Verified
**Last verified:** 2026-03-12

## Purpose
This document defines the stable external interfaces that are actually implemented and safe for downstream reliance.

## Current State
As of 2026-03-12, `doc_forge` has one stable public interface family:

- a localhost HTTP service API served by FastAPI
- a live OpenAPI description for that service
- a Swagger UI for local inspection of the OpenAPI surface

The stable contract is the local service started by `uv run poe run-api`, not the internal Python package layout under `src/doc_forge/`.

## Scope
### In Scope
- the stable localhost HTTP routes exposed by the FastAPI app
- the OpenAPI schema served by that runtime
- the boundary between stable local service routes and changeable internal modules

### Out Of Scope
- internal module boundaries
- direct imports from `src/doc_forge/`
- workstream proposals and delivery drafts
- implementation details behind the service routes

## Stable Interfaces
### Stable Local HTTP Service API
When started via `uv run poe run-api`, the stable local service base URL is:

- `http://127.0.0.1:8000`
- `http://localhost:8000`

The stable localhost route set is:

- `GET /healthz`
- `GET /readyz`
- `POST /documents`
- `GET /documents/{doc_id}`
- `GET /documents/{doc_id}/status`
- `GET /documents/{doc_id}/artifacts`
- `POST /documents/{doc_id}/retry`
- `POST /queries`
- `GET /queries/{query_id}`
- `GET /queries/{query_id}/trace`
- `GET /queries/{query_id}/citations`

Stable identifier validation at this boundary is:

- `workspace_id` inputs must be non-empty, must not have leading or trailing whitespace, and must not contain `/`, `\\`, `.`, or `..` path-segment forms.
- `doc_id` values remain string-backed and field names are unchanged; generated values such as `doc_<hex>` remain valid.

These routes are stable at the HTTP boundary: path, method, request shape, response shape, and documented status codes should not change incompatibly without first updating this file.

### Stable OpenAPI Description
The FastAPI runtime is the source of truth for the live service schema:

- `GET /openapi.json` exposes the stable OpenAPI description
- `GET /docs` exposes the Swagger UI for the same contract

`uv run poe run-api` exports `DOC_FORGE_ENVIRONMENT=dev` (via the Makefile's old env or explicit `.env` usage in poe/uv depending on setup), so the local Swagger UI is available by default on localhost. In non-dev environments, `/docs` and `/openapi.json` remain controlled by the existing Swagger toggle rules.

## Implemented But Not Public
The following are implemented but are not part of the stable public contract:

- `POST /retrieval/query`, which remains a retrieval smoke/debug endpoint
- `POST /internal/run-next-job`, which remains an internal operator/test endpoint
- direct imports from `src/doc_forge/query/`, `src/doc_forge/readmodels/`, `src/doc_forge/lifecycle/`, and other package internals
- persistence artifacts such as `query_runs`, `query_snapshots`, and `query_stage_traces`

## Compatibility And Change Control
Because the localhost FastAPI service API is stable:

- incompatible changes to the stable route set require updating this file first
- OpenAPI-visible request or response shape changes for stable routes are contract changes
- internal Python modules remain changeable unless they are explicitly promoted here later
- package-level imports are still not downstream-supported interfaces

## Promotion Rule
An interface should appear in this file only when all of the following are true:

- it exists in the codebase
- its behavior is exercised by tests or equivalent validation
- the team intends downstream callers to rely on it
- the team is willing to treat incompatible changes as breaking changes

## Relationship To Other Docs
- [`docs/evergreen/architecture.md`](./architecture.md) describes current repo shape and internal seams behind the service.
- [`docs/evergreen/runbook.md`](./runbook.md) describes how to start and operate the local runtime.
- [`docs/evergreen/mvp.md`](./mvp.md) describes the target product, not the service contract by itself.
- `docs/delivery/` and `docs/workstreams/` may describe future changes, but they do not override this contract.
