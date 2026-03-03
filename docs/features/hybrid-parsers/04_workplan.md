# Workplan: Hybrid PDF Parsing Pipeline

## 1. Milestone Mapping
- Phase 1 alignment: improve `application/pdf` parsing robustness while preserving deterministic `ParsedDocument` outputs for downstream chunking.

This workplan is PDF-pipeline-scoped and uses [`./01_rfc.md`](./01_rfc.md) as the contract source, with [`../parsers/01_rfc.md`](../parsers/01_rfc.md) remaining authoritative for `ParsedDocument`.

## 2. Dependency Order
1. Implement engine wrappers + adapters (Marker, MinerU).
2. Implement deterministic selection and placeholder logic.
3. Implement intermediate schema emission + artifact/logging layout.
4. Implement distillation integration and determinism tests.

## 3. PR Plan with Exit Criteria

### PR1: Contract + Docs Alignment
Scope:
- Add hybrid-parsers feature artifact set (this directory).

Touched modules:
- `docs/features/hybrid-parsers/*`

Acceptance checks:
- No changes to `ParsedDocument` schema.

Required tests:
- Docs-only (no mandatory runtime tests).

Rollback/mitigation:
- Revert docs if necessary.

Exit criteria:
- Docs are internally consistent and links resolve.

### PR2: Engine Adapters
Scope:
- Implement adapters that map Marker and MinerU outputs to shared candidate/block models.

Touched modules:
- `src/docforge/parsers/pdf_hybrid/engines/*.py`
- `src/docforge/parsers/pdf_hybrid/models.py`

Acceptance checks:
- Each adapter produces stable, page-granular candidates with provenance fields.

Required tests:
- Unit tests for adapter normalization and provenance completeness.

Rollback/mitigation:
- Keep adapters behind a feature flag until selection + distillation is complete.

Exit criteria:
- Adapter unit tests pass and output models roundtrip deterministically.

### PR3: Selection and Scoring
Scope:
- Implement signals, scoring, and deterministic tie-breakers.
- Implement placeholder block emission for failed pages.

Touched modules:
- `src/docforge/parsers/pdf_hybrid/selection.py`
- `src/docforge/parsers/pdf_hybrid/config.py`

Acceptance checks:
- Same inputs/config yield identical `selected_engine_by_page`.

Required tests:
- Unit + snapshot tests for selection determinism.

Rollback/mitigation:
- Provide a config to force a single-engine path for emergency rollback.

Exit criteria:
- Determinism snapshots pass on a fixed PDF fixture set.

### PR4: Intermediate Schema + Artifact Emission
Scope:
- Emit `extracted_pdf_document.json` matching [`01_rfc.md §9`](./01_rfc.md).
- Emit `selection_log.jsonl` and per-engine artifact refs consistently.

Touched modules:
- `src/docforge/parsers/pdf_hybrid/artifacts.py`
- `src/docforge/parsers/pdf_hybrid/schema.py`

Acceptance checks:
- Artifacts are stable across runs for identical inputs/config.

Required tests:
- Snapshot tests for intermediate schema stability.

Rollback/mitigation:
- Allow disabling intermediate emission (for storage constraints) without changing `ParsedDocument`.

Exit criteria:
- Snapshot fixtures are stable and provenance is complete.

### PR5: Distillation Integration + End-to-End Fixtures
Scope:
- Distill intermediate output into canonical `ParsedDocument` (per [`../parsers/01_rfc.md`](../parsers/01_rfc.md)).
- Add PDF fixtures covering digital-born, scan-heavy, mixed layout cases.

Touched modules:
- `src/docforge/parsers/pdf_hybrid/distill.py`
- `src/docforge/parsers/default.py` (routing PDFs to hybrid pipeline behind a flag)
- `tests/` fixtures and integration tests (paths per repo conventions)

Acceptance checks:
- `ParsedDocument` determinism holds across repeated runs.
- Page delimiters and ordering are stable and versioned.

Required tests:
- Integration + snapshot tests for end-to-end PDF parsing.

Rollback/mitigation:
- Feature flag: keep existing PDF parsing path as fallback.

Exit criteria:
- `make fmt`, `make lint`, `make type`, `make test` all pass for implementation PRs.

## 4. Test Strategy by Phase

See [`05_test_plan.md`](./05_test_plan.md) for the comprehensive test and fixture strategy.

- Unit tests: adapters, scoring, cap logic, ordering keys.
- Snapshot tests: intermediate schema + selection logs + final `ParsedDocument` on fixed fixtures.
- Fixture suites: representative PDFs (multi-column, scanned, malformed).
- Property tests (optional): determinism and provenance completeness across randomized block orders.

## 5. Risks and Mitigations
- Risk: nondeterminism from engine updates.
  - Mitigation: pin versions; record `engine_version` and `engine_config_hash`; snapshot tests.
- Risk: ordering regressions on complex layouts.
  - Mitigation: fixture coverage; rely on engine native order; keep tie-breaks explicit.
- Risk: placeholder fallback on difficult PDFs.
  - Mitigation: since fallbacks are removed, pages failing both engines are lost. Monitor `selection_log.jsonl` to ensure failure rates remain acceptable.

## 6. Command Checklist
Implementation PRs (API/schema/logic changes):
1. `make fmt`
2. `make lint`
3. `make type`
4. `make test`

## 7. Definition of Done
1. Feature artifact set exists and is internally consistent.
2. [`./01_rfc.md`](./01_rfc.md) is authoritative for PDF pipeline invariants and intermediates.
3. Acceptance criteria map to tests/workplan steps.
4. Determinism and provenance requirements are enforced by fixtures/snapshots.
5. No unrelated files are modified.
