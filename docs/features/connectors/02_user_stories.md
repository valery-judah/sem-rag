# User Stories: Connectors (MVP-1 Local PDF)

## Personas
- **Developer (local MVP)**: wants a deterministic way to ingest a local PDF for downstream parsing experiments.
- **Integrator**: wants a stable contract to build parsers/segmenters against without guessing connector behavior.

## Acceptance Criteria (Given / When / Then)

### AC1 — Ingest single PDF
- Given a TOML config with one `local_file` PDF source
- When `LocalFileConnector.iter_raw_documents()` runs
- Then exactly one `RawDocument` is produced with:
  - required fields present (per `01_rfc.md` §2.3)
  - `content_bytes` equal to the file bytes
  - `content_type` resolved to `application/pdf` by config or `.pdf` suffix

### AC2 — Incremental since filter
- Given a `since` timestamp that is newer than the file’s `timestamps.updated_at`
- When `LocalFileConnector.iter_raw_documents(since=...)` runs
- Then zero documents are yielded

### AC3 — CLI emits artifacts
- Given `docforge connect --config <config.toml> --out <dir>`
- When the command succeeds
- Then:
  - `<dir>/raw/*.json` is written (metadata only; no PDF bytes inline)
  - `<dir>/blobs/*.bin` is written (raw bytes)
  - the JSON sidecar includes `content_sha256` matching the blob bytes

## Edge / Failure Scenarios (explicit)
- Given a missing file path, `docforge connect` exits non-zero with a clear error.
- Given a non-readable file, `docforge connect` exits non-zero with a clear error.
- Given an empty file, ingestion succeeds but bytes length is recorded as zero.

## Traceability Matrix
| AC | RFC section(s) | Test category | Planned test module(s) |
|---|---|---|---|
| AC1 | `01_rfc.md` §2–§4 | Unit | `tests/test_connectors_local_file.py` |
| AC2 | `01_rfc.md` §1, §3.1 | Unit | `tests/test_connectors_local_file.py` |
| AC3 | `01_rfc.md` §3.1 | CLI | `tests/test_cli_connect.py` |

