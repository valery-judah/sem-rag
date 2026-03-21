Yes.

For FastAPI, the stable formulation is:

**Dependency inversion**: business code depends on abstract contracts, not FastAPI, ORM, or transport details.

**Dependency injection**: FastAPI resolves concrete implementations only at the HTTP boundary; below that boundary, use plain constructor injection.

FastAPI gives you the mechanics for this: callable dependencies, nested sub-dependencies, per-request dependency cachi([FastAPI][1])l has to come from you.

## Stable principles

1. **The domain must not import FastAPI.**
   No `Depends`, `Request`, `Response`, router objects, or ORM session types in domain entities or use cases.

2. **High-level policy depends on contracts only.**
   Use interfaces such as `UserRepository`, `UnitOfWork`, `Clock`, `Mailer`, `EventBus`.

3. **FastAPI DI stays at the edge.**
   Use `Depends(...)` in routes and provider functions only.

4. **Inside the app, prefer constructor injection.**
   Services and use cases should receive dependencies as normal Python arguments.

5. **Use `Protocol` by default for ports; use ABCs when you need inheritance semantics.**
   Python supports structural subtyping with `Protocol`, and the `abc` module provides standard abstract-base-class machinery.

6. **Request-scoped resources use `yield` dependencies.**
   DB sessions and simila([Python documentation][2])nd closed through `yield`. FastAPI documents this explicitly.

7. **Application-scoped resources use lifespan.**
   Pools, model registries, and long-lived clients belong in FastAPI lifespan setup/shutdown.

8. **Configuration may be cached once; mutable request state must not be.**
   FastAPI resolves repeated uses of the same dependency once per request by default, and its settings docs show caching settings with `lru_cache` to avoid repeated file reads.

9. **Tests override providers, not business code.**
   FastAPI provides `app.dependency_overrides` for replacing dependencies during tests.

10. **Have one composition root.**
    The app factory or dependency module should be the single place where contracts are bound to concrete adapters.

## Practical rule

**FastAPI is an adapter, not the architecture.**

That one sentence avoids most DI mistakes in FastAPI codebases.

## Recommended layering

```text
domain/
  entities.py
  ports.py          # Protocol / ABC contracts

application/
  use_cases/

infrastructure/
  db/
  external/

web/
  dependencies.py   # FastAPI providers only
  routes/

main.py             # app factory, lifespan, router wiring
```

## Minimal pattern

```python
from typing import Protocol, Annotated
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

# contracts

class UserRepository(Protocol):
    def get_by_id(self, user_id: str) -> dict | None: ...

class U:contentReference[oaicite:8]{index=8} def commit(self) -> None: ...
    def rollback(self) -> None: ...

# use case

class GetUserProfile:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, user_id: str) -> dict | None:
        return self.rep:contentReference[oaicite:9]{index=9}infrastructure

class SqlAlchemyUserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: str) -> dict | None:
        ...

# FastAPI edge

def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_user_repo(
   :contentReference[oaicite:10]{index=10}b)],
) -> UserRepository:
    return SqlAlchemyUserRepository(session)

def get_user_profile(
    repo: Annotated[UserRepository, Depends(get_user_repo)],
) :contentReference[oaicite:11]{index=11}le(repo)

app = FastAPI()

@app.get("/users/{user_id}")
def read_user(
    user_id: str,
    uc: Annotated[GetUserProfile, Depends(get_user_profile)],
):
    return uc.execute(user_id)
```

## What to avoid

* `Depends(...)` inside services or repositories
* domain code importing FastAPI
* injecting raw DB sessions everywhere instead of repositories/UoW
* hiding business logic inside dependency functions
* global mutable singletons as “DI”

## Compact formulation

A stable set of principles for FastAPI is:

**Contracts in the core. Implementations in infr([FastAPI][3]). Constructor injection below the boundary. `yield` for request resources. Lifespan for app resources. Dependency overrides for tests.**

That is the version that remains stable even if you change web framework, ORM, or test strategy.
