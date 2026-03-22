# Dependency Injection Principles (v2)

## Purpose

These principles define how dependency inversion and dependency injection
should be judged and shaped in this codebase.

They are the preferred target direction for new boundaries and future refactors,
not a claim that every current module already conforms today. Current repo
conformance is partial and uneven. Canonical current-state truth remains in
[`docs/evergreen/architecture.md`](/Users/val/projects/rag/sem-rag/docs/evergreen/architecture.md),
not in this workstream document.

The documents path is the current pilot for this style. Query, internal, and
system paths do not fully conform yet.

- **Dependency inversion** means core business code depends on contracts, not frameworks, ORMs, or transport details.
- **Dependency injection** means concrete implementations are assembled at the boundary and passed inward.

For FastAPI, the stable rule is:

> **FastAPI is an adapter, not the architecture.**

FastAPI provides the mechanics for dependency resolution at the HTTP boundary. The architectural boundaries still have to be chosen and enforced by the codebase.

---

## Scope

These principles apply to:

- domain entities and business rules
- reusable application services and use cases
- infrastructure adapters
- web adapters and dependency providers
- test composition and provider overrides

These principles do **not** require every module named `service` to be
framework-agnostic. They **do** require each module’s layer intent to be
explicit.

---

## Layer intent must be explicit

A module is **reusable application code** if it:

- can be called from HTTP, CLI, jobs, or tests
- expresses business flow or policy
- should not choose HTTP status codes or transport responses

A module is **web adapter code** if it:

- depends on FastAPI types or provider mechanics
- shapes HTTP request or response DTOs
- translates internal errors into HTTP responses
- owns transport concerns such as status codes, headers, cookies, or request metadata

Do not leave mixed-purpose modules ambiguous.

- If code is adapter code, name and place it accordingly.
- If code is reusable application code, keep FastAPI out of it.

Module names are not sufficient classification. In this repo, some current
modules under `app/services/` are intentionally adapter-leaning even though
they are named as services.

A practical rule:

- If a module chooses HTTP status codes, raises `HTTPException`, shapes HTTP response bodies, or logs transport-only fields such as `http_status`, it is adapter code.
- If a module should be reusable outside HTTP, it must not depend on FastAPI.

---

## Stable principles

### 1. Core code must not import FastAPI.

Domain code and reusable application services must not import FastAPI types such as:

- `Depends`
- `Request`
- `Response`
- `HTTPException`
- router objects
- FastAPI-specific session or transport types

FastAPI belongs at the web boundary.

### 2. High-level policy depends on contracts only.

High-level code should depend on abstractions such as:

- `UserRepository`
- `UnitOfWork`
- `Clock`
- `Mailer`
- `EventBus`

Concrete adapters belong in infrastructure or web composition.

### 3. FastAPI dependency injection stays at the web edge.

Use `Depends(...)` in:

- routes
- provider functions
- web dependency modules

Do **not** use `Depends(...)` inside:

- domain code
- reusable application services
- repositories
- infrastructure internals

### 4. Below the edge, use constructor injection.

Once the object graph crosses the FastAPI boundary, dependencies should be passed as normal Python arguments.

Reusable services and use cases should be constructed like plain Python objects.

### 5. Use `Protocol` by default for ports.

Prefer `Protocol` for structural contracts.

Use ABCs only when you specifically need:

- inheritance semantics
- shared abstract behavior
- registration or class-based constraints

Default to the lightest contract mechanism that expresses the port clearly.

### 6. Request-scoped resources use `yield` dependencies.

Resources with request lifetime, such as database sessions, should be opened and closed through `yield` providers at the web boundary.

Request cleanup should happen in the dependency that owns the resource.

### 7. Application-scoped resources use lifecycle management only when they have real lifecycle needs.

Use FastAPI lifespan for resources that require startup or shutdown work, such as:

- connection pools
- managed clients
- model registries
- worker runtimes
- caches with explicit teardown

Simple cached factories are acceptable for app-scoped objects that do not require startup or teardown.

Do not introduce lifespan only to satisfy style when the resource has no lifecycle semantics.

### 8. Cache configuration once; never cache mutable request state.

Use memoization for stable process-wide configuration, such as settings.

Do **not** cache:

- request-specific state
- user-specific mutable state
- values whose lifetime should be limited to a single request

### 9. Tests override providers, not business code.

Tests should replace dependencies through the composition root.

In FastAPI applications, prefer:

- provider overrides
- test app factories
- explicit dependency replacement at the edge

Avoid test-only branches inside business logic.

### 10. Have one composition root.

There should be one clear composition root per executable entrypoint.

In a FastAPI application, this is typically:

- the app factory
- the dependency/provider module
- the web assembly layer

In this repo, that means separate composition paths for the HTTP app and the
worker/runtime rather than one literal universal root file.

Business code should not perform its own service location.

---

## Error handling rule

**HTTP translation belongs at the web edge.**

That means:

- reusable application services should raise domain, query, or application exceptions
- routers, thin router helpers, dedicated web error-mapping helpers, or explicit exception handlers should translate those exceptions into `HTTPException` or transport-specific responses
- reusable application services should not raise `HTTPException`

A new generic `AppError` hierarchy is **not** the default.

Introduce one only when there is a clear need for a stable cross-transport application-level error contract.

Until that need is explicit, prefer mapping existing domain or query exceptions at the edge.

The documents path is the current positive example of this rule. It should not
be read as proof that every route family in the repo already follows it.

---

## Resource lifetime rule

Use the simplest mechanism that matches the actual lifetime of the resource:

- **`yield` dependencies** for request-scoped resources
- **lifespan** for app-scoped resources with startup or teardown requirements
- **cached factories** for app-scoped objects with no lifecycle behavior

The goal is correct ownership and cleanup, not mechanical uniformity.

---

## Recommended layering

This tree is an illustrative boundary model, not a required filesystem refactor
for the current repo. The repo already has earned internal seams with a
different package layout. The value is in dependency direction and layer intent,
not in directory names.

```text
domain/
  entities.py
  value_objects.py
  ports.py
  errors.py

application/
  use_cases/
  services/

infrastructure/
  db/
  external/

web/
  dependencies.py
  routes/
  schemas/
  error_mapping.py

main.py
```

### Notes

- `domain/` and reusable `application/` code should be framework-agnostic.
- `web/` is allowed to depend on FastAPI.
- `infrastructure/` implements contracts declared by the core.
- `main.py` and the dependency modules compose the app.

If a module shapes HTTP DTOs, chooses status codes, or logs transport fields such as `http_status`, it should live at the web boundary or be explicitly documented as adapter code.

---

## Minimal pattern

```python
from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


# contracts

class UserRepository(Protocol):
    def get_by_id(self, user_id: str) -> dict | None: ...


class UserNotFoundError(Exception):
    pass


# reusable application code

class GetUserProfile:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def execute(self, user_id: str) -> dict:
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user


# infrastructure

class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: str) -> dict | None:
        ...


# web edge

def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_user_repo(
    session: Annotated[Session, Depends(get_db)],
) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_user_profile(
    repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> GetUserProfile:
    return GetUserProfile(repo)


router = APIRouter()


@router.get("/users/{user_id}")
def read_user(
    user_id: str,
    uc: Annotated[GetUserProfile, Depends(get_user_profile)],
):
    try:
        return uc.execute(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc
```

This pattern keeps:

- contracts in the core
- implementations in infrastructure
- dependency providers at the edge
- HTTP translation at the edge

---

## What to avoid

- `Depends(...)` inside reusable services or repositories
- domain or reusable application code importing FastAPI
- `HTTPException` raised below the web boundary
- hidden business logic inside dependency provider functions
- passing raw DB sessions through every layer instead of using repositories or a unit of work
- global mutable singletons presented as DI
- creating new error taxonomies without a concrete consumer
- forcing lifespan for objects that have no startup or shutdown behavior
- ambiguous modules that mix reusable business flow with transport-specific response handling

---

## Decision checklist for ambiguous modules

Before changing or judging a module, answer these questions:

1. Can this code be called meaningfully outside HTTP?
2. Does it choose HTTP status codes or response details?
3. Does it shape transport DTOs or headers?
4. Does it log transport-only fields such as `http_status`?
5. Does it import FastAPI types or provider mechanics?

Interpretation:

- If the transport questions are yes, the module is adapter code and should remain thin.
- If the reuse question is yes, the module should be framework-agnostic.
- If both are true, the module is carrying mixed responsibilities and should be split or reclassified.

---

## Compact formulation

**Contracts in the core. Implementations in infrastructure. FastAPI at the edge. Constructor injection below the boundary. `yield` for request resources. Lifespan only when lifecycle exists. Provider overrides for tests. HTTP translation at the web edge.**
