# Workplan: Structural Parser & Distiller

## 1. Milestone Mapping
- Phase 1 M1 alignment: corpus ingestion + canonical parsing.
- Phase 1 M2 alignment: parser outputs stable anchors and hierarchy for segmenter consumption.

This workplan is parser-scoped (component 3.2) and uses [01_rfc.md](./01_rfc.md) as the contract source.

## 2. Dependency Order
1. PR1 contract scaffolding
2. PR2 canonicalization
3. PR3 structure extraction
4. PR4 ranges + anchors + edge policies
5. PR5 determinism + observability + corpus gates

No PR should proceed to merge without prior PR exit criteria satisfied.

## 3. PR Plan with Exit Criteria

### PR1: Contract Scaffolding (M1)
Scope:
- Define/align parser-side data models to RFC input/output contract.
- Define explicit tree node types and parser metadata fields.

Touched modules:
- `src/docforge/parsers/models.py`
- `src/docforge/parsers/base.py`
- parser config schema files

Acceptance checks:
- Required fields in RFC are representable in types.
- Serialization/deserialization roundtrip is stable.

Required tests:
- Model unit tests.
- Contract shape validation tests.

Rollback/mitigation:
- Keep old model adapters behind compatibility layer until downstream adoption is verified.

Exit criteria:
- Contract tests pass.
- No breaking import churn in downstream parser package users.

### PR2: Canonicalization Pipeline (M1)
Scope:
- Implement deterministic canonicalization by content type.
- Preserve code/table semantics during conversion.

Touched modules:
- `src/docforge/parsers/canonicalize.py`
- parser entrypoint implementation files

Acceptance checks:
- `canonical_text` UTF-8 correctness.
- Non-empty output for parser-eligible textual docs.

Required tests:
- HTML/Markdown/plain-text unit fixtures.
- Newline and whitespace normalization tests.

Rollback/mitigation:
- Feature-flag canonicalization backend strategy if conversion regressions occur.

Exit criteria:
- Canonicalization tests pass on fixture suite.
- No nondeterministic deltas between repeated runs.

### PR3: Structure Tree Extraction (M1)
Scope:
- Parse canonical text AST.
- Build heading/block hierarchy with deterministic ordering.

Touched modules:
- `src/docforge/parsers/tree_builder.py`
- AST integration utilities

Acceptance checks:
- Valid acyclic tree.
- Correct attachment for heading and non-heading blocks.

Required tests:
- Property tests for hierarchy integrity.
- Fixture tests for skipped levels and heading-free docs.

Rollback/mitigation:
- Retain fallback root attachment path for edge inputs.

Exit criteria:
- Tree property tests pass.
- Fixture set covers major edge scenarios.

### PR4: Ranges, Anchors, and Edge Policies (M2)
Scope:
- Implement block range derivation and anchor generation.
- Enforce duplicate heading tie-breakers and malformed table fallback policy.

Touched modules:
- `src/docforge/parsers/ranges.py`
- `src/docforge/parsers/anchors.py`
- parser orchestration layer

Acceptance checks:
- Every emitted block range resolves in `canonical_text`.
- Anchor uniqueness and determinism within document.

Required tests:
- Range resolvability property tests.
- Deterministic anchor tests with duplicate headings.
- Malformed-table fallback unit tests.

Rollback/mitigation:
- Keep previous anchor derivation behind temporary compatibility switch during migration window.

Exit criteria:
- Anchor/range test suite passes.
- Cross-check with user story AC mappings is complete.

### PR5: Determinism, Observability, and Quality Gates (M2)
Scope:
- Add parser observability events.
- Add golden corpus snapshots and acceptance reporting.

Touched modules:
- parser instrumentation files
- parser test corpus fixtures
- CI checks for parser quality gates

Acceptance checks:
- Snapshot determinism on golden corpus.
- Metrics for >= 99% non-empty canonical output in parser-eligible corpus.

Required tests:
- Snapshot tests.
- Pipeline event emission tests.

Rollback/mitigation:
- If snapshot churn is high, freeze parser version and regenerate baseline only after contract review.

Exit criteria:
- Determinism and quality gate checks pass in CI.
- Parser emits `DocParsed` and `PipelineError` events with required fields.

## 4. Test Strategy by Phase
- Contract tests: schemas/required fields match RFC.
- Unit tests: canonicalization, table/code handling, fallback paths.
- Property tests: hierarchy integrity, anchor/range resolvability.
- Snapshot tests: deterministic full-document outputs over fixed corpus.
- Corpus quality checks: parser success rate and non-empty-output KPI.

## 5. Risks and Mitigations
- Risk: HTML conversion drift due to parser/backend upgrades.
  - Mitigation: pin converter/parser versions and track parser version metadata.
- Risk: anchor churn from normalization changes.
  - Mitigation: versioned anchor policy, migration notes, snapshot diff review.
- Risk: malformed source documents causing unstable fallbacks.
  - Mitigation: explicit fallback rules + dedicated fixtures.

## 6. Command Checklist
Docs-only changes:
- Required: no mandatory runtime checks.
- Recommended: targeted consistency checks on links/terminology.

Code/API/parser logic changes in implementation PRs:
1. `make fmt`
2. `make lint`
3. `make type`
4. `make test`

## 7. Definition of Done
1. Parser docs and implementation align to RFC authority model.
2. User stories map to executable test categories.
3. Required parser quality gates are represented and enforced.
4. No parser responsibilities leak into connector/segmenter scopes.
5. No unrelated files are modified.
