# Manual End-to-End Ingestion Test

**Status:** Verified
**Last verified:** 2026-03-20

## Purpose
This document provides a step-by-step guide to verifying the complete ingestion pipeline locally. You will run a manual end-to-end test using the Docker stack and interact directly with the API and database to ensure documents are processed, chunked, and embedded correctly.

## Prerequisites
- Docker and Docker Compose installed.
- `make` and `curl` available in your terminal.

## Steps

### 1. Start the Docker stack
Bring up the API, worker, and database containers using the provided Make target.
```bash
make docker-up-build
```
*Wait a few seconds for the services to become healthy.*

### 2. Upload a test document
Create a small markdown file and post it to the `/documents` endpoint. The API requires a `multipart/form-data` payload containing a `workspace_id` and the `file`.

```bash
# Create a test markdown file
echo -e "# Test Document\n\nThis is a test paragraph for chunking." > test.md

# Upload it to the API
curl -X POST "http://127.0.0.1:8000/documents" \
  -F "workspace_id=test_workspace" \
  -F "file=@test.md"
```

*Note the `doc_id` returned in the JSON response (e.g., `doc_1234abcd`). You will need it for the next steps.*

### 3. Poll the document status
Use the returned `doc_id` to check the document's ingestion status until the `ingest_status` transitions to `ready`.

```bash
# Replace <YOUR_DOC_ID> with the actual doc_id
curl -s "http://127.0.0.1:8000/documents/<YOUR_DOC_ID>/status"
```
You can repeat this command until you see `"ingest_status": "ready"`.

### 4. Connect to the database
Once the document is ready, connect to the PostgreSQL database container to verify the indexing output.

```bash
docker compose exec db psql -U doc-forge -d doc-forge
```

### 5. Query the chunks and embeddings
Inside the `psql` shell, run the following queries to verify the generated chunks and their corresponding embeddings for your document:

```sql
-- View the extracted text chunks
SELECT chunk_id, text FROM chunks WHERE doc_id = '<YOUR_DOC_ID>';

-- Verify embeddings were created
SELECT chunk_id, embedding_model FROM chunk_embeddings WHERE doc_id = '<YOUR_DOC_ID>';
```

If these queries return rows, the end-to-end ingestion pipeline has successfully processed and indexed your document. You can exit the `psql` shell by typing `\q`.
