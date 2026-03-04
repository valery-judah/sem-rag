# Plan: MinerU CLI Runner (PR4)

## Context
The pdf-hybrid pipeline already has a Marker CLI runner. This PR adds an analogous MinerU runner following the same patterns, plus an ad-hoc script and tests. The design doc (`pr4_mineru_design.md`) is fully specified — this plan maps it to implementation steps.

## Files to create
1. `src/docforge/parsers/pdf_hybrid/engines/mineru_cli.py` — MineruRunner class
2. `scripts/run_mineru.py` — ad-hoc runner script
3. `tests/parsers/pdf_hybrid/test_mineru_cli.py` — unit tests

## Files to reuse (read-only)
- `engines/marker_cli.py` — structural template for the runner
- `engines/_subprocess.py` — `run_command()` shared helper
- `engines/run_manifest.py` — `EngineRunManifest` model
- `engines/miner_u.py` — `adapt_mineru_output()` adapter
- `scripts/run_marker.py` — template for the script
- `scripts/targets.json` — shared targets file

---

## Step 1: `mineru_cli.py` — MineruRunner

Mirror `marker_cli.py` structure with MinerU-specific logic from design doc sections 3–9.

### Key differences from MarkerRunner:
- **Discovery (§4):** two binary names (`mineru`, `magic-pdf`), env var `DOCFORGE_MINERU_BIN`, venv path `tools/mineru/.venv`
- **Version (§5):** try `--version`, fallback `-V`
- **Config injection (§6):** write `mineru_config.json` into output_dir, set `MINERU_TOOLS_CONFIG_JSON` env var. Config includes models-dir (modern vs legacy format), device-mode, table/formula/layout config, bucket_info, optional Gemini block
- **CLI flavor detection (§7):** check binary basename — `mineru` = modern, else = legacy `magic-pdf`. Different flags (`-b backend` vs `-m method`), different page range support (modern: `-s`/`-e` 0-based; legacy: not supported → error)
- **Output selection (§8):** `_select_mineru_json_payload()` — prefer `*_content_list.json`, then `*_middle.json`, then largest `.json` (excluding `mineru_config.json`)
- **Bridge (§9):** `load_and_adapt()` calls `adapt_mineru_output()`
- **Page range API:** `start_page`/`end_page` (0-based inclusive ints) instead of Marker's string `page_range`

### Implementation outline:
```
_select_mineru_json_payload(output_dir: Path) -> Path
_build_mineru_config(output_dir, binary_name, models_dir, device, env) -> Path
_is_modern_cli(binary_path: str) -> bool

class MineruRunner:
    __init__(override_binary_path, env_overrides)
    discover() -> str | None
    get_version() -> str | None
    is_available() -> bool
    run(pdf_path, output_dir, timeout_s, start_page, end_page) -> EngineRunManifest
    load_and_adapt(manifest) -> list[PageCandidate]
```

## Step 2: `scripts/run_mineru.py` — Ad-hoc script

Mirror `scripts/run_marker.py` with MinerU adaptations per §10:
- `--pdf` / `--targets` mutually exclusive args
- Page range conversion: targets.json 1-based → runner 0-based (`"37"` → start=36, end=36; `"37-38"` → start=36, end=37)
- Reject comma-separated ranges with clear error
- Legacy CLI + page range → record error, continue
- Output dirs: `output/mineru_test/{pdf_stem}_{clean_page_range}/`
- Print: binary + version, status, error details, artifact counts (`.json`, `.md` recursive)
- Default timeout: 300s

## Step 3: `tests/parsers/pdf_hybrid/test_mineru_cli.py` — Tests

Mirror `test_marker_cli.py` structure per §11:

### Test classes:
1. **TestMineruPayloadSelection** — `_content_list.json` preferred, `_middle.json` fallback, largest `.json` fallback, error if none
2. **TestMineruRunnerDiscovery** — override path, `DOCFORGE_MINERU_BIN`, venv `mineru`/`magic-pdf`, PATH `mineru`/`magic-pdf`
3. **TestMineruRunnerVersion** — semver from `--version` stdout, `-V` fallback, None on unparseable
4. **TestMineruRunnerRun** — ok (writes dummy `_content_list.json`), timeout, crash, unavailable, legacy+range → error
5. **TestMineruRunnerLoadAndAdapt** — ok manifest → calls `adapt_mineru_output`, non-ok → `[]`

### Mock boundaries:
- Patch `docforge.parsers.pdf_hybrid.engines.mineru_cli.run_command`
- Patch `os.environ`, `os.path.exists`, `pathlib.Path.exists`, `shutil.which`

---

## Verification
1. `python -m pytest tests/parsers/pdf_hybrid/test_mineru_cli.py -v` — all tests pass
2. `python -m pytest tests/ -v` — no regressions
3. (Manual, if MinerU installed) `python scripts/run_mineru.py --targets scripts/targets.json` — creates output dirs, prints results
