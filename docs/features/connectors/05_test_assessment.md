# Connectors Test Assessment vs RFC (`01_rfc.md`)

## Verdict
The connector implementation and test suite now satisfy the MVP-1 RFC requirements under the strict interpretation from the follow-up plan:
- Relative `path` values are resolved from the TOML config directory for file IO.
- `source_ref` is preserved exactly as configured.
- Default identity (`doc_id`) and URL policy are anchored to the preserved `source_ref` string.

## Coverage Matrix (Current State)

| RFC requirement | Coverage | Evidence |
|---|---|---|
| Input schema requires `type` and `path`; allows optional connector fields | Strong | `SourceConfig` defines required/optional schema, and config tests cover normal parsing plus missing required fields failing validation. |
| Relative path policy: resolve relative `path` from config directory for file IO | Strong | `load_config` sets `path_resolved` from `config_path.parent` and CLI test verifies relative path ingestion works when using `./input.pdf` in config. |
| `source_ref` preserved exactly as configured | Strong | Local connector uses `source.path` as `source_ref`; CLI relative-path test asserts literal `./input.pdf` is preserved. |
| `doc_id` policy: configured value wins; fallback hashes `source_ref` bytes | Strong | Connector contract test checks default hash behavior; CLI artifact test checks configured `doc_id` path; relative-path CLI test checks hash is based on literal `./input.pdf`. |
| `url` policy: configured value wins; fallback is `file:<source_ref>` | Strong | Dedicated connector test validates URL override; contract/CLI tests validate default URL behavior. |
| Required `RawDocument` output fields populated | Strong | Connector contract test asserts full required field set and deterministic equality across repeated runs. |
| Metadata and ACL defaults are `{}` when omitted | Strong | Dedicated connector test asserts empty-dict defaults for `metadata` and `acl_scope`. |
| Timestamp policy: `updated_at` from file `mtime` in UTC; `created_at == updated_at` | Strong | Contract test fixes mtime and asserts both timestamp values; dedicated test asserts UTC-aware tzinfo on both fields. |
| Incremental filter: exclude when `updated_at <= since`, include when `updated_at > since` | Strong | Connector tests validate exclusion for older/equal boundary and inclusion for newer updates. |
| CLI artifacts: sidecar JSON + blob, no inlined `content_bytes`, `content_sha256` matches blob | Strong | CLI tests assert sidecar/blob emission, SHA match, and no inlined content bytes. |
| Determinism for unchanged input/config | Strong (MVP-1 scope) | Connector test compares repeated runs for identical model output under unchanged input/config. |

## Gap Status vs Prior Assessment
The previously identified high-priority gaps have been closed for MVP-1:
1. URL override coverage: **closed**.
2. Relative-path config-dir resolution + literal `source_ref` preservation: **closed**.
3. Identity policy anchored to exact configured string (including `./`): **closed**.
4. Required field/default behavior checks for metadata/ACL: **closed**.
5. Missing required config field validation: **closed**.

## Remaining Notes (Non-Blocking for MVP-1)
- Multi-source ordering rules remain a forward-looking RFC rule and are not exercised in MVP-1’s single-document scope.

## Suggested Acceptance Gate
For MVP-1 connector RFC parity, keep the following checks green:
- `tests/test_connectors_local_file.py`
- `tests/test_cli_connect.py`
- `tests/test_config.py`

These tests jointly enforce schema handling, identity policy, timestamps/incremental behavior, and CLI artifact integrity.
