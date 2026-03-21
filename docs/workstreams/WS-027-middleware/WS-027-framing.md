# Framing

## Resolution
The `request_logging_middleware` was removed entirely rather than extracted.
The global exception handler remains in `create_app()` as the sole app-level
safeguard for unhandled errors.

Removed capabilities (intentionally out of scope until observability redesign):

- `x-request-id` response header
- `http.request.started` / `http.request.completed` log events
- request-scoped `request_id` contextvar binding

## Original Problem
`request_logging_middleware` was a ~50-line closure nested inside `create_app()`
in `src/doc_forge/app/api.py`. After WS-022→WS-025 extracted DTOs, routers, and
services, the middleware and the global exception handler were the remaining
coupling that made the app factory hard to scan.

The middleware mixed three concerns in a single function:

- request-ID generation and contextvar binding
- structured request/response logging with timing
- unhandled-exception catch, log, and error-response construction

The middleware had been inline since the first commit (`50f4cba`). It was never
extracted because it wasn't the focus of prior workstreams.

## Scope
- `request_logging_middleware` in `src/doc_forge/app/api.py:60-106`
- `global_exception_handler` in `src/doc_forge/app/api.py:108-115`
- test coverage in `tests/app/test_exception_leakage.py`

## Constraints
- the stable HTTP contract must be preserved (`x-request-id` header, error
  response shape, structured log events)
- structlog contextvars integration must continue to work (request-ID binding
  propagates to all downstream log calls)
- no streaming endpoints exist today, so response-buffering is not a current
  concern

## Input context
- paths:
  - `src/doc_forge/app/api.py`
  - `src/doc_forge/app/logging.py`
  - `src/doc_forge/app/schemas.py` (`ErrorResponse`)
  - `tests/app/test_exception_leakage.py`
- read first:
  - `src/doc_forge/app/api.py`

## Key decisions
- Which extraction pattern to use (see Options below)
- Whether to also extract `global_exception_handler` alongside the middleware
- Whether to split the middleware's three concerns or keep them unified

## Expected outputs
- middleware logic extracted from `create_app()` into its own module or class
- `create_app()` reduced to app construction, middleware registration, and router
  inclusion
- existing tests continue to pass without modification (or with minimal import
  updates)

## Exit criteria
- a design option is chosen and documented
- the extraction approach is clear enough to execute without further framing

## Objective
Extract request logging middleware from the app factory so that `create_app()`
reads as a wiring function rather than an implementation of request lifecycle
logic.

## Non-goals
- changing the logging format or event names
- replacing structlog with a different logging library
- adding new middleware (CORS, auth, rate limiting)
- modifying the HTTP contract (headers, status codes, response shapes)

## Options

### 1. BaseHTTPMiddleware Class
Extract to `src/doc_forge/app/middleware.py` as a Starlette `BaseHTTPMiddleware`
subclass. Register via `app.add_middleware(RequestLoggingMiddleware)`.

```python
from starlette.middleware.base import BaseHTTPMiddleware

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # request-ID, logging, timing, error handling
        ...
```

Pros:

- standard Starlette pattern, familiar to most FastAPI developers
- clean class-based encapsulation
- easy to unit test by instantiating the class directly
- `create_app()` becomes a short wiring function

Cons:

- `BaseHTTPMiddleware` buffers the entire response body before returning,
  which breaks streaming responses
- not a concern today (no streaming endpoints), but limits future options
- adds a Starlette import dependency (already transitive via FastAPI)

### 2. Pure ASGI Middleware
Write a raw ASGI callable class that wraps the application. No Starlette base
class.

```python
class RequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        # request-ID, logging, timing, error handling at ASGI level
        ...
```

Pros:

- streaming-safe — does not buffer the response body
- no dependency on `BaseHTTPMiddleware` internals
- full control over ASGI lifecycle

Cons:

- significantly more boilerplate (must handle `scope`, `receive`, `send`
  manually)
- harder to read and maintain for developers unfamiliar with raw ASGI
- error handling and response construction are more verbose at this level
- overengineered for a project with no streaming endpoints

### 3. Extract as Standalone Function
Keep the `@app.middleware("http")` decorator style, but define the function in
`src/doc_forge/app/middleware.py` and register it in `create_app()`.

```python
# middleware.py
async def request_logging_middleware(request, call_next):
    ...

# api.py
from .middleware import request_logging_middleware
app.middleware("http")(request_logging_middleware)
```

Pros:

- smallest diff — the function body does not change at all
- no new abstraction or class
- easy to review and merge

Cons:

- still a bare function, not a reusable component
- registration in `create_app()` is slightly awkward (decorator used as a
  function call)
- does not improve testability beyond what exists today
- still buffers the response (same as `@app.middleware("http")`)

### 4. Split Concerns
Decompose the middleware into two smaller, focused pieces:

- a thin request-ID middleware (contextvar binding + response header)
- access logging delegated to uvicorn's access log or a structlog processor

```python
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = f"req-{uuid4().hex}"
        bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        clear_contextvars()
        return response
```

Pros:

- strongest separation of concerns
- request-ID middleware becomes trivially testable
- access logging can leverage uvicorn's built-in capabilities
- each piece is small enough to reason about independently

Cons:

- two things to maintain instead of one
- uvicorn access logging format may not match the current structured log
  events (`http.request.started`, `http.request.completed` with `duration_ms`)
- may require a custom uvicorn log formatter to preserve the current contract
- more moving parts for a problem that is currently contained

## Tradeoff Comparison

| Option | Separation | Testability | Boilerplate | Streaming-safe | Complexity |
| --- | --- | --- | --- | --- | --- |
| BaseHTTPMiddleware class | high | high | low | no* | low |
| Pure ASGI middleware | high | high | medium-high | yes | medium |
| Extract as function | medium | medium | lowest | no* | lowest |
| Split concerns | highest | high | medium | partial | medium |

*`BaseHTTPMiddleware` and `@app.middleware("http")` both buffer the response
body. This is not a current concern (no streaming endpoints).

## Relevant context
- paths:
  - `src/doc_forge/app/api.py`
  - `src/doc_forge/app/logging.py`
  - `tests/app/test_exception_leakage.py`
- components:
  - structlog contextvars integration
  - `ErrorResponse` schema in `src/doc_forge/app/schemas.py`
- constraints:
  - must preserve `x-request-id` header contract
  - must preserve structured log event names and fields
- read first:
  - `src/doc_forge/app/api.py`

## Workflow steps
1. Frame the workstream scope and constraints.
2. Choose an extraction pattern from the options above.
3. Execute the extraction and validate.

## Validation and Definition of Done
- `create_app()` no longer contains middleware implementation logic
- `tests/app/test_exception_leakage.py` passes without modification
- `x-request-id` header is still set on all responses
- structured log events (`http.request.started`, `http.request.completed`)
  are unchanged in shape
- full test suite passes

## Linked artifacts
- `docs/workstreams/WS-027-middleware/WS-027-workstream.md`
- Prior extractions: WS-022 (api-docs), WS-023 (api-docs-extract),
  WS-024 (api-schemas-extract), WS-025 (api-decoupling)
