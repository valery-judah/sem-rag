# RFC: Connectors (MVP-1 Local PDF)

## 1. Problem and Scope

Build the Phase 1 “Source Connectors” boundary for an MVP that ingests a **single local PDF file** into a stable `RawDocument` contract suitable for downstream parsing/segmentation.

### In Scope
- Single source type: `local_file` (one PDF)
- TOML config `[[sources]]`
- Connector produces `RawDocument` with required fields
- Incremental filter (`since`) based on filesystem `mtime`

### Out of Scope
- Parsing PDF contents (text extraction, canonicalization)
- Multi-doc crawling
- Remote sources (Confluence/Jira/GDrive/Git)

## 2. Normative Contracts
This document is the authority for connector inputs/outputs, required fields, invariants, deterministic ordering rules, and identity policy for MVP-1.

### 2.1 Input Schema (TOML conceptual schema)
Configuration is provided via TOML with an array-of-tables at `[[sources]]`.

Required fields:
- `type: "local_file"`
- `path: string` (file path; relative or absolute)

Optional fields:
- `doc_id: string` (recommended for single-file MVP)
- `url: string`
- `content_type: string`
- `metadata: object` (e.g. `{ title = "..." }`)
- `acl_scope: object` (opaque; stored as-is)

### 2.2 Output Schema (`RawDocument`)
Connector output must match the Phase 1 connector contract shape in `docs/phase-1.md` §3.1.

```json
{
  "doc_id": "string",
  "source": "local_file",
  "source_ref": "string",
  "url": "string",
  "content_bytes": "bytes",
  "content_type": "application/pdf|application/octet-stream|...",
  "metadata": { "title": "string", "...": "..." },
  "acl_scope": { "...": "opaque" },
  "timestamps": { "created_at": "timestamp", "updated_at": "timestamp" }
}
```

Notes:
- `content_bytes` is an in-memory field; CLI/debug serialization must not inline PDF bytes into JSON.

### 2.3 Required Fields
All `RawDocument` fields in §2.2 are required on produced objects:
- `doc_id`, `source`, `source_ref`, `url`
- `content_bytes`, `content_type`
- `metadata`, `acl_scope`
- `timestamps.created_at`, `timestamps.updated_at`

Optionality only applies to configuration; connectors must fill defaults as needed.

## 3. Invariants and Deterministic Ordering
### 3.1 Invariants
1. `doc_id` is stable across re-ingestion when config unchanged.
2. `source_ref` equals the configured path string (preserved as-given).
3. CLI emission must compute `content_sha256` that matches the emitted blob bytes.

### 3.2 Ordering Rules
- If multiple sources exist later: process sources in config order.
- Within a connector: emit documents in stable lexicographic order of `source_ref`.
- MVP-1 emits exactly one document.

## 4. Identity / Anchor Policy
Locked decisions for MVP-1:
- `doc_id` resolution:
  - If config provides `doc_id`, use it.
  - Else derive `doc_id = "local_file:" + sha256(source_ref_utf8).hexdigest()`.
- `url` default: `"file:" + source_ref` unless configured.
- `timestamps.updated_at`: filesystem `mtime` converted to UTC.
- `timestamps.created_at = timestamps.updated_at` (MVP-1 simplification).

## 5. Success Criteria
MVP-1 is considered successful when:
- `docforge connect` ingests the configured PDF and emits artifacts successfully.
- Unit tests cover: contract fields + incremental filter.
- Outputs are deterministic for unchanged inputs and config.

## 6. Non-Goals
- Any parsing/canonicalization beyond raw byte fetching
- Orchestration, retries, caching, or multi-source scheduling

## 7. Open Decisions
None for MVP-1.

## 8. Change Control
- Any change to `RawDocument` fields, identity policy, or emission artifacts requires updating:
  - this RFC
  - corresponding tests
  - any downstream code that assumes the contract

