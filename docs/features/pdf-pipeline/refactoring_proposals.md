# CLI Runner Refactoring Proposals

**Context:** Adding `MineruRunner` alongside `MarkerRunner`. Both share ~70% structural overlap (init, discovery chain, version parsing, outcome recording, load_and_adapt). The key tension: their `run()` methods genuinely differ — Marker loops over output formats, MinerU has binary-flavor branching and config file injection.

---

## Proposal 1 — Thin Shared Helpers (Lightest)

Extract only provably-duplicated logic into `engines/_runner_utils.py`. Both runners remain standalone classes.

**Shared (`_runner_utils.py`, ~60 lines):**
```python
parse_semver(stdout, stderr) -> str | None
build_outcome_manifest(engine_name, result, version, bin_path,
                       output_dir, select_payload_fn, execution_time_s) -> EngineRunManifest
```

**Stays per-engine:** `__init__`, `discover()`, `get_version()` (calls `parse_semver`), `is_available()`, `run()`, `load_and_adapt()`, `_select_*_payload()`.

**File changes:**
| File | Action |
|---|---|
| `engines/_runner_utils.py` | Create (~60 lines) |
| `engines/marker_cli.py` | Update to use `parse_semver` + `build_outcome_manifest` (~30 lines removed) |
| `engines/mineru_cli.py` | Create (~160 lines), importing from `_runner_utils` |
| `test_marker_cli.py` | **No changes** — all patch targets survive |

**Pros:** Zero test breakage. Each runner file is fully self-contained. MinerU's unique complexity (config file writing, CLI flavor detection) stays local.

**Cons:** ~15 lines of structural duplication accepted (`__init__`, `is_available`, `load_and_adapt` guard). Discovery chain pattern is copy-pasted.

---

## Proposal 2 — Abstract Base Class (Medium)

Introduce `BaseCLIRunner` ABC in `engines/_base_runner.py` with concrete `is_available`, `get_version`, `load_and_adapt`, `_record_outcome`. Abstract methods: `discover()`, `_select_json_payload()`, `_adapt()`.

**Key constraint:** `run()` cannot be a template method — Marker's format loop and MinerU's single-call-with-flavor-branching are structurally different. So `run()` stays concrete in each subclass, calling `self._record_outcome()`.

```python
class BaseCLIRunner(ABC):
    ENGINE_NAME: str

    # Concrete: is_available, get_version, load_and_adapt, _record_outcome
    # Abstract: discover, _select_json_payload, _adapt
```

MinerU overrides `get_version` to add `-V` fallback.

**File changes:**
| File | Action |
|---|---|
| `engines/_base_runner.py` | Create (~100 lines) |
| `engines/marker_cli.py` | Refactor to extend base (228 → ~130 lines) |
| `engines/mineru_cli.py` | Create (~180 lines) |
| `test_marker_cli.py` | Likely no changes (patches survive through inheritance) |

**Pros:** `is_available`, `load_and_adapt`, version regex, outcome recording written once. ABC enforces interface at import time.

**Cons:** `run()` duplication remains (~20 lines each). `_build_env` for MinerU writes files to disk — doesn't fit an abstract "build env" contract. One more file to trace through.

---

## Proposal 3 — Data-Driven Config Object (Heaviest)

Single `CLIRunner` class driven by an `EngineConfig` dataclass. Engine-specific behavior provided via callable fields (protocols):

```python
@dataclass
class EngineConfig:
    engine_name: str
    env_bin_var: str           # "DOCFORGE_MINERU_BIN"
    env_venv_var: str          # "DOCFORGE_MINERU_VENV"
    default_venv_path: str     # "tools/mineru/.venv"
    primary_binary_names: list[str]  # ["mineru", "magic-pdf"]
    version_flags: list[str]
    build_env: EnvBuilder      # callable
    build_cmd: CmdBuilder      # callable
    select_payload: PayloadSelector
    adapter: Callable
```

Discovery is fully generic — parameterized by config values. Each engine module becomes ~60 lines (callables + config + backward-compat alias).

**File changes:**
| File | Action |
|---|---|
| `engines/_cli_runner.py` | Create (~150 lines) |
| `engines/marker_cli.py` | Replace class with config + alias (228 → ~60 lines) |
| `engines/mineru_cli.py` | Create (~120 lines) |
| `test_marker_cli.py` | Needs review — multi-format loop handling may change |

**Pros:** `discover`, `get_version`, `is_available`, `load_and_adapt`, outcome recording all written once. Adding a third engine is purely additive. Discovery is parameterized, not copied.

**Cons:** Marker's format loop doesn't fit the single-`run_command` model — either Marker overrides `run()` (defeating the purpose) or generic `run()` gains a multi-command hook (over-engineered for one engine). `**run_kwargs` loses type safety across engines. Callable fields on dataclasses are awkward to mock. Overkill for two engines.

---

## Recommendation

**Proposal 1** for now. Rationale:

1. The shared duplication is bounded (~55 lines of outcome recording + ~5 lines of semver parsing). That's a fair price for self-contained, readable runner files.
2. The `run()` signatures genuinely differ — Marker's format loop and MinerU's flavor branching resist a clean shared template.
3. MinerU's `_build_env` writes a config file to disk — a side effect that doesn't belong in an abstract contract.
4. Zero test breakage. `test_marker_cli.py` survives unchanged.
5. **Revisit Proposal 2 if a third engine arrives** — at that point, the ABC cost is justified and can be designed with three concrete examples rather than speculation.
