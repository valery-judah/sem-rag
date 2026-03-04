import json
import os
import re
import shutil
import time
from pathlib import Path

from docforge.parsers.pdf_hybrid.engines._subprocess import run_command
from docforge.parsers.pdf_hybrid.engines.marker import adapt_marker_output
from docforge.parsers.pdf_hybrid.engines.run_manifest import EngineRunManifest
from docforge.parsers.pdf_hybrid.models import PageCandidate


def _select_marker_json_payload(output_dir: Path) -> Path:
    candidates = [
        path for path in output_dir.rglob("*.json") if not path.name.endswith("_meta.json")
    ]
    if not candidates:
        raise RuntimeError("Extractor 'marker' did not produce JSON output.")
    # Pick the largest JSON file as the main payload
    return max(candidates, key=lambda path: path.stat().st_size)


class MarkerRunner:
    def __init__(
        self, override_binary_path: str | None = None, env_overrides: dict[str, str] | None = None
    ):
        """Initializes the runner, optionally overriding discovery."""
        self._override_binary_path = override_binary_path
        self._env_overrides = env_overrides or {}
        self._binary_path: str | None = None
        self._version: str | None = None

    def discover(self) -> str | None:
        """Finds the marker binary according to the discovery policy."""
        if self._binary_path is not None:
            return self._binary_path

        if self._override_binary_path:
            self._binary_path = self._override_binary_path
            return self._binary_path

        # 1. Exact path from DOCFORGE_MARKER_BIN
        env_bin = os.environ.get("DOCFORGE_MARKER_BIN")
        if env_bin and os.path.exists(env_bin):
            self._binary_path = env_bin
            return self._binary_path

        # 2. {venv_path}/bin/marker_single
        env_venv = os.environ.get("DOCFORGE_MARKER_VENV", "tools/marker/.venv")
        venv_bin = Path(env_venv) / "bin" / "marker_single"
        if venv_bin.exists():
            self._binary_path = str(venv_bin)
            return self._binary_path

        # 3. marker_single in $PATH
        path_bin_single = shutil.which("marker_single")
        if path_bin_single:
            self._binary_path = path_bin_single
            return self._binary_path

        # 4. marker in $PATH
        path_bin = shutil.which("marker")
        if path_bin:
            self._binary_path = path_bin
            return self._binary_path

        return None

    def get_version(self) -> str | None:
        """Returns the version of the discovered binary."""
        if self._version:
            return self._version

        bin_path = self.discover()
        if not bin_path:
            return None

        result = run_command([bin_path, "--version"], timeout_s=5.0)

        # Parse output like "marker 0.1.0" or "0.1.0"
        for output in (result.stdout, result.stderr):
            match = re.search(r"(\d+\.\d+\.\d+)", output)
            if match:
                self._version = match.group(1)
                return self._version

        return None

    def is_available(self) -> bool:
        """Returns True if the binary is found."""
        return self.discover() is not None

    def run(
        self,
        pdf_path: Path,
        output_dir: Path,
        timeout_s: float,
        page_range: str | None = None,
        output_formats: list[str] | None = None,
    ) -> EngineRunManifest:
        """
        Executes marker on the given PDF, saving outputs to output_dir.
        Returns the run manifest detailing the outcome.
        """
        bin_path = self.discover()
        if not bin_path:
            return EngineRunManifest(
                engine_name="marker",
                status="unavailable",
            )

        if output_formats is None:
            output_formats = ["json", "markdown"]

        env = os.environ.copy()
        env.update(self._env_overrides)
        if "TORCH_DEVICE" not in env:
            env["TORCH_DEVICE"] = "cpu"
        if "PYTORCH_ALLOC_CONF" not in env:
            env["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

        start_time = time.monotonic()
        version = self.get_version()

        last_result = None
        for fmt in output_formats:
            cmd = [
                bin_path,
                str(pdf_path),
                "--output_dir",
                str(output_dir),
                "--output_format",
                fmt,
                "--disable_multiprocessing",
            ]
            if page_range:
                cmd.extend(["--page_range", page_range])

            result = run_command(cmd, timeout_s=timeout_s, env=env)
            last_result = result
            if result.timed_out or result.returncode != 0:
                break

        execution_time_s = time.monotonic() - start_time
        
        if last_result is None:
             return EngineRunManifest(
                 engine_name="marker",
                 status="error",
                 version=version,
                 binary_path=bin_path,
                 execution_time_s=execution_time_s,
                 error_details="No output formats specified.",
             )

        result = last_result

        if result.timed_out:
            return EngineRunManifest(
                engine_name="marker",
                status="timeout",
                version=version,
                binary_path=bin_path,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time_s=execution_time_s,
                error_details=result.error_message,
            )

        if result.returncode != 0:
            return EngineRunManifest(
                engine_name="marker",
                status="error",
                version=version,
                binary_path=bin_path,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time_s=execution_time_s,
                error_details=result.error_message
                or f"Process exited with code {result.returncode}",
            )

        # Check if output is there
        try:
            _select_marker_json_payload(output_dir)
            return EngineRunManifest(
                engine_name="marker",
                status="ok",
                version=version,
                binary_path=bin_path,
                raw_output_dir=str(output_dir),
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time_s=execution_time_s,
            )
        except RuntimeError as e:
            return EngineRunManifest(
                engine_name="marker",
                status="error",
                version=version,
                binary_path=bin_path,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time_s=execution_time_s,
                error_details=str(e),
            )

    def load_and_adapt(self, manifest: EngineRunManifest) -> list[PageCandidate]:
        """
        Loads the raw JSON from manifest.raw_output_dir and delegates to
        docforge.parsers.pdf_hybrid.engines.marker.adapt_marker_output.
        """
        if manifest.status != "ok":
            return []

        if not manifest.raw_output_dir:
            return []

        output_dir = Path(manifest.raw_output_dir)
        try:
            payload_path = _select_marker_json_payload(output_dir)
            with open(payload_path, encoding="utf-8") as f:
                raw_json_dict = json.load(f)
            return adapt_marker_output(raw_json_dict, artifact_ref=str(output_dir))
        except Exception:
            return []
