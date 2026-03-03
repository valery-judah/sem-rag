# Context: Connectors (MVP-1 Local PDF)

## Purpose in Pipeline
- Component: Phase 1 → **Source Connectors**
- Module path (planned): `src/docforge/connectors/`
- Upstream dependency: none (source boundary)
- Downstream dependency: Structural Parser & Distiller (future)

## Component Boundaries
### Owns
- Fetch raw bytes + minimal metadata into `RawDocument`
- Incremental filtering by `updated_at` (`since`)

### Does Not Own
- PDF parsing/text extraction/canonicalization
- Anchors/structure/segments/embeddings/indexing

## Contract References
- Normative contracts: `./01_rfc.md`
- Source inspiration: `docs/phase-1.md` §3.1 (“Source Connectors”)

## Invariants Summary
- Stable identity: `doc_id` stable across re-runs when config unchanged
- Anchorability/provenance: `source_ref` + `url` preserved; bytes hash recorded
- Determinism: same config + same file → same `RawDocument` fields (except timestamps if file mtime changes)

## Golden Example (Compact)
Input:
```toml
[[sources]]
type = "local_file"
path = "data/mvp.pdf"
doc_id = "mvp_pdf"
content_type = "application/pdf"
metadata = { title = "MVP PDF" }
acl_scope = { visibility = "internal" }
```

Expected outcomes:
- A single `RawDocument` is produced.
- `RawDocument.source == "local_file"`.
- `RawDocument.source_ref == "data/mvp.pdf"` (preserved as configured).
- `RawDocument.url == "file:data/mvp.pdf"` unless explicitly configured otherwise.
- `RawDocument.content_type == "application/pdf"`.
- `RawDocument.content_bytes` matches the bytes read from the file.
- `RawDocument.timestamps.updated_at` reflects filesystem `mtime` (UTC).

Output shape (bytes omitted):
```json
{
  "doc_id": "mvp_pdf",
  "source": "local_file",
  "source_ref": "data/mvp.pdf",
  "url": "file:data/mvp.pdf",
  "content_type": "application/pdf",
  "metadata": { "title": "MVP PDF" },
  "acl_scope": { "visibility": "internal" },
  "timestamps": { "created_at": "...", "updated_at": "..." }
}
```

## Verification Map
| Contract area | Verification family | Example checks |
|---|---|---|
| TOML config parsing | Unit tests | loads `[[sources]]` (type/path/doc_id/content_type/metadata/acl_scope) into config model |
| `LocalFileConnector` output contract | Unit tests | yields exactly 1 `RawDocument` with required fields + correct bytes + correct `content_type` |
| CLI emission (`raw/*.json` + `blobs/*.bin`) | CLI tests | `docforge connect` writes both files; `content_sha256` matches blob bytes |

