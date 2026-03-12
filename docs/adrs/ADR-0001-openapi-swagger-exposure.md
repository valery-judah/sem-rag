# ADR-0001: OpenAPI and Swagger UI Exposure

- Status: accepted
- Date: 2026-03-12

## Context
Operators and developers need a way to inspect the `doc_forge` API payloads, especially the internal test routes (`/queries`, `/documents`, etc.). The application currently uses FastAPI, which provides an OpenAPI schema and Swagger UI by default, but it does not have explicit configuration around its exposure, title, or version. Since `doc_forge` currently has no stable public API (as documented in `docs/evergreen/api-contracts.md`), we need a deliberate design for exposing these docs without implying they represent a stabilized public interface.

## Decision
We will explicitly configure FastAPI's OpenAPI and Swagger UI exposure with the following design:

1. **Endpoints:**
   - Swagger UI will be exposed at the default `/docs` endpoint.
   - The OpenAPI JSON schema will be exposed at `/openapi.json`.
   - ReDoc will be disabled (`redoc_url=None`) to keep the exposed surface area focused.

2. **Environment Toggle:**
   - The OpenAPI schema and Swagger UI will be enabled by default in the `dev` environment (`DOC_FORGE_ENVIRONMENT == "dev"`).
   - A new environment variable, `DOC_FORGE_ENABLE_SWAGGER` (boolean), will be added to `AppSettings` in `src/doc_forge/app/settings.py`.
   - If `DOC_FORGE_ENABLE_SWAGGER` is explicitly set to `True`, Swagger will be enabled regardless of the environment (useful for operators in higher environments).
   - If not in `dev` and the flag is not `True`, OpenAPI generation and the UI will be disabled (`openapi_url=None`, `docs_url=None`).

3. **Metadata Updates:**
   - `title`: "Doc Forge Internal API" (explicitly highlighting that this is an internal, non-stable interface).
   - `version`: Match the package version (e.g., "0.1.0" as defined in `pyproject.toml`).
   - `description`: "Internal document lifecycle and query evaluation API. No stable public contract."

## Consequences
- Positive: Developers and operators get a clear, interactive interface to test internal seams and endpoints.
- Positive: Security by default in higher environments, preventing accidental exposure of internal application structure.
- Negative/Tradeoff: Requires adding logic to parse `pyproject.toml` or hardcode the version in `src/doc_forge/app/api.py`.

## Related Workstreams
- `docs/workstreams/WS-007-public-api/` (Future public API workstream)
