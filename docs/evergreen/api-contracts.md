# API Contracts

**Status:** Verified
**Last verified:** 2026-03-21

## Purpose
This document defines the stable external interfaces that are actually implemented and safe for downstream reliance.

## Current State
As of 2026-03-21, `doc_forge` has one stable public interface family:

- a localhost HTTP service API served by FastAPI
- an optional OpenAPI description for the mounted app surface when Swagger exposure is enabled
- an optional Swagger UI for local inspection of that mounted app surface when Swagger exposure is enabled

The stable contract is the local service started by `uv run poe run-api`, not the internal Python package layout under `src/doc_forge/`.

## Scope
### In Scope
- the stable localhost HTTP routes exposed by the FastAPI app
- the optional OpenAPI schema and Swagger UI exposed by that runtime when enabled
- the boundary between stable public routes, runtime-exposed internal routes, and changeable internal modules

### Out Of Scope
- internal module boundaries
- direct imports from `src/doc_forge/`
- workstream proposals and delivery drafts
- implementation details behind the service routes

## Stable Interfaces
### Stable Public HTTP Routes
When started via `uv run poe run-api`, the stable local service base URL is:

- `http://127.0.0.1:8000`
- `http://localhost:8000`

The stable localhost route set is:

- `GET /healthz`
- `GET /readyz`
- `POST /documents`
- `DELETE /documents/{doc_id}`
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
- `query_id` path values use the same non-empty, trimmed, no-separator, no-dot-segment validation rules as other stable identifiers.

These routes are stable at the HTTP boundary: path, method, request shape, response shape, and documented status codes should not change incompatibly without first updating this file.

Runtime exposure alone does not make a route part of the stable public contract; only the routes enumerated in this section carry compatibility guarantees.

### Optional Runtime Schema And Docs
When `DOC_FORGE_ENABLE_SWAGGER=true`, the FastAPI runtime also exposes:

- `GET /openapi.json`, which describes the currently mounted app surface
- `GET /docs`, which serves the Swagger UI for that same mounted app surface

`DOC_FORGE_ENVIRONMENT=dev` alone does not enable these endpoints. They are available only when the existing Swagger exposure toggle is enabled.

Because the mounted app currently includes both stable public routes and internal-only routes, the live OpenAPI description is useful runtime documentation but is not, by itself, the definition of the stable public contract.

### Runtime-Exposed But Non-Public Routes
The following HTTP routes are implemented and callable in the mounted app, but they are not part of the stable public contract:

- `POST /retrieval/query`, which remains a retrieval smoke/debug endpoint
- `POST /internal/run-next-job`, which remains an internal operator/test endpoint

These routes may change without the compatibility guarantees that apply to the stable public route list above.

## Other Implemented But Not Public
The following are implemented but are not part of the stable public contract:

- direct imports from `src/doc_forge/query/`, `src/doc_forge/readmodels/`, `src/doc_forge/lifecycle/`, and other package internals
- persistence artifacts such as `query_runs`, `query_snapshots`, and `query_stage_traces`

## Compatibility And Change Control
Because the localhost FastAPI service API is stable:

- incompatible changes to the stable route set require updating this file first
- OpenAPI-visible request or response shape changes for stable routes are contract changes
- runtime exposure in `/openapi.json` does not promote an internal route into the stable public contract
- internal Python modules remain changeable unless they are explicitly promoted here later
- package-level imports are still not downstream-supported interfaces


## Relationship To Other Docs
- [`docs/evergreen/architecture.md`](./architecture.md) describes current repo shape and internal seams behind the service.
- [`docs/evergreen/runbook.md`](./runbook.md) describes how to start and operate the local runtime.
- [`docs/evergreen/mvp.md`](./mvp.md) describes the target product, not the service contract by itself.
- `docs/delivery/` and `docs/workstreams/` may describe future changes, but they do not override this contract.
