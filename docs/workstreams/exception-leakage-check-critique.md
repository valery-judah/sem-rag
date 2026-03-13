# Critique: Automated Detection of Exception Leakage in FastAPI

**Author:** Principal Software Engineer
**Date:** Current
**Reference Proposal:** [`docs/workstreams/exception-leakage-check-proposal.md`](docs/workstreams/exception-leakage-check-proposal.md)

## 1. Executive Summary
While standardizing error responses to an `ErrorResponse` canonical format is a critical goal for maintaining stable API contracts, the proposed solution of building a custom AST-based checker (Option 1) is not recommended. It introduces a high-maintenance, low-ROI tool that attempts to solve an architectural problem through static inspection. Furthermore, the proposal demonstrates a misunderstanding of FastAPI's exception lifecycle regarding middleware. An Application Factory pattern combined with a top-level exception-handling middleware is the recommended enterprise approach to guarantee consistency by construction rather than post-hoc verification.

---

## 2. ROI of the AST-Based Checker (Option 1)
**Verdict: Negative ROI**

Building and maintaining a custom AST-based checker for a framework-specific configuration pattern is an anti-pattern. 
- **Brittleness:** An AST parser is highly sensitive to code structure. If a developer aliases `FastAPI`, wraps the instantiation in a helper function, or configures the exception handler in a separate file, the checker will either produce false positives (failing correct code) or false negatives (passing broken code).
- **Maintenance Burden:** As the framework evolves or our internal conventions change, the custom parser will require ongoing maintenance.
- **Wrong Abstraction Level:** Static analysis is excellent for catching common language pitfalls (e.g., via Ruff) or type errors (e.g., via MyPy), but it is a poor fit for verifying runtime framework configuration. We should be enforcing correct architecture "by construction" rather than "by inspection."

---

## 3. The Actual Exception Handling Lifecycle in FastAPI/Starlette
The proposal incorrectly assumes that an `@app.exception_handler(Exception)` will catch exceptions leaking from any middleware. In the Starlette/FastAPI ASGI stack, the exception handling lifecycle is strictly layered:

1. **Outer Middlewares:** Custom middlewares added via `@app.middleware("http")` (which uses `BaseHTTPMiddleware`) or `app.add_middleware()` sit at the very edge of the application.
2. **ExceptionMiddleware:** This built-in Starlette middleware wraps the actual routing and endpoint execution.
3. **Routers & Endpoints:** Where your actual business logic lives.

If an exception is raised *inside* an endpoint or a dependency, the `ExceptionMiddleware` catches it and delegates to `app.exception_handler`. However, if an exception is raised in an **outer middleware** (e.g., authentication, logging, or rate-limiting middleware), it occurs *outside* the `ExceptionMiddleware`'s scope. 

Therefore, `app.exception_handler` will **not** catch exceptions leaking from outer middlewares. The exception will bubble up to Starlette's `ServerErrorMiddleware` (or whatever sits above it), completely bypassing our custom `ErrorResponse` formatting. Implementing Option 1 enforces a pattern that doesn't actually solve the stated problem of middleware exception leakage.

---

## 4. Enterprise Patterns & Architectural Soundness
Instead of relying on a bespoke linter, we should solve this through architectural design patterns that guarantee consistency.

### A. The Application Factory Pattern (`create_app()`)
Rather than allowing developers to manually instantiate `FastAPI()` throughout the codebase and hoping they remember to attach the right handlers, we should centralize the configuration using an Application Factory.

```python
# src/doc_forge/app/factory.py
def create_app() -> FastAPI:
    app = FastAPI(title="Doc Forge API")
    
    # Register all standard middlewares
    app.add_middleware(GlobalExceptionMiddleware) # See below
    
    # Register all standard exception handlers
    register_exception_handlers(app)
    
    return app
```
By enforcing the use of `create_app()` across the organization (which is easily verifiable in code review without custom tooling), we guarantee that every application or sub-application is configured correctly out of the box.

### B. Outer Exception-Handling Middleware
To truly address the problem of exceptions leaking from *anywhere* in the application (including other middlewares), we should implement a top-level ASGI middleware specifically designed to catch everything and return an `ErrorResponse`. This middleware must be added *last* (so it executes *first* in the request lifecycle) to wrap all other middlewares.

```python
class GlobalExceptionMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Format to canonical ErrorResponse and send response directly
            response = JSONResponse(
                status_code=500,
                content=ErrorResponse(detail="Internal server error").model_dump()
            )
            await response(scope, receive, send)
```

## 5. Conclusion and Next Steps
1. **Reject Option 1 (AST Checker):** It is brittle, high-maintenance, and enforces a pattern that fails to address middleware exception leakage.
2. **Adopt the Application Factory Pattern:** Standardize the creation of `FastAPI` applications via a central `create_app()` factory.
3. **Implement an Outer Exception Middleware:** To guarantee no unhandled exceptions leak as plain text `500 Internal Server Error`, wrap the entire ASGI application in a catch-all middleware.
4. **Approve Option 3 (Integration Test):** Keep the proposed E2E/Integration test approach. Testing the factory-produced application against simulated failures is the most robust way to ensure runtime compliance.