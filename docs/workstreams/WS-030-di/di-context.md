# DI Review Context for External Reviewers

## Purpose

This file is a repo-specific context pack for reviewing
[`di-principles-v2.md`](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-030-di/di-principles-v2.md)
without full repository access.

Its goal is not to restate generic dependency-injection theory. Its goal is to
provide the minimum repo truth needed so an external reviewer can judge the DI
guidance against the real `doc_forge` architecture, current implementation
shape, recent WS-030 changes, and known remaining gaps.

## Authority and Scope

Use the docs with the following authority order:

- [`docs/evergreen/architecture.md`](/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md)
  is canonical for current implementation truth.
- [`docs/evergreen/api-contracts.md`](/Users/val/projects/rag/sem-rag/docs/evergreen/api-contracts.md)
  is canonical for stable external interfaces.
- [`docs/workstreams/WS-030-di/`](/Users/val/projects/rag/sem-rag/docs/workstreams/WS-030-di/)
  contains design and review material for this workstream. It is not canonical
  runtime truth.

This context pack is a snapshot for review. It is not a source of public API
guarantees.

## Repo Architecture Snapshot

`doc_forge` is currently a single-service local runtime built around FastAPI.

At a high level, the current runtime is:

- one FastAPI HTTP application
- one primary relational metadata store
- filesystem-backed artifact storage for raw, extracted, and normalized files
- one internal query domain growing inside the same service boundary as the
  document lifecycle

The main bounded contexts called out by evergreen architecture are:

- document lifecycle
- query runtime
- query-facing read model
- persistence
- artifacts
- evaluation

The stable public interface is HTTP only. There is no stable public Python
package API. Internal Python seams are allowed to change unless they are
explicitly promoted into evergreen API contracts.

For DI review purposes, this means an external reviewer should not assume
package layout or internal object seams are public commitments.

## Stable vs Internal HTTP Boundary

For this repo, the stable contract is the local HTTP service started by
`uv run poe run-api`, not the internal Python package structure.

The evergreen API contract treats the main document and query-facing HTTP routes
as the stable local interface. It also explicitly calls out two implemented
routes that are **not** part of the stable external contract:

- `POST /retrieval/query`, which is kept as a local retrieval smoke and debug
  route
- `POST /internal/run-next-job`, which is kept as an internal operator and test
  route

This matters for DI review. External reviewers should optimize for boundary
clarity and stable HTTP behavior, not for freezing internal Python shapes.

## DI-Relevant Current Code Shape

The current dependency-injection shape is uneven but intentional.

The relevant current structure is:

- FastAPI `Depends(...)` usage is concentrated in
  [`src/doc_forge/app/deps.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/app/deps.py)
  and router modules.
- Plain runtime object construction lives in
  [`src/doc_forge/app/factories.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/app/factories.py).
- The documents path now has a transport-neutral
  [`DocumentsFacade`](/Users/val/projects/rag/sem-rag/src/doc_forge/lifecycle/documents.py)
  under `src/doc_forge/lifecycle/`.
- Document HTTP exception mapping now lives in
  [`src/doc_forge/app/documents_http.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/app/documents_http.py)
  and is used by
  [`src/doc_forge/app/routers/documents.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/app/routers/documents.py).
- Documents are the only route family that currently follows this
  facade-plus-edge-mapping pattern.
- Query, internal retrieval, and system paths still use HTTP-aware app services
  under
  [`src/doc_forge/app/services/`](/Users/val/projects/rag/sem-rag/src/doc_forge/app/services/).

The asymmetry matters. An external reviewer should not assume the whole repo has
already been normalized to the same DI boundary style.

## Working Terms in This Repo

Use these terms in the repo-specific sense below when reviewing
`di-principles-v2.md`:

- **Adapter:** code that translates between an external interface and internal
  behavior. In this repo, FastAPI routers, request parsing, response shaping,
  and HTTP exception mapping are adapter concerns.
- **Web edge:** the FastAPI boundary where `Depends(...)`, HTTP DTOs, status
  codes, and transport logging belong.
- **Facade:** a transport-neutral orchestration surface that presents a small
  callable API over lower-level workflow services without taking on HTTP
  concerns. In WS-030, `DocumentsFacade` is the example.
- **Application service:** a reusable service that coordinates business flow or
  policy and is intended to stay usable outside one transport. In practice, this
  should not import FastAPI if it is meant to be reused.
- **HTTP-aware app service:** an existing repo pattern under `src/doc_forge/app/`
  where a module is called a service but still raises `HTTPException` or shapes
  HTTP behavior. These modules are real current-state code, but they should be
  reviewed as adapter-leaning, not transport-neutral by default.
- **Composition root:** the place where concrete implementations are assembled
  and wired together for one executable entrypoint. In this repo, that concept
  is split across HTTP and worker startup paths rather than forced into one
  literal file.

These terms are descriptive aids for review. They do not imply the current repo
has perfectly clean package-level separation everywhere.

## Executable Entrypoints and Composition Nuance

The repo should be read as having separate executable entrypoints, not one
literal runtime shell for every responsibility:

- `uv run poe run-api` composes and starts the FastAPI HTTP application
- `uv run poe run-worker` composes and starts the queue-draining worker loop

Because of that, DI guidance about “one composition root” should be interpreted
in repo-specific terms as **one clear composition root per executable
entrypoint**, not one universal file for every runtime path.

## What Changed in WS-030 So Far

The main WS-030 change already landed only on the documents path.

Recent decisions already reflected in code:

- the documents route family was refactored from an HTTP-shaped app service to a
  transport-neutral facade plus router-edge HTTP mapping
- document route logging now lives at the HTTP router boundary
- document error mapping is centralized in a small helper instead of introducing
  a generic `AppError` hierarchy
- focused tests were added for:
  - facade delegation
  - transport-neutral detail mapping
  - helper exception mapping
  - router contract and router logging behavior
- internal, query, and system adapters were intentionally not refactored in the
  same pass

This is the most important context for reviewing
`di-principles-v2.md`: the repo has a real DI pilot, but not a repo-wide
conversion.

## Evidence Already Landed

The documents-boundary refactor is not just design intent. It is implemented and
backed by focused tests.

Evidence currently present in the repo includes:

- facade and exception-mapping seam tests in
  [`tests/app/test_documents_boundary.py`](/Users/val/projects/rag/sem-rag/tests/app/test_documents_boundary.py)
- direct documents route contract tests in
  [`tests/app/test_documents_api.py`](/Users/val/projects/rag/sem-rag/tests/app/test_documents_api.py)
- ASGI/runtime logging and route behavior tests in
  [`tests/app/test_runtime_api.py`](/Users/val/projects/rag/sem-rag/tests/app/test_runtime_api.py)

This gives external reviewers a useful calibration point: the documents path is
the current DI pilot, and other route families should be compared against it
rather than assumed to already match it.

## Known Open Gaps

The main remaining DI-related gaps are concrete and current:

- [`src/doc_forge/app/services/queries.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/app/services/queries.py)
  still imports FastAPI and raises `HTTPException`.
- [`src/doc_forge/app/services/internal.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/app/services/internal.py)
  still imports FastAPI and raises `HTTPException`.
- [`src/doc_forge/app/services/system.py`](/Users/val/projects/rag/sem-rag/src/doc_forge/app/services/system.py)
  still imports FastAPI and raises `HTTPException`.
- The repo does not use a literal single composition root for every executable.
  HTTP app composition and worker/runtime composition are separate.
- Cached factories are used for app-scoped objects that do not need explicit
  startup or shutdown work. FastAPI lifespan is not broadly used yet.

These are known review pressure points. A useful DI review should engage with
them directly instead of giving generic framework advice.

## Review Lens for `di-principles-v2.md`

When reviewing `di-principles-v2.md`, apply this lens:

- Treat it as a target-state design standard or evaluation rubric, not as a
  claim that every current module already conforms.
- Prefer repo-specific judgment over generic framework purity.
- Do not treat internal Python seams as stable public API.
- Separate “good target principle” from “current repo truth.”
- Flag wording that sounds prescriptive in ways that conflict with the repo’s
  current topology or earned seams.
- Focus on whether the principles help make decisions in this repo, especially
  for:
  - mixed-purpose modules
  - HTTP translation boundaries
  - facade versus adapter splits
  - cached factories versus lifespan usage
  - per-entrypoint composition

## Questions the Reviewer Should Answer

Please answer these questions when reviewing `di-principles-v2.md`:

1. Which principles are durable and useful for this repo as written?
2. Where does `di-principles-v2.md` overstate current repo conformance?
3. Which sections should be reframed as target-state guidance rather than
   present-state description?
4. Does the “one composition root” principle need per-entrypoint wording for
   this repo?
5. Does the recommended layering section need to be explicitly framed as
   illustrative rather than literal package guidance?
6. What minimal additional repo context, if any, would produce a more valuable
   review?

## Distinctions To Preserve

Please keep these distinctions sharp in the review:

- **Canonical truth:** evergreen docs
- **Current internal implementation:** code and tests in the repo today
- **WS-030 design intent:** how future DI cleanup should be judged and shaped

The purpose of this context pack is to improve external review quality, not to
onboard a new contributor to the full product.
