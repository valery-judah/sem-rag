Now I have all the context. Here's the complete updated workplan with all the details needed to prompt another agent:

```markdown
# Workplan: Hybrid PDF Pipeline Wiring

**Status:** Draft
**Last updated:** 2026-03-04

## Summary
Implement `run_pdf_pipeline()` and required wiring so that PDFs can be parsed via hybrid engines
behind a feature flag, with deterministic intermediate artifacts and stable distillation outputs.

## Architecture Overview
```

Engine A (Marker) ???
                    ???? Per-Page Selection ??? ExtractedPdfDocument ??? Distill ??? ParsedDocument
Engine B (MinerU) ???
```
## Reference Documents
- **Context:** `docs/features/pdf-pipeline/00_context.md`
- **RFC (this feature):** `docs/features/pdf-pipeline/01_rfc.md`
- **User Stories:** `docs/features/pdf-pipeline/02_user_stories.md`
- **Design:** `docs/features/pdf-pipeline/03_design.md`
- **Test Plan:** `docs/features/pdf-pipeline/05_test_plan.md`
- **Hybrid Parsers RFC:** `docs/features/hybrid-parsers/01_rfc.md` (intermediate schema, selection algorithm)
- **Parsers RFC:** `docs/features/parsers/01_rfc.md` (ParsedDocument contract)

---

## PR Plan (phased, with exit criteria)

### PR1: Feature docs (this directory)
**Scope:**
- Add `docs/features/pdf-pipeline/` feature artifact set.
- Cross-link to:
  - `docs/features/hybrid-parsers/01_rfc.md`
  - `docs/features/parsers/01_rfc.md`
  - `docs/features/e2e/*`

**Exit criteria:**
- Docs are internally consistent and reference real code paths.

**Checks:**
- Docs-only.

---

### PR2: Config, models, and safe byte materialization
**Scope:**
- Modify `src/docforge/parsers/default.py` to materialize PDF bytes once and rewrap `RawDocument`
  for pipeline (see Design �3 for stream-drain safety).
- Extend `ParserConfig` to include `pdf_hybrid: PdfHybridConfig`.
- Add `pypdf` dependency to `pyproject.toml`.
- Add intermediate schema models in `src/docforge/parsers/pdf_hybrid/models.py`:
  - `PdfHybridConfig`:
    - `marker_timeout_s: int = 120`
    - `mineru_timeout_s: int = 180`
    - `selection_weights: SelectionWeights`
    - `force_engine: str | None = None`
    - `emit_artifacts: bool = True`
    - `artifact_dir: str = "artifacts/pdf_hybrid_pipeline"`
    - `require_any_engine: bool = True`
  - `SelectionWeights`:
    - `w_chars: float = 1.0`
    - `w_blocks: float = 0.2`
    - `w_dupes: float = 2.0`
    - `w_coords: float = 0.3`
    - `w_headings: float = 0.2`
    - `w_assets: float = 0.1`
  - `ExtractedPdfDocument` (per hybrid-parsers RFC �9.1):
    - `doc_id: str`
    - `source_pdf: SourcePdfInfo` (content_hash, page_count, metadata)
    - `pipeline: PipelineInfo` (pipeline_version, config_hash)
    - `engine_runs: list[EngineRun]`
    - `pages: list[ExtractedPage]`
  - `ExtractedPage`:
    - `page_idx: int`
    - `width: float`, `height: float`
    - `selected_engine: str`
    - `selection_reason: str`
    - `blocks: list[ExtractedBlock]`
    - `assets: list[ExtractedAsset]`
    - `diagnostics: dict`
  - `ExtractedBlock` (per hybrid-parsers RFC �9.2):
    - `block_id: str`
    - `type: Literal["heading", "para", "list", "table", "code", "caption", "footer", "header", "unknown"]`
    - `text: str`
    - `page_idx: int`
    - `bbox: tuple[float, float, float, float] | None`
    - `poly: list[tuple[float, float]] | None`
    - `reading_order_key: str`
    - `source: BlockSource` (engine, engine_artifact_ref, engine_block_ref)
    - `confidence: float`
    - `metadata: dict`
  - `ExtractedAsset` (per hybrid-parsers RFC �9.3)
  - `EngineRun`:
    - `engine: Literal["marker", "mineru"]`
    - `engine_version: str`
    - `engine_config_hash: str`
    - `engine_artifact_ref: str`
    - `status: Literal["ok", "partial", "error", "timeout", "unavailable"]`
  - `PageCandidate`:
    - `page_idx: int`
    - `blocks: list[ExtractedBlock]`
    - `assets: list[ExtractedAsset]`
    - `signals: CandidateSignals`
    - `status: Literal["ok", "empty", "error", "timeout"]`
  - `CandidateSignals` (per hybrid-parsers RFC �8.2):
    - `char_count: int`
    - `block_count: int`
    - `line_count: int`
    - `duplicate_line_ratio: float`
    - `heading_like_count: int`
    - `has_coords: bool`
    - `asset_count: int`
- Add exception types in `src/docforge/parsers/pdf_hybrid/exceptions.py` (per Design �5.1):
  - `PdfHybridPipelineError(Exception)` ? base class
  - `PdfHybridPipelineUnavailable(PdfHybridPipelineError)` ? no engines available
  - `EngineTimeoutError(PdfHybridPipelineError)` ? engine exceeded timeout
  - `EngineProcessError(PdfHybridPipelineError)` ? engine crashed or non-zero exit
  - `AdapterParseError(PdfHybridPipelineError)` ? engine output malformed

**Exit criteria:**
- PDF pipeline failures no longer cause empty fallback due to drained streams.
- All intermediate models validate with Pydantic (test with sample data).
- Exception hierarchy is importable and tested.
- `ParserConfig.pdf_hybrid` is accessible with defaults.

**Checks:**
- `make fmt`, `make lint`, `make type`, `make test`.

**New files:**
```

src/docforge/parsers/pdf_hybrid/
??? __init__.py
??? models.py
??? exceptions.py
tests/parsers/pdf_hybrid/
??? __init__.py
??? test_models.py
??? test_exceptions.py
```
---

### PR3: Engine runner layer + adapters
**Scope:**
- Add internal runner modules:
  - `src/docforge/parsers/pdf_hybrid/engines/__init__.py`
  - `src/docforge/parsers/pdf_hybrid/engines/_subprocess.py`:
    - `run_subprocess(cmd, timeout_s, cwd) -> SubprocessResult`
    - `SubprocessResult`: stdout, stderr, return_code, timed_out
  - `src/docforge/parsers/pdf_hybrid/engines/run_manifest.py`:
    - `EngineRunManifest`: engine, version, config_hash, artifact_dir, status, timing
  - `src/docforge/parsers/pdf_hybrid/engines/marker_cli.py`:
    - `discover_marker_binary() -> str | None`
    - `get_marker_version(binary_path) -> str | None`
    - `run_marker(pdf_path, output_dir, timeout_s) -> EngineRunManifest`
  - `src/docforge/parsers/pdf_hybrid/engines/mineru_cli.py`:
    - `discover_mineru_binary() -> str | None`
    - `get_mineru_version(binary_path) -> str | None`
    - `run_mineru(pdf_path, output_dir, timeout_s) -> EngineRunManifest`
- Implement engine discovery (per Design �5.2):
  - Marker: `tools/marker/.venv/bin/marker_single` ? fallback `marker` on PATH
  - MinerU: `tools/mineru/.venv/bin/mineru`
- Implement version detection (`--version` parsing).
- Implement timeout handling:
  - Use `subprocess.run(..., timeout=timeout_s)`
  - Catch `subprocess.TimeoutExpired` ? raise `EngineTimeoutError`
  - Catch non-zero exit ? raise `EngineProcessError`
- Add output adapters:
  - `src/docforge/parsers/pdf_hybrid/adapters/__init__.py`
  - `src/docforge/parsers/pdf_hybrid/adapters/marker_adapter.py`:
    - `adapt_marker_output(raw_json: dict, artifact_ref: str, page_count: int) -> list[PageCandidate]`
    - Parse Marker's JSON output format into `PageCandidate` list
    - Map Marker block types to canonical types
    - Extract bbox coordinates
    - Compute `reading_order_key` from native order
  - `src/docforge/parsers/pdf_hybrid/adapters/mineru_adapter.py`:
    - `adapt_mineru_output(raw_json: dict, artifact_ref: str, page_count: int) -> list[PageCandidate]`
    - Parse MinerU's JSON output format into `PageCandidate` list
    - Map MinerU block types to canonical types
    - Handle MinerU's coordinate system
- Adapters MUST handle malformed input gracefully ? raise `AdapterParseError`

**Exit criteria:**
- Runner code is unit-tested without requiring real engines (mock subprocess).
- Adapters are tested with fixture JSON files representing real engine output schemas.
- Version detection returns `None` gracefully when engine unavailable.
- Timeout handling raises `EngineTimeoutError` with appropriate message.
- Process errors raise `EngineProcessError` with stderr captured.
- Local manual run works when tools are provisioned.

**Checks:**
- `make fmt`, `make lint`, `make type`, `make test`.

**New files:**
```

src/docforge/parsers/pdf_hybrid/
??? engines/
?   ??? __init__.py
?   ??? _subprocess.py
?   ??? run_manifest.py
?   ??? marker_cli.py
?   ??? mineru_cli.py
??? adapters/
    ??? __init__.py
    ??? marker_adapter.py
    ??? mineru_adapter.py
tests/parsers/pdf_hybrid/
??? engines/
?   ??? test_subprocess.py
?   ??? test_marker_cli.py
?   ??? test_mineru_cli.py
??? adapters/
?   ??? test_marker_adapter.py
?   ??? test_mineru_adapter.py
??? fixtures/
    ??? marker_output_sample.json
    ??? mineru_output_sample.json
```
---

### PR4a: Selection logic and placeholder policy
**Scope:**
- Implement selection module `src/docforge/parsers/pdf_hybrid/selection.py`:
  - `compute_signals(candidate: PageCandidate) -> CandidateSignals`:
    - Count non-whitespace chars across all blocks
    - Count blocks, lines
    - Compute duplicate line ratio (normalize lines, count dupes)
    - Count heading-like blocks
    - Check if majority of blocks have coordinates
    - Count assets
  - `score_candidate(candidate: PageCandidate, weights: SelectionWeights) -> float`:
    - Implement scoring formula from hybrid-parsers RFC �8.3:
      ```python
      score = (
          weights.w_chars * math.log1p(signals.char_count)
          + weights.w_blocks * math.log1p(signals.block_count)
          - weights.w_dupes * signals.duplicate_line_ratio
          + weights.w_coords * (1.0 if signals.has_coords else 0.0)
          + weights.w_headings * math.log1p(signals.heading_like_count)
          + weights.w_assets * math.log1p(signals.asset_count)
      )
      ```
  - `run_selection(page_candidates: dict[int, dict[str, PageCandidate]], config: PdfHybridConfig) -> list[SelectionResult]`:
    - For each page (0 to page_count-1):
      - If only one candidate has `status=ok` ? select it
      - If both ok ? score both, select higher; tie-break: marker > mineru
      - If both failed ? emit placeholder
    - Return `SelectionResult` per page: `page_idx`, `selected_engine`, `selection_reason`, `scores`
  - `SelectionResult`:
    - `page_idx: int`
    - `selected_engine: Literal["marker", "mineru", "placeholder"]`
    - `selection_reason: str` (e.g., "score:marker=2.5,mineru=1.8", "single:marker", "placeholder:all_engines_failed")
    - `marker_score: float | None`
    - `mineru_score: float | None`
- Implement placeholder emission (per Design �5.4 and hybrid-parsers RFC �13):
  - `create_placeholder_block(page_idx: int) -> ExtractedBlock`:
    ```python
    ExtractedBlock(
        block_id=f"placeholder_{page_idx}",
        type="unknown",
        text=f"[UNPARSEABLE PAGE {page_idx + 1}]",
        page_idx=page_idx,
        bbox=None,
        poly=None,
        reading_order_key="0000",
        source=BlockSource(engine="placeholder", engine_artifact_ref=None, engine_block_ref=None),
        confidence=0.0,
        metadata={"placeholder_reason": "all_engines_failed"}
    )
    ```

**Exit criteria:**
- Selection is deterministic given identical inputs (verified by repeated runs).
- Placeholder blocks match schema in Design �5.4.
- Unit tests cover all selection scenarios:
  - Single engine ok (marker only, mineru only)
  - Both ok, marker wins by score
  - Both ok, mineru wins by score
  - Both ok, tie ? marker wins (tie-breaker)
  - Both failed ? placeholder
  - Mixed statuses (one ok, one error/timeout/empty)

**Checks:**
- `make fmt`, `make lint`, `make type`, `make test`.

**New files:**
```

src/docforge/parsers/pdf_hybrid/
??? selection.py
tests/parsers/pdf_hybrid/
??? test_selection.py
```
---

### PR4b: Pipeline assembly + distillation
**Scope:**
- Implement `run_pdf_pipeline()` in `src/docforge/parsers/pdf_hybrid/pipeline.py` (per Design �4):
  1. **Drain bytes** from `doc.content_stream` ? `pdf_bytes`
  2. **Compute content_hash**: `hashlib.sha256(pdf_bytes).hexdigest()`
  3. **Compute page_count**: `len(pypdf.PdfReader(io.BytesIO(pdf_bytes)).pages)`
  4. **Resolve artifact paths**:
     - `safe_doc_id = doc.doc_id if is_fs_safe(doc.doc_id) else sha256(doc.doc_id)[:32]`
     - `config_hash = sha256(canonical_json({pipeline_version, config, engine_versions}))`
     - `run_id = f"{PIPELINE_VERSION}_{content_hash[:16]}_{config_hash[:16]}"`
     - `doc_dir = Path(config.pdf_hybrid.artifact_dir) / safe_doc_id / run_id`
  5. **Stage PDF** to temp file for engine CLIs (use `tempfile.NamedTemporaryFile`)
  6. **Check engine availability** (per Design �5.2):
     - Call `discover_marker_binary()`, `discover_mineru_binary()`
     - If neither available and `require_any_engine=True` ? raise `PdfHybridPipelineUnavailable`
  7. **Run engines sequentially** (MVP; inject runners for testing):
     - `marker_result = run_marker(pdf_path, doc_dir / "engine_artifacts/marker", config.marker_timeout_s)`
     - `mineru_result = run_mineru(pdf_path, doc_dir / "engine_artifacts/mineru", config.mineru_timeout_s)`
     - Catch `EngineTimeoutError`, `EngineProcessError` ? record status, continue
  8. **Load and adapt outputs**:
     - `marker_candidates = adapt_marker_output(...)` (or empty list on failure)
     - `mineru_candidates = adapt_mineru_output(...)` (or empty list on failure)
  9. **Build page_candidates dict**: `{page_idx: {"marker": candidate, "mineru": candidate}}`
  10. **Run selection**: `selection_results = run_selection(page_candidates, config)`
  11. **Assemble ExtractedPdfDocument**:
      - Build `engine_runs[]` from manifests
      - Build `pages[]` from selection results + selected candidates (or placeholders)
  12. **Emit artifacts** if `config.emit_artifacts`:
      - `doc_dir / "selection_log.jsonl"`: one JSON line per page with selection details
      - `doc_dir / "extracted_pdf_document.json"`: full intermediate
      - `doc_dir / "parsed_document.json"`: after distillation
  13. **Cleanup**: delete temp PDF file (use context manager / finally)
  14. **Return** `ExtractedPdfDocument`

- Implement distillation in `src/docforge/parsers/pdf_hybrid/distill.py` (per hybrid-parsers RFC �10):
  - `distill_pdf(extracted: ExtractedPdfDocument, config: ParserConfig) -> ParsedDocument`:
    1. **Build canonical_text** (per RFC �10.3):
       - Iterate pages by `page_idx`
       - Within page, iterate blocks by `reading_order_key`
       - Join blocks with `\n\n`
       - Join pages with `\n\n\f\n\n` (form feed delimiter)
    2. **Compute ranges**: track `[start, end)` offset for each block as text is built
    3. **Build structure_tree** (per RFC �10.4):
       - Root `doc` node
       - `heading` blocks ? heading nodes with level
       - Other blocks ? leaves under most recent heading (or root)
    4. **Compute anchors** (per RFC �10.6):
       - `doc_anchor = sha256(doc_id)`
       - `sec_anchor = sha256(doc_id + normalized_section_path)`
       - `pass_anchor = sha256(sec_anchor + block_type + ordinal)`
    5. **Build metadata**:
       - `pdf_pipeline_version`
       - `selected_engine_counts`
       - `intermediate_artifact_ref`
    6. **Return** `ParsedDocument`

- Wire into `DeterministicParser.parse()` in `src/docforge/parsers/default.py`:
  ```python
  if config.enable_hybrid_pdf_pipeline and doc.content_type == "application/pdf":
      # Materialize bytes once (stream-drain safety)
      pdf_bytes = b"".join(doc.content_stream)
      rewrapped_doc = RawDocument(..., content_stream=iter([pdf_bytes]))
      try:
          extracted = run_pdf_pipeline(rewrapped_doc, config)
          return distill_pdf(extracted, config)
      except PdfHybridPipelineUnavailable:
          # Fall back to legacy with already-materialized bytes
          rewrapped_doc = RawDocument(..., content_stream=iter([pdf_bytes]))
          return self._legacy_parse(rewrapped_doc, config)
  ```

**Exit criteria:**
- CI tests pass without real engines (inject fake runners returning fixture data).
- `ExtractedPdfDocument` validates against Pydantic model.
- `ParsedDocument` passes strict invariants from parsers RFC.
- Determinism test: run pipeline twice with identical inputs ? byte-identical artifacts.
- Temp files are cleaned up (verify in tests: no temp files left after run).
- Artifact files are created in correct structure when `emit_artifacts=True`.
- Stream-drain safety: pipeline failure doesn't break fallback parsing.

**Checks:**
- `make fmt`, `make lint`, `make type`, `make test`.

**New/modified files:**
```

src/docforge/parsers/pdf_hybrid/
??? pipeline.py (implement run_pdf_pipeline)
??? distill.py (new)
src/docforge/parsers/
??? default.py (modify to wire hybrid pipeline)
tests/parsers/pdf_hybrid/
??? test_pipeline.py
??? test_distill.py
??? test_determinism.py
??? test_stream_drain_safety.py
```
---

### PR5: Local-only real engine smoke path (not in CI)
**Scope:**
- Wire default `run_pdf_pipeline()` to use real subprocess runners (production path).
- Create `docs/features/pdf-pipeline/LOCAL_SMOKE.md` with:
  - **Prerequisites**:
    - Python 3.11+
    - `uv` installed
    - GPU recommended for MinerU (CPU fallback documented)
  - **Provisioning tools/marker/**:
    ```bash
    cd tools/marker
    uv venv
    uv pip install marker-pdf
    # Verify: tools/marker/.venv/bin/marker_single --version
    ```
  - **Provisioning tools/mineru/**:
    ```bash
    cd tools/mineru
    uv venv
    uv pip install mineru
    # Download models: mineru-download-models
    # Verify: tools/mineru/.venv/bin/mineru --version
    ```
  - **Running smoke test**:
    ```bash
    # With a sample PDF
    python -c "
    from docforge.parsers.default import DeterministicParser
    from docforge.parsers.pdf_hybrid.models import PdfHybridConfig
    
    config = ParserConfig(
        enable_hybrid_pdf_pipeline=True,
        pdf_hybrid=PdfHybridConfig(emit_artifacts=True)
    )
    parser = DeterministicParser(config)
    result = parser.parse(RawDocument(doc_id='test', content_type='application/pdf', content_stream=open('sample.pdf', 'rb')))
    print(result)
    "
    ```
  - **Expected artifacts** in `artifacts/pdf_hybrid_pipeline/test/<run_id>/`:
    - `engine_artifacts/marker/...`
    - `engine_artifacts/mineru/...`
    - `selection_log.jsonl`
    - `extracted_pdf_document.json`
    - `parsed_document.json`
  - **Troubleshooting**:
    - Timeout errors: increase `marker_timeout_s` / `mineru_timeout_s`
    - OOM: reduce page count, use smaller PDF, or use CPU-only mode
    - Missing models: run `mineru-download-models`
    - Engine not found: check `tools/*/` venv paths
- Add sample PDF for testing: `tests/fixtures/sample_2page.pdf` (or document where to get one)

**Exit criteria:**
- On a machine with tool envs provisioned and models available, hybrid parsing produces all expected artifacts.
- `parsed_document.json` validates under strict invariants.
- LOCAL_SMOKE.md is complete and tested by a human.

**Checks:**
- `make test` (CI ? no real engines, tests still pass).
- Manual local smoke step per LOCAL_SMOKE.md.

**New files:**
```

docs/features/pdf-pipeline/
??? LOCAL_SMOKE.md
```
---

## Dependency Graph
```

PR1 (docs)
 ?
 ?
PR2 (config, models, exceptions)
 ?
 ?
PR3 (runners, adapters)
 ?
 ?????????????????????
 ?                   ?
PR4a (selection)    PR4b (pipeline, distill)
 ?                   ?
 ?????????????????????
           ?
         PR5 (real engine smoke)
```
> **Note:** PR4a and PR4b can be developed in parallel after PR3 merges. PR4b imports from PR4a
> for selection, so either:
> - Merge PR4a first, then PR4b
> - Or PR4b can stub selection and integrate after PR4a merges

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PR4b too large | Medium | Delays | Split into PR4b (pipeline) + PR4c (distill) if needed |
| Engine output schema changes | Medium | Adapter breaks | Pin engine versions in test fixtures; add schema validation in adapters |
| Timeout tuning varies by hardware | Low | False failures | Document defaults; make configurable; add guidance in LOCAL_SMOKE.md |
| Memory pressure on large PDFs | Low | OOM | Document size limits; consider streaming in future enhancement |
| Marker/MinerU non-determinism | Medium | Flaky tests | Pin versions; record engine_config_hash; use snapshot tests with tolerance |

---

## Definition of Done
- [ ] `run_pdf_pipeline()` fully implemented and deterministic.
- [ ] Parsing PDFs with `enable_hybrid_pdf_pipeline=True` yields valid `ParsedDocument`.
- [ ] Artifacts are reproducible and provenance-complete when `emit_artifacts=True`.
- [ ] Placeholder blocks emitted for pages where all engines fail.
- [ ] Exception types used consistently for all failure modes.
- [ ] No unrelated files modified.
- [ ] All tests pass in CI without requiring real engines.
- [ ] Local smoke path documented in LOCAL_SMOKE.md and validated manually.
- [ ] All new code has type hints and passes `make type`.
- [ ] All new code is formatted and passes `make lint`.
```
