# ADR-0002: Documents Boundary Separation

- Status: accepted
- Date: 2026-03-21

## Context

The documents route family originally depended on an HTTP-shaped service that
mixed several responsibilities:

- document workflow calls into the lifecycle layer
- translation of lifecycle/domain exceptions into `HTTPException`
- shaping of HTTP response DTOs
- route-oriented structured logging including `http_status`

That shape worked for an MVP, but it made the reusable document path harder to
separate from FastAPI concerns. It also made the term "service" ambiguous:
although the module coordinated document operations, it still chose HTTP status
codes, raised `HTTPException`, and emitted transport-specific log fields.

WS-030 clarified two repo-specific pressures:

1. Documents are the most likely route family to need reuse outside a single
   HTTP caller in the future.
2. The stable contract for this repo is the HTTP boundary documented in
   `docs/evergreen/api-contracts.md`, not the internal Python package shape.

Given those pressures, the documents path needed a cleaner separation between
transport-neutral document operations and the FastAPI adapter layer.

In this repo, the relevant "internal shapes" are mostly lifecycle and
persistence-facing types, not public-facing contracts. `DocumentLifecycleService`
is assembled from repositories, artifact storage, vector-store access,
lifecycle-event access, jobs, and orchestration collaborators. Its callable
surface also includes lifecycle result models and lower-level access such as
`require_document(...) -> PersistedDocument`. The coupling concern was not that
these types are inherently wrong. The concern was that the web adapter should
not depend directly on `require_document()` or on persistence-shaped document
records.

## Decision

We separate the documents path into three explicit responsibilities:

1. `DocumentLifecycleService` remains the workflow engine.
   It owns document lifecycle behavior, persistence coordination, retry rules,
   and lifecycle semantics.

2. `DocumentsFacade` provides a small transport-neutral caller surface over the
   lifecycle service.
   It exposes document operations needed by callers:
   - upload
   - delete
   - get detail
   - get status
   - get artifact refs
   - retry

   The facade may adapt internal lifecycle or persistence-shaped data into
   transport-neutral result models, such as `DocumentDetailResult`, but it does
   not choose HTTP status codes or raise `HTTPException`.

3. The FastAPI router owns HTTP adapter concerns.
   This includes:
   - request parsing
   - response DTO shaping
   - mapping document exceptions to HTTP semantics
   - route-level structured logging that includes transport metadata such as
     `http_status`

A small helper module,
`src/doc_forge/app/documents_http.py`, centralizes document-exception to HTTP
mapping for the router layer. We deliberately do not introduce a generic
cross-repo `AppError` hierarchy as part of this decision.

## Why This Shape

This separation is intentional for the following reasons:

- The lifecycle service is a workflow engine, not the preferred direct API for
  web callers.
- The router is already the FastAPI adapter, so HTTP translation belongs there
  rather than inside a supposedly reusable service.
- A facade gives callers a narrower and cleaner document-oriented surface
  without forcing them to know lifecycle internals such as `require_document()`
  or persistence-shaped records.
- If another transport is added later, the reusable seam is the
  facade-plus-lifecycle path, not the router.

## Current Callers

The current repo shape after WS-030 is:

- documents HTTP routes call `DocumentsFacade`, not `DocumentLifecycleService`
  directly
- `DocumentsFacade` is the main production caller that still uses
  `require_document(...)` in order to adapt a persisted document into
  `DocumentDetailResult`
- the internal retrieval smoke path still calls `DocumentLifecycleService`
  directly for `query_document(...)`
- the worker path is separate and does not use `DocumentLifecycleService` as a
  web-facing seam
- tests still call `DocumentLifecycleService` directly where the purpose is to
  verify lifecycle rules

The facade exists to prevent the documents router from depending on lower-level
lifecycle internals while still allowing direct lifecycle use where that is
already an internal and acceptable seam.

## Consequences

- Positive: The reusable document path no longer depends on FastAPI types or
  HTTP semantics.
- Positive: HTTP translation is explicit at the web edge, which aligns with the
  repo's DI guidance and makes route behavior easier to test.
- Positive: The router now depends on a smaller document-specific surface
  instead of coupling directly to the broader lifecycle engine.
- Positive: The documents path becomes a concrete pilot for future boundary
  cleanup in other route families.
- Negative/Tradeoff: Some code that previously lived in a service now lives in
  the router layer, so routers are somewhat less thin than before.
- Negative/Tradeoff: `DocumentsFacade` is currently a narrow wrapper over the
  lifecycle service, so it adds one more layer that must justify itself through
  reuse and clearer boundaries.
- Negative/Tradeoff: This decision is intentionally local to documents for now;
  query, internal, and system paths still contain HTTP-aware services and are
  therefore asymmetric with the documents path.

## Alternatives Considered

### Keep the original HTTP-shaped service

Rejected because it preserved mixed responsibilities and kept FastAPI semantics
inside a layer that should be reusable if documents gain another caller.

### Call `DocumentLifecycleService` directly from the router

Rejected because it would couple the router to lower-level lifecycle internals
and internal data shapes more tightly than needed. The facade provides a smaller
document-oriented seam and a place for transport-neutral result adaptation.

### Introduce a generic application error hierarchy

Rejected for now because the repo does not yet need a stable cross-transport
error contract. Existing document exceptions can be mapped at the edge without
adding a broader abstraction.

## Related Workstreams

- `docs/workstreams/WS-030-di/`
