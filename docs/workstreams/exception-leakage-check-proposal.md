# Proposal: Automated Detection of Exception Leakage in FastAPI

## Problem Context
During the architectural review, we identified that `src/doc_forge/app/api.py` had an exception leakage issue. If an unhandled exception reached the global HTTP middleware (`@app.middleware("http")`), it was logged and re-raised (`raise`), allowing it to leak up to Starlette's `ServerErrorMiddleware`. This resulted in standard text-based `500 Internal Server Error` responses instead of JSON payloads conforming to our canonical `ErrorResponse` schema.

We fixed this in `api.py` by adding a global exception handler:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # ... logging ...
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail="Internal server error").model_dump(),
    )
```

However, as the application scales (e.g., adding more sub-apps, routers, or specialized middleware), we risk introducing new routes or middleware that might bypass standard error handling, leading to inconsistent API contracts. 

## Proposed Solutions

### Option 1: AST-Based CI Checker (Recommended)
We can add a custom Python script using the built-in `ast` module to statically analyze our FastAPI applications. This script will enforce the presence of a global exception handler that returns an `ErrorResponse`.

**Implementation details:**
- Write a script (e.g., `scripts/check_exception_handlers.py`) that uses `ast.parse` on all files defining a `FastAPI()` instance.
- The script traverses the AST looking for `app.exception_handler(Exception)`.
- It also verifies that inside the handler, the returned response constructs `ErrorResponse` (i.e., looks for `Return` nodes containing `Call` to `ErrorResponse` or its `.model_dump()`).
- This script can be added to our `poe lint` or `poe verify` pipeline.

### Option 2: Custom Ruff Rule (Advanced)
If we want real-time editor feedback, we could contribute a rule to Ruff or build a custom Flake8 plugin (if Flake8 was in use). However, since we rely on `ruff` natively without custom plugin support out-of-the-box, we would have to rely on an external linter or stick to the AST-based approach (Option 1) which is much easier to maintain locally.

### Option 3: End-to-End/Integration Test Enforcement
Add a universal test in `tests/app/` that mounts the app and explicitly triggers an unhandled exception in an isolated route (e.g., a dummy route injected only during testing or mocking an internal service to raise `Exception`).
- The test asserts that the `status_code` is 500.
- The test asserts that the response JSON conforms exactly to the `ErrorResponse` schema.

**Example Test snippet:**
```python
async def test_global_exception_handler_returns_error_response(app: FastAPI, client: AsyncClient):
    @app.get("/_test_crash")
    def crash():
        raise RuntimeError("simulated crash")
    
    response = await client.get("/_test_crash")
    assert response.status_code == 500
    assert "detail" in response.json()
    assert response.json()["detail"] == "Internal server error"
```
This is robust and guarantees runtime compliance, augmenting the static checks.

## Recommendation
Implement **Option 1 (AST Checker)** for static validation across the codebase and **Option 3 (Integration Test Enforcement)** to ensure runtime correctness. We can include the AST checker in our standard CI pipeline (via `poe verify`) to fail fast when developers instantiate new `FastAPI` objects without the appropriate handlers.