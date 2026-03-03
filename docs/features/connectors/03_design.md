# Design: Connectors (MVP-1 Local PDF)

## 1. Design Goals
- Minimal surface area and minimal dependencies (TOML via stdlib `tomllib`)
- Deterministic behavior aligned to `docs/phase-1.md` connector contract
- Clear boundary: connectors fetch raw bytes; parsing is downstream

## 2. Data Flow
1. Load TOML config → `DocforgeConfig`
2. `make_connector(source_cfg)` → `LocalFileConnector`
3. Connector yields `RawDocument`
4. CLI serializes:
   - JSON sidecar (no bytes) + blob file (raw bytes)

## 3. Algorithms and Tie-Breakers
### 3.1 MIME type selection
Priority order:
1. Use configured `content_type` if provided.
2. If the path suffix is `.pdf`, use `application/pdf`.
3. Else use `mimetypes.guess_type(path)`; if unknown, fallback to `application/octet-stream`.

### 3.2 Timestamp normalization
- `timestamps.updated_at` comes from filesystem `mtime` and is converted to a UTC datetime.
- `timestamps.created_at = timestamps.updated_at` for MVP-1.

### 3.3 Deterministic filenames (CLI emission)
- Compute `doc_key = sha256(doc_id).hexdigest()` to create safe deterministic filenames.
- Emit:
  - `raw/<doc_key>.json` (sidecar metadata, includes `content_sha256`)
  - `blobs/<doc_key>.bin` (raw bytes)

## 4. Edge-Case Handling
- Missing file path: error, non-zero exit.
- Non-readable file: error, non-zero exit.
- Empty file: allowed; still yields a `RawDocument` and emits artifacts with `bytes_len == 0`.

## 5. Tradeoff Decisions
- Emit bytes to `blobs/*.bin` instead of JSONL to avoid large and non-portable JSON artifacts.
- Keep `acl_scope` opaque to avoid coupling to auth/identity systems in MVP-1.

## 6. Observability
Minimal event vocabulary (printed/logged):
- `DocFetched(doc_id, updated_at, bytes_len, content_type)`

Payload fields (minimum):
- `doc_id`, `source_ref`, `updated_at`, `bytes_len`, `content_type`, `content_sha256`

## 7. Performance and Complexity Notes
- Single file read into memory; acceptable for MVP-1.
- No concurrency, pagination, or retries.

## 8. Limitations and Deferred Items
- No directory crawling, no multi-source enumeration.
- No remote connectors.
- No parsing/canonicalization, anchors, segmentation, embeddings, or publishing.

