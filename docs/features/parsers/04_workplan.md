# Workplan: Structural Parsers (Phase 1)

## 1. Milestone Mapping
- Maps to `docs/phase-1.md` §3.2 **Structural Parser & Distiller** and §3.3 **Hierarchical Segmenter**.
- Supports Phase 1 invariants in `docs/phase-1.md` §2:
  - stable identity
  - anchorability
  - hierarchical integrity
  - deterministic segmentation

## 2. Scope (MVP)
Implement parser capabilities needed to transform `RawDocument` into canonical, anchorable, segmented content:
1. Canonicalization by content type (`text/plain`, `text/markdown`, `text/html`, `application/pdf`)
2. Structure extraction (headings, lists, tables, code blocks)
3. Anchor generation (`doc`, `section`, `block/passage`)
4. Hierarchical segmentation into `SECTION` and `PASSAGE` nodes
5. Deterministic output contracts suitable for downstream augmentor/indexing stages

Out of scope for this workplan:
- Retrieval/index serving
- Runtime orchestration/retry logic
- Graph extraction prompt quality tuning

## 3. Dependency Order
1. Data contracts and parser interfaces
2. Canonicalization adapters by format
3. Structure tree extraction + anchor strategy
4. Segmenter implementation + special handling (tables/code)
5. CLI wiring/artifact output for parser stage
6. Tests, fixtures, and contract validation

## 4. PR Plan with Exit Criteria

Progress status (as of 2026-03-03):
- PR1: done
- PR2: done
- PR3: done
- PR4: done
- PR5: pending

### PR1: Contracts + parser pipeline skeleton (Done 2026-03-03)
Scope:
- Add/confirm typed models for:
  - `ParsedDocument`
  - `StructureNode`
  - `AnchorRef`
  - `Segment` (`SECTION|PASSAGE`)
- Define parser interfaces:
  - `Canonicalizer`
  - `StructureExtractor`
  - `Segmenter`
- Add pipeline entrypoint (composition only; minimal logic)

Touched modules (expected):
- `src/.../models/`
- `src/.../parsers/`

Implemented modules:
- `src/docforge/models/parser.py`
- `src/docforge/models/__init__.py`
- `src/docforge/models/raw_document.py`
- `src/docforge/parsers/interfaces.py`
- `src/docforge/parsers/pipeline.py`
- `src/docforge/parsers/__init__.py`

Acceptance checks:
- [x] Pipeline imports cleanly and can construct no-op/default components
- [x] Contracts encode parent/child segment relationships and anchor fields

Required tests:
- [x] Model serialization/deserialization tests
- [x] Interface contract test (minimal fake implementation)

Implemented tests:
- `tests/test_models_parser.py`
- `tests/test_parsers_pipeline.py`

Exit criteria:
- [x] `make type` passes
- [x] `make test` passes

### PR2: Canonicalization adapters (plain/markdown/html/pdf) (Done 2026-03-03)
Scope:
- Implement canonical text conversion to UTF-8
- Normalize newline behavior while preserving code block content
- Preserve heading order and body text fidelity
- For PDF, use deterministic extraction settings and explicit fallback behavior

Touched modules (expected):
- `src/.../parsers/canonicalize_*.py`
- `src/.../parsers/registry.py`

Implemented modules:
- `src/docforge/parsers/canonicalize_common.py`
- `src/docforge/parsers/canonicalize_plain.py`
- `src/docforge/parsers/canonicalize_markdown.py`
- `src/docforge/parsers/canonicalize_html.py`
- `src/docforge/parsers/canonicalize_pdf.py`
- `src/docforge/parsers/errors.py`
- `src/docforge/parsers/registry.py`

Acceptance checks:
- [x] Identical bytes + metadata produce identical canonical text
- [x] Unsupported/empty content types return explicit typed error paths

Required tests:
- [x] Format-specific fixture tests (`.txt`, `.md`, `.html`, `.pdf`)
- [x] Determinism test (repeat run produces byte-identical canonical output)

Implemented tests:
- `tests/test_parsers_canonicalization.py`
- `tests/fixtures/parsers/sample.txt`
- `tests/fixtures/parsers/sample.md`
- `tests/fixtures/parsers/sample.html`
- `tests/fixtures/parsers/sample.pdf`

Exit criteria:
- [x] `make fmt` passes
- [x] `make lint` passes
- [x] `make type` passes
- [x] `make test` passes

### PR3: Structure extraction + anchors (Done 2026-03-03)
Scope:
- Build structure tree with nodes for headings, paragraphs, lists, tables, code
- Generate:
  - `doc_anchor`
  - stable `sec_anchor` from section path/slug strategy
  - `block_anchor` / passage-range anchors
- Add collision-safe anchor normalization rules

Touched modules (expected):
- `src/.../parsers/structure.py`
- `src/.../parsers/anchors.py`

Implemented modules:
- `src/docforge/parsers/structure.py`
- `src/docforge/parsers/anchors.py`
- `src/docforge/parsers/pipeline.py`
- `src/docforge/parsers/__init__.py`

Acceptance checks:
- Heading hierarchy is preserved
- Tables preserve header semantics in serialized text
- Code blocks preserve verbatim content boundaries
- Anchors resolve uniquely within document scope

Required tests:
- Golden tests for structure tree outputs
- Anchor uniqueness/collision tests
- Regression tests for repeated headings with identical titles

Implemented tests:
- `tests/test_parsers_structure.py`
- `tests/test_parsers_pipeline.py`

Exit criteria:
- [x] `make lint` passes
- [x] `make type` passes
- [x] `make test` passes

### PR4: Hierarchical segmenter (Done 2026-03-03)
Scope:
- Implement section boundary detection from structure tree
- Implement passage splitting with configurable token target (300–800) and overlap (0–15%)
- Add table-aware and code-aware splitting policy:
  - keep full block when feasible
  - otherwise split by rows/logical boundaries with repeated context headers

Touched modules (expected):
- `src/.../parsers/segmenter.py`
- `src/.../config.py` (parser/segmenter tunables)

Implemented modules:
- `src/docforge/parsers/segmenter.py`
- `src/docforge/parsers/pipeline.py`
- `src/docforge/parsers/__init__.py`
- `src/docforge/config.py`

Acceptance checks:
- [x] Segment DAG is cycle-free and parent pointers are valid
- [x] `segment_id` stability guaranteed for identical doc version input
- [x] Token window constraints respected within tolerance

Required tests:
- [x] Segment contract tests (parent/child integrity)
- [x] Determinism tests for segment IDs
- [x] Edge-case fixtures: long tables, long code blocks, no headings

Implemented tests:
- `tests/test_parsers_segmenter.py`
- `tests/test_config.py`

Exit criteria:
- [x] `make fmt` passes
- [x] `make lint` passes
- [x] `make type` passes
- [x] `make test` passes

### PR5: Parser CLI stage + persisted artifacts
Scope:
- Add parser-stage command (or subcommand wiring) to emit parse artifacts
- Emit machine-readable artifacts for parsed docs + segments
- Include doc-level run metadata (version, timestamp, parser profile)

Touched modules (expected):
- `src/.../cli.py`
- `src/.../parsers/pipeline.py`

Acceptance checks:
- Running parser stage on fixture corpus writes expected artifact set
- Artifact schema remains backward compatible for downstream consumers

Required tests:
- CLI integration test with fixture corpus
- Artifact schema validation test

Exit criteria:
- `make check` passes

## 5. Test Strategy
- Unit tests for each parser component (canonicalization, structure, anchors, segmentation)
- Contract tests for parser output schema and stability guarantees
- Integration test for end-to-end parser pipeline on a small mixed-format fixture corpus
- Determinism tests run at least twice per fixture and compare normalized outputs

## 6. Risks and Mitigations
- Risk: nondeterministic PDF/text extraction ordering
  - Mitigation: pin extraction backend/config and normalize deterministic ordering rules.
- Risk: anchor churn due to heading edits
  - Mitigation: version-aware anchor derivation and explicit traceability metadata.
- Risk: token counting drift across tokenizer versions
  - Mitigation: pin tokenizer dependency and record tokenizer version in metadata.
- Risk: oversized table/code passages degrade retrieval
  - Mitigation: fallback split policies with repeated headers/context.

## 7. Command Checklist (for implementation PRs)
1. `make sync`
2. `make install`
3. `make fmt`
4. `make lint`
5. `make type`
6. `make test`

## 8. Definition of Done
1. Parser pipeline satisfies Phase 1 parser + segmenter contracts.
2. Deterministic behavior is proven in automated tests.
3. Anchor and hierarchy guarantees are validated by tests.
4. Parser artifacts are consumable by downstream augmentor/indexing stages.
5. `docs/features/parsers/` documents are aligned with implementation.
