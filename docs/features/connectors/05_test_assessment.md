# Connectors Test Assessment vs RFC (`01_rfc.md`)

## Verdict
The current connector tests provide **good baseline coverage** for MVP-1, but they are **not sufficient to fully guarantee** all normative requirements in `01_rfc.md`.

## Coverage Matrix

| RFC requirement | Current coverage | Evidence | Gap / risk |
|---|---|---|---|
| Input schema supports required fields (`type`, `path`) and optional fields (`doc_id`, `url`, `content_type`, `metadata`, `acl_scope`) | Partial | `tests/test_config.py` validates load/parsing for these fields. | No explicit negative validation tests for malformed `[[sources]]` shapes/types. |
| Output schema contains required `RawDocument` fields | Strong | `test_local_file_connector_contract_fields_and_determinism` asserts every required field. | No explicit schema-level assertion for type errors or missing fields under faulty inputs. |
| `doc_id` policy: use config `doc_id` when provided | Partial | Covered indirectly via CLI sidecar assertion (`sample_pdf`). | No direct connector-level assertion proving configured `doc_id` overrides derived hash. |
| `doc_id` policy: derive `local_file:<sha256(source_ref_utf8)>` when absent | Strong | `test_local_file_connector_contract_fields_and_determinism`. | None notable for MVP-1. |
| `source_ref` equals configured path string as-given | Strong | Same connector contract test asserts exact `str(pdf_path)`. | No regression test for relative path preservation as literal string. |
| `url` default is `file:<source_ref>` unless configured | Partial | Default branch covered in connector contract test. | No test for configured `url` override path. |
| `timestamps.updated_at` from filesystem `mtime` in UTC; `created_at == updated_at` | Strong | Connector contract test sets mtime and compares both fields. | No test for timezone normalization when `since` is naive datetime. |
| Incremental filter (`since`) excludes docs when `updated_at <= since` | Strong | `test_local_file_connector_since_filter_excludes_older_update`. | Missing boundary-inclusive test for equality (`updated_at == since`) and include-case (`updated_at > since`). |
| Content type behavior | Strong | Explicit override + fallback tests; `.pdf` path in contract test. | Could add explicit non-PDF known extension expectation if desired. |
| Deterministic behavior for unchanged input/config | Partial | Repeated connector call equality asserted. | No end-to-end determinism check for emitted artifact filenames/order with >1 source. |
| CLI emission must include matching `content_sha256` and avoid inlining `content_bytes` | Strong | `tests/test_cli_connect.py` verifies hash and omitted bytes. | No multi-source ordering assertion for sidecar/blob emission sequence. |
| Ordering rules for future multi-source support | Not covered | N/A (MVP currently one document). | Gap is acceptable for MVP-1 but should be covered before multi-source rollout. |

## Recommended Test Improvements

### High Priority
1. Add connector test: **configured `doc_id` overrides default hash**.
2. Add connector test: **configured `url` override is preserved verbatim**.
3. Add incremental tests for `since` semantics:
   - include when `updated_at > since`
   - exclude when `updated_at == since` (boundary)
4. Add config validation tests for invalid/missing required source fields.

### Medium Priority
1. Add test for **relative path literal preservation** in `source_ref` and derived hash input.
2. Add test for **naive `since` normalization to UTC** (exercise `_normalize_utc`).
3. Add end-to-end CLI test with multiple `[[sources]]` ensuring deterministic emission order by config order.

### Future (pre multi-source connectors)
1. Add ordering contract tests for lexicographic `source_ref` within connector output.
2. Add tests that assert deterministic raw/blob filenames and stable sidecar ordering across reruns.

## Suggested Acceptance Gate
Before declaring full RFC compliance, require the connectors suite to pass an explicit checklist for:
- identity policy (`doc_id`, `source_ref`, `url`),
- timestamp/incremental semantics (including boundary cases),
- artifact integrity (`content_sha256` + no inlined bytes),
- deterministic output ordering (where applicable).
