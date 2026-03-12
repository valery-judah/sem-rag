# WS-005 Alpha API Exposure Plan

**Date:** 2026-03-12  
**Status:** proposed  
**Scope of this note:** Lightweight API exposure plan for local frontend / alpha environments, and not a move to a stable public contract.

## Summary

This note records a simplified plan to expose the DocForge API for local development (e.g., frontend integration via docker-compose) and early alpha environments (e.g., Kubernetes). 

We determined that we do not need a "true public" API decoupling at this stage. Instead of creating a separate stable public contract, we just need to expose the existing API safely for these targeted use cases.

## Context and Findings

* The application already binds to `0.0.0.0` in `src/doc_forge/runtime.py` and `docker-compose.yml`. This is already correct for containerized environments and should be maintained.
* The shared entrypoint (`python -m doc_forge.runtime`) remains the planned architecture and does not need to be split into separate application images.
* To support browser-based frontends during local development and in alpha environments, Cross-Origin Resource Sharing (CORS) needs to be configured.

## Implementation Plan

The required steps are lightweight and focused on enabling cross-origin requests:

1. **Add Middleware:** Add `CORSMiddleware` from `fastapi.middleware.cors` to the FastAPI application instance in `src/doc_forge/app/api.py`.
2. **Configure Origins:** Introduce a new environment variable `DOC_FORGE_CORS_ORIGINS` (likely in settings) to dynamically handle allowed origins. This allows local environments to permit `http://localhost:*` while alpha environments can restrict it to specific deployed frontend domains.
3. **Maintain Bindings:** Acknowledge and keep the `0.0.0.0` binding in `src/doc_forge/runtime.py` and `docker-compose.yml` as it is already correct.
4. **Maintain Entrypoint:** Keep the shared entrypoint (`python -m doc_forge.runtime`) as planned, avoiding unnecessary architectural changes.

## Validation Plan

Recommended validation for the eventual implementation:

* Run the standard test suite: `make test`
* Verify that the API starts successfully locally via `docker-compose`.
* Confirm that CORS headers are correctly applied when requests are made from origins specified in `DOC_FORGE_CORS_ORIGINS`.
