# WS-029 DI Alignment Note

**Status:** Draft
**Applies to:** WS-029 end state
**Last updated:** 2026-03-21

## Purpose

Capture the final dependency-injection and dependency-inversion assessment for WS-029 after
the A+ refactor landed, so the tradeoffs remain easy to revisit later.

This note is an assessment artifact. It does not change the implementation plan.

## Reference

This assessment is evaluated against:

- `docs/workstreams/WS-030-di/di-principles.md`
- `docs/workstreams/WS-029-deps/WS-029-framing.md`
- `docs/workstreams/WS-029-deps/WS-029-design.md`
- `docs/workstreams/WS-029-deps/WS-029-plan.md`

## What WS-029 improved

WS-029 materially improved DI boundary hygiene in the repo:

- FastAPI wiring is concentrated in `src/doc_forge/app/deps.py`
- plain construction logic now exists in `src/doc_forge/app/factories.py`
- `src/doc_forge/lifecycle/worker.py` now constructs its runtime worker through plain factories
  rather than importing private builders from `app.deps`
- the internal HTTP routes no longer share one combined app service that forces both
  `DocumentLifecycleService` and `DocumentLifecycleWorker` to be built for both routes

Against the DI principles, those are meaningful gains:

- FastAPI is more clearly kept at the edge
- constructor injection is more explicit below the HTTP boundary
- provider override seams remain available for tests

## End-state assessment

The final state is **substantially better aligned** with `di-principles.md`, but it is not a
complete ports-and-adapters inversion design.

### Where the alignment is strong

1. **FastAPI DI mostly stays at the edge.**

   `Depends(...)` is now concentrated in `src/doc_forge/app/deps.py` and the router layer.
   The worker runtime no longer imports FastAPI-shaped providers for construction.

2. **Constructor injection below the boundary is improved.**

   `src/doc_forge/app/factories.py` builds runtime graphs with plain Python arguments:
   `Engine`, `FilesystemArtifactStore`, and `EmbeddingAdapter`.

3. **The internal HTTP boundary is more honest.**

   `src/doc_forge/app/services/internal.py` now has two route-specific services:
   `InternalRetrievalAppService` and `InternalWorkerAppService`.

4. **The current test strategy still fits.**

   FastAPI providers remain present in `src/doc_forge/app/deps.py`, so test overrides still
   target provider seams rather than mutating business code directly.

## Remaining gaps

### 1. App services still carry transport concerns

This is the main remaining DI-alignment gap.

`src/doc_forge/app/services/internal.py` imports `HTTPException` and `status`, and
`InternalRetrievalAppService.retrieval_query()` raises an HTTP exception directly.

Implication:

- the app-service layer still knows about FastAPI transport semantics
- the boundary is cleaner than before, but FastAPI is not fully confined to the adapter layer

If the team wants strict alignment with the DI principles, HTTP exception translation should
move outward into a thinner HTTP adapter boundary, and app services should instead return
app-level results or raise app-level exceptions.

### 2. High-level policy still depends on concrete implementations

WS-029 did not introduce ports or protocols for lifecycle/query collaborators.

Examples:

- `InternalRetrievalAppService` depends on concrete `DocumentLifecycleService`
- `InternalWorkerAppService` depends on concrete `DocumentLifecycleWorker`
- `app/factories.py` binds concrete repositories, stores, and stage runners directly

Implication:

- the result is improved FastAPI-boundary discipline
- it is not a full dependency-inversion architecture in the “contracts in the core” sense

This is acceptable for WS-029 because broader inversion was explicitly out of scope.

### 3. Composition-root interpretation remains contextual

The DI principles say there should be one composition root.

The current repo effectively has:

- `src/doc_forge/app/deps.py` as the HTTP composition root
- `src/doc_forge/lifecycle/worker.py:main()` plus `app/factories.py` as the worker-process
  construction root

That is reasonable if “one composition root” is interpreted per executable entrypoint.
It is not a literal single construction root for the whole repo.

## Conclusion

WS-029 should be considered a success on its stated scope.

It achieved:

- removal of the misleading dual-use worker construction path
- cleaner separation between plain construction and FastAPI dependency wiring
- more honest route-level dependency graphs

It did **not** achieve:

- removal of all FastAPI concerns from app services
- full dependency inversion through ports/protocols
- a single literal construction root for every executable path in the repo

The right interpretation is:

**WS-029 earned better DI boundary hygiene, not a full inversion architecture.**

## Follow-up options

If future work wants closer alignment with `di-principles.md`, the next candidates are:

1. Move HTTP exception translation out of `app/services/*` and into a thinner HTTP adapter layer.
2. Introduce explicit ports/protocols only where multiple concrete implementations or testing
   pressure justify them.
3. Revisit whether app-service boundaries should become framework-agnostic use cases rather than
   HTTP-aware orchestration services.
