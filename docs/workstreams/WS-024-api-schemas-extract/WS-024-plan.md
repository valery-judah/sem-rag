# Implementation Plan: API Schemas Extraction (WS-024)

## Overview
This plan details the steps required to extract the Pydantic DTO models from `src/doc_forge/app/api.py` into `src/doc_forge/app/schemas.py`.

## Step 1: Create `schemas.py`
1. Create a new file at `src/doc_forge/app/schemas.py`.
2. Add the necessary imports to the top of the file:
   - Standard library and Pydantic imports (`BaseModel`, `ConfigDict`, `Field`).
   - Domain model imports used by the schemas (`DocId`, `QueryId`, `AnswerDraft`, `AnswerMode`, `CitationBundle`, `SupportState`).
   - Example dictionary imports from `.api_examples`.
3. Move the following classes verbatim from `api.py` to `schemas.py`:
   - `RetrievalQueryRequest`
   - `QueryAnswerResponse`
   - `WorkerJobResult`
   - `ErrorResponse`
   - `SystemStatusResponse`
   - `DocumentDetailResponse`

## Step 2: Refactor `api.py`
1. Remove the 6 extracted classes from `src/doc_forge/app/api.py`.
2. Update the imports in `api.py`:
   - Remove unused Pydantic imports (`BaseModel`, `ConfigDict`, `Field`) if they are no longer needed.
   - Remove the unused domain imports if they are only used by the models.
   - Remove unused example imports from `.api_examples`.
   - Add a new import statement: `from .schemas import DocumentDetailResponse, ErrorResponse, QueryAnswerResponse, RetrievalQueryRequest, SystemStatusResponse, WorkerJobResult`.

## Step 3: Validation
1. Run the local verification suite:
   ```bash
   uv run poe verify
   ```
2. The verification script will ensure that:
   - Types are correct (Pyright).
   - Code is formatted and linted properly (Ruff).
   - Tests pass successfully.

## Hand-off to Code Mode
Once this plan is reviewed, switch to Code mode to execute the steps above.