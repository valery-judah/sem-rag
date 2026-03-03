# Workplan: Connectors (MVP-1 Local PDF)

## 1. Milestone Mapping
- Maps to `docs/phase-1.md` **M1** (“Implement connectors for 1-2 sources”), constrained to **one local PDF**.

## 2. Dependency Order
1. Models + config
2. Connector implementation
3. CLI command
4. Tests + checks

## 3. PR Plan with Exit Criteria
### PR1: Add models + config loader
Scope:
- Add `RawDocument` pydantic models (and timestamps type)
- Add TOML config loader using stdlib `tomllib`

Touched modules:
- `src/docforge/models/`
- `src/docforge/config.py`

Acceptance checks:
- Package imports cleanly
- Config loads the example `[[sources]]` shape from `01_rfc.md` §2.1

Required tests:
- Unit test for config parsing

Rollback/mitigation:
- Keep models/config isolated so removal is a clean revert if needed

Exit criteria:
- `make type` passes
- `make test` passes

### PR2: Implement `local_file` connector
Scope:
- Implement `LocalFileConnector` to produce `RawDocument`
- Implement incremental `since` filter using `timestamps.updated_at`

Touched modules:
- `src/docforge/connectors/`

Acceptance checks:
- Deterministic `RawDocument` fields for unchanged config + file
- Correct `content_type` resolution per `03_design.md` §3.1

Required tests:
- Connector contract test
- Incremental filter test

Rollback/mitigation:
- Keep connector registry isolated to allow future source types without refactors

Exit criteria:
- `make type` passes
- `make test` passes

### PR3: Add `docforge connect`
Scope:
- Add CLI subcommand `docforge connect`
- Emit artifacts:
  - `raw/<doc_key>.json` (metadata only)
  - `blobs/<doc_key>.bin` (raw bytes)
- Compute and store `content_sha256` and print a one-line summary per doc

Touched modules:
- `src/docforge/cli.py`
- `src/docforge/connectors/` (wiring only)

Acceptance checks:
- Running `docforge connect` produces both artifact files for the PDF
- Sidecar `content_sha256` matches blob bytes

Required tests:
- CLI connect test validates file creation + hash match

Rollback/mitigation:
- Keep CLI subcommand isolated; do not change existing `--version` semantics

Exit criteria:
- `make check` passes

## 4. Test Strategy by Phase
- MVP-1 uses unit tests + a focused CLI test only (no snapshots yet).

## 5. Risks and Mitigations
- Risk: timestamp differences across platforms/filesystems
  - Mitigation: compare normalized UTC timestamps or compare within second precision in tests.

## 6. Command Checklist
1. `make fmt`
2. `make lint`
3. `make type`
4. `make test`

## 7. Definition of Done
1. Docs in this folder reflect the implemented behavior.
2. `01_rfc.md` is the authoritative connector contract.
3. All acceptance criteria in `02_user_stories.md` are covered by tests.
4. Required commands in §6 pass with no unrelated file changes.

