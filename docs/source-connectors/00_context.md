# Context: Source Connectors

## Pipeline Placement
The Source Connectors module is the **very first component** in the Knowledge Representation Pipeline.
- **Upstream Dependencies:** None (fetches directly from external/internal sources like Wiki, Drive, Git, DBs, Jira, Confluence, etc.).
- **Downstream Dependencies:** Provides output directly to the **Structural Parser & Distiller**, which relies on the standardized output from this module.

## Boundary Contract

### Inputs
- Source-specific configuration (e.g., credentials, target spaces/repos, inclusion/exclusion paths).
- Sync state/cursors for incremental runs (e.g., last `updated_at` timestamp, commit hash, or event streams).

### Outputs (The `RawDocument` Schema)
Connectors must yield a standardized `RawDocument` conforming to this exact schema:

```json
{
  "doc_id": "string",
  "source": "confluence|gdrive|git|jira|...",
  "source_ref": "string",
  "url": "string",
  "content_stream": "Iterator[bytes]",
  "content_type": "text/html|text/markdown|application/pdf|text/plain|...",
  "metadata": { 
    "title": "string", 
    "...": "..." 
  },
  "acl_scope": { 
    "...": "opaque" 
  },
  "timestamps": { 
    "created_at": "...", 
    "updated_at": "..." 
  }
}
```

## Invariants & Rules

1. **Stable Identity:** `doc_id` MUST be perfectly stable across re-ingestion and incremental syncs. If a document changes externally but remains the "same" document, its `doc_id` cannot change.
2. **Metadata Consistency:** Every `RawDocument` must preserve ACL scope, timestamps, URL, and a `source_ref` so downstream modules and the final published index can trace content back to the originating system.
3. **No Content Modification:** Source connectors fetch raw bytes. They DO NOT parse, canonicalize, or clean the content. The `content_type` must accurately reflect the payload format to ensure the downstream Structural Parser can dispatch the correct parser.
4. **Resilience:** The extraction logic must gracefully handle temporary source outages, yielding clear error classes, and supporting retries.
5. **Incremental Capability:** Connectors must yield only modified, added, or deleted documents relative to the provided cursor or event stream. Re-fetching unmodified documents should be explicitly bypassed unless doing a forced full sync.

## Golden Examples

**Example 1: Confluence Page**
```json
{
  "doc_id": "conf_space_12345",
  "source": "confluence",
  "source_ref": "page/12345",
  "url": "https://wiki.corp.com/spaces/ENG/pages/12345/Architecture",
  "content_stream": ["<p>Some HTML ", "content...</p>"],
  "content_type": "text/html",
  "metadata": { "title": "Architecture Overview" },
  "acl_scope": { "groups": ["engineering", "leadership"] },
  "timestamps": { "created_at": "2023-01-15T08:00:00Z", "updated_at": "2023-11-20T10:00:00Z" }
}
```

## Test Map
- **Stable Identity Tests:** Ensure `doc_id` deterministic generation logic from source-specific IDs doesn't drift.
- **Contract Adherence Tests:** Validate the output of all connectors strictly against the `RawDocument` schema.
- **Incremental Polling Tests:** Simulate metadata updates and confirm that only modified files are fetched when passing a sync cursor.