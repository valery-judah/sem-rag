# Settings injection lifecycle

## Normal startup

Module load triggers `app = create_app()` at the bottom of `api.py`. With no
argument, `create_app` calls `get_settings()`, which is an `@lru_cache`
function that reads from environment variables and `.env` on first call and
returns the same `Settings` instance on every subsequent call.

```
process start
  → uvicorn imports doc_forge.app.api:app
  → module body executes: app = create_app()
      → get_settings()          # first call: reads env / .env, caches result
      → configure_logging(...)  # uses settings.service_name / environment / log_level
      → FastAPI(...)            # uses settings.docs_enabled for swagger URLs
      → app.state.settings = settings
```

## Per-request dependency injection

Route handlers and their dependencies receive settings through FastAPI's `Depends`
mechanism. `get_settings` in `deps.py` is the same `@lru_cache` function imported
from `settings.py`, so every request resolves to the same cached instance — no
re-reading of environment variables at request time.

```python
# deps.py
def get_engine(settings: Annotated[Settings, Depends(get_settings)]) -> Engine:
    return _build_engine(settings.database_url)
```

## Test / custom startup

Pass a `Settings` instance directly to `create_app` to bypass `get_settings`
entirely. This is the primary mechanism for injecting test configuration.

```python
settings = Settings(environment="test", enable_swagger=True, database_url="sqlite+pysqlite:///:memory:")
app = create_app(settings=settings)
```

Because `get_settings` is cached, tests must call `reset_runtime_caches()`
before mutating environment variables and before calling `create_app()`. This
clears the lru_cache so the next `get_settings()` call re-reads the environment.

```python
# conftest.py pattern
reset_runtime_caches()
monkeypatch.setenv("DATABASE_URL", db_url)
app = create_app()
```

## Cache scope

`get_settings` uses `@lru_cache` (no `maxsize` limit, effectively `maxsize=None`).
The cache is process-scoped: one Settings instance per process lifetime unless
explicitly cleared with `get_settings.cache_clear()` (or `reset_runtime_caches()`
which clears all runtime caches including engine, artifact store, and adapters).

## Secret files

In container or cloud deployments, `Settings` also reads from `/run/secrets/`
via `secrets_dir`. A file named `/run/secrets/database_url` would be read as
the `database_url` field value. This requires no code change — it is handled
transparently by pydantic-settings.
