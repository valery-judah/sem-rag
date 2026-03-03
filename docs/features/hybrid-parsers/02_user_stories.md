# User Stories: Hybrid PDF Parsing Pipeline

## 1. Personas and Outcomes
- As a pipeline operator, I need PDF parsing to be stable and debuggable so ingest runs are reproducible and failures are diagnosable.
- As a retrieval/citation consumer, I need page/region provenance so citations can be traced to PDF locations.
- As a downstream chunking/segmentation developer, I need deterministic ordering and stable page delimiters so chunk boundaries are predictable.

## 2. Acceptance Criteria

### AC1: Deterministic page selection
- Given a PDF document and fixed engine versions/config
- When Marker and MinerU candidates are scored per page
- Then the selected engine for each page is deterministic
- And ties are broken deterministically (preference order is stable)

### AC2: Best-effort page coverage
- Given a PDF document containing mixed digital-born and scan-heavy pages
- When the hybrid pipeline runs
- Then each page yields at least one text-bearing block
- Or a deterministic placeholder block is emitted for unparseable pages

### AC3: Traceability / provenance on every block
- Given any emitted block in the intermediate schema
- When provenance fields are inspected
- Then the block includes `page_idx` and `source.engine`
- And `source.engine_artifact_ref` is present for reproducible debugging

### AC4: Deterministic ordering and page delimiters
- Given a PDF with multi-column layouts
- When blocks are ordered and distilled into `canonical_text`
- Then block ordering is natively preserved from the selected engine via `reading_order_key`
- And page delimiters are stable and versioned

### AC5: Intermediate artifact is emitted
- Given a successful parse run
- When artifacts are persisted
- Then `extracted_pdf_document.json` is written deterministically
- And `selection_log.jsonl` contains per-page scores and reasons

## 3. Failure and Edge Scenarios

### ES1: Engine timeout or crash
- Given a page where Marker or MinerU times out/errors
- When selection runs
- Then the pipeline scores the remaining engine or emits a placeholder if both fail
- And diagnostics are recorded in the intermediate artifact

### ES2: Both engines fail
- Given a page where both engines fail or produce empty results
- When normalization runs
- Then a placeholder block is deterministically emitted
- And output remains well-formed and deterministic

## 4. Traceability Matrix
| ID | RFC reference | Test category |
|---|---|---|
| AC1 | [01_rfc.md §8.3](./01_rfc.md) | Unit + snapshot |
| AC2 | [01_rfc.md §4.1, §13](./01_rfc.md) | Fixture + corpus |
| AC3 | [01_rfc.md §4.1, §9.2](./01_rfc.md) | Unit/property |
| AC4 | [01_rfc.md §10.2–§10.3](./01_rfc.md) | Fixture |
| AC5 | [01_rfc.md §12](./01_rfc.md) | Snapshot |
| ES1 | [01_rfc.md §7.2, §8.3, §13](./01_rfc.md) | Fixture |
| ES2 | [01_rfc.md §8.3, §13](./01_rfc.md) | Unit |

## 5. Quality Gates
- Determinism: repeated parses on fixed fixtures produce identical intermediate + `ParsedDocument`.
- Coverage: scan-heavy fixtures produce non-empty per-page output (or placeholders) without failing whole doc.
- Provenance completeness: 100% of blocks carry required provenance fields.

