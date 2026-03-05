# Design: MinerU CLI Runner

**Status:** Proposed  
**Related PR:** PR4 of `docs/features/pdf-pipeline/04_workplan.md`  
**Last updated:** 2026-03-04  
**Context:** `docs/features/pdf-pipeline/03_design.md`, `docs/features/e2e/03_design.md`

## 1. Overview

This document specifies the design for introducing a MinerU CLI runner module (and an ad-hoc script runner) analogous to the existing Marker CLI runner.

Goals:
- Discover and run MinerU via subprocess with timeouts.
- Keep heavy MinerU dependencies isolated (tool venv under `tools/mineru/`), not in the main project env.
- Capture reproducible run metadata in `EngineRunManifest`.
- Load MinerU raw outputs and delegate parsing to the existing adapter:
  - `src/docforge/parsers/pdf_hybrid/engines/miner_u.py::adapt_mineru_output`

Non-goals:
- Running MinerU in CI (tests must be mock-based).
- Changing the MinerU adapter semantics beyond what’s required for loader compatibility.

## 2. Components

### 2.1. Existing shared modules (already present)
- `src/docforge/parsers/pdf_hybrid/engines/_subprocess.py`
  - `run_command(cmd, timeout_s, cwd=None, env=None) -> SubprocessResult`
- `src/docforge/parsers/pdf_hybrid/engines/run_manifest.py`
  - `EngineRunManifest` model (engine_name/status/version/binary_path/raw_output_dir/stdout/stderr/etc.)

### 2.2. New MinerU runner module (to add)
- `src/docforge/parsers/pdf_hybrid/engines/mineru_cli.py`
  - Implements:
    - binary discovery
    - version detection
    - subprocess execution
    - canonical output JSON selection
    - `load_and_adapt()` bridge to `adapt_mineru_output`

### 2.3. New ad-hoc script (to add)
- `scripts/run_mineru.py`
  - Mirrors `scripts/run_marker.py` behavior:
    - run on a single PDF (`--pdf`)
    - run a set of page-range targets from `scripts/targets.json` (`--targets`)
    - create per-target output dirs under `output/mineru_test/...`
    - print artifact counts and run status

## 3. Interfaces

### 3.1. MinerU runner interface
`MineruRunner` mirrors the shape of `MarkerRunner`:

```py
class MineruRunner:
    def __init__(
        self,
        override_binary_path: str | None = None,
        env_overrides: dict[str, str] | None = None,
    ): ...

    def discover(self) -> str | None: ...
    def get_version(self) -> str | None: ...
    def is_available(self) -> bool: ...

    def run(
        self,
        pdf_path: Path,
        output_dir: Path,
        timeout_s: float,
        *,
        start_page: int | None = None,  # 0-based inclusive
        end_page: int | None = None,    # 0-based inclusive
    ) -> EngineRunManifest: ...

    def load_and_adapt(self, manifest: EngineRunManifest) -> list[PageCandidate]: ...
```

Runner outcomes are recorded in `EngineRunManifest.status`:
- `ok`
- `timeout`
- `error`
- `unavailable`

## 4. Discovery policy (deterministic)

MinerU discovery must support the modern CLI:
- preferred: `mineru`

Resolution order (first hit wins):
1. `override_binary_path` (if provided)
2. `DOCFORGE_MINERU_BIN` (explicit path; must exist)
3. `{DOCFORGE_MINERU_VENV or "tools/mineru/.venv"}/bin/mineru` (if exists)
4. `mineru` in `$PATH`

Notes:
- This runner does not provision tool envs; it only discovers and runs.
- If no binary is found, `run()` returns `EngineRunManifest(engine_name="mineru", status="unavailable")`.

## 5. Version detection

`get_version()` should:
- call the discovered binary with `--version` (fallback `-V`) using `_subprocess.run_command(..., timeout_s=5)`
- extract the first semver match `(\d+\.\d+\.\d+)` from stdout/stderr
- cache the parsed version

If no version string is parseable, return `None` (do not fail the run).

## 6. MinerU config + environment injection (reproducibility)

MinerU expects a config JSON file pointed to by `MINERU_TOOLS_CONFIG_JSON`.

Design choice (locked): the runner writes this config file inside the run output directory:
- `config_path = output_dir / "mineru_config.json"`
- env sets: `MINERU_TOOLS_CONFIG_JSON=str(config_path)`

The config payload must include:
- `models-dir`
  - modern `mineru`: `{"pipeline": "<dir>", "vlm": "<dir>"}`
- `device-mode`: from `DOCFORGE_MINERU_DEVICE` (default `"cpu"`)
- `table-config`: `{"enable": True, "max_time": 400}`
- `formula-config`: `{"enable": True}`
- `layout-config`: `{}`
- `bucket_info`: `{"[default]": ["", "", ""]}`

Optional Gemini block:
- enabled only if `GEMINI_API_KEY` or `GOOGLE_API_KEY` is set
- default model: `gemini-2.0-flash`
- default base_url: `https://generativelanguage.googleapis.com/v1beta/openai/`
- include both:
  - `llm-aided-config` with shared fields
  - `title_aided` sub-object (mirrors the other repo’s compatibility behavior)

## 7. Command construction + page range semantics

Base command:
- `[bin, "-p", <pdf_path>, "-o", <output_dir>, "-b", <backend>]`

Backend:
- from `DOCFORGE_MINERU_BACKEND` (default `"pipeline"`)

Page range:
- if `start_page` is not None: add `["-s", str(start_page)]`
- if `end_page` is not None: add `["-e", str(end_page)]`
- page indices are **0-based, inclusive** at the runner API level

## 8. Output selection (canonical JSON for adaptation)

MinerU emits multiple JSON artifacts. The runner must choose a canonical JSON payload to feed into
`adapt_mineru_output(...)`, preferring stable/flat formats.

Selection algorithm for `_select_mineru_json_payload(output_dir)`:
1. Prefer files matching `*_content_list.json` (choose largest if multiple).
2. Else prefer files matching `*_middle.json` (choose largest if multiple).
3. Else choose the largest `.json` file under `output_dir`, excluding `mineru_config.json`.
4. If none found, raise `RuntimeError("Extractor 'mineru' did not produce JSON output.")`.

`run()` should only return `status="ok"` if a canonical JSON payload can be selected.

## 9. Bridge to existing adapter

`MineruRunner.load_and_adapt(manifest)`:
- if `manifest.status != "ok"` or `manifest.raw_output_dir` is missing: return `[]`
- select canonical payload path
- `json.load(...)` the payload (may be `list[dict]` or `dict`)
- call `adapt_mineru_output(payload, artifact_ref=str(output_dir))`
- on any exception: return `[]` (match Marker runner resilience)

## 10. Ad-hoc runner script: `scripts/run_mineru.py` (targets like Marker)

### 10.1. CLI
Mutually exclusive:
- `--pdf <path>` run once
- `--targets <json>` iterate targets

### 10.2. Targets file semantics (locked)
Design choice (locked): page ranges in `scripts/targets.json` are **1-based (human)**.

For MinerU CLI flags (`-s/-e`, 0-based inclusive), convert:
- `"37"` => `start_page=36`, `end_page=36`
- `"37-38"` => `start_page=36`, `end_page=37`

Constraints:
- reject comma-separated non-contiguous ranges (e.g. `"1,3,5"`) with a clear error

### 10.3. Output dirs
For each target, output root:
- `output/mineru_test/{pdf_stem}_{clean_page_range}/`

The script should print:
- discovered binary + version
- run status, error_details, stderr on failure
- counts of `*.json` and `*.md` under the output dir (recursive)

Timeout default:
- `timeout_s=300` (match `scripts/run_marker.py`)

## 11. CI-safe testing strategy (no real MinerU)

Add `tests/parsers/pdf_hybrid/test_mineru_cli.py` following the structure of `test_marker_cli.py`:

- payload selection tests:
  - prefers `_content_list.json`
  - falls back to `_middle.json`
  - errors if no JSON
- discovery tests:
  - `DOCFORGE_MINERU_BIN`
  - `tools/mineru/.venv/bin/mineru`
  - PATH fallbacks
- version parsing:
  - semver from stdout/stderr for both `--version` and `-V`
- run() outcomes with mocked `_subprocess.run_command`:
  - `ok` writes dummy `_content_list.json`
  - `timeout` yields manifest `status="timeout"`
  - non-zero exit yields `status="error"`
  - discover None yields `status="unavailable"`
- load_and_adapt() tests:
  - ok manifest loads payload and calls `adapt_mineru_output(...)`
  - non-ok manifest returns `[]`

Mock boundaries:
- patch `docforge.parsers.pdf_hybrid.engines.mineru_cli.run_command`
- patch `os.environ`, `os.path.exists`, `pathlib.Path.exists`, `shutil.which` as needed

## 12. Operational notes (local-only)
- MinerU requires model weights (default location `~/models`, override via `DOCFORGE_MINERU_MODELS_DIR`).
- The main repo must not depend on MinerU; it should run from an isolated tool env (e.g. `tools/mineru/.venv`).

## 13. Acceptance criteria
- `MineruRunner` can discover, run with timeout, produce an `EngineRunManifest`, and adapt output via `adapt_mineru_output`.
- `scripts/run_mineru.py --targets scripts/targets.json` creates per-target output dirs under `output/mineru_test/`.
- Unit tests validate discovery/version/run/output-selection/load+adapt without requiring MinerU installed.
