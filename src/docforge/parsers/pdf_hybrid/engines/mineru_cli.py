import json
import os
import re
import shutil
import time
from pathlib import Path

from docforge.parsers.pdf_hybrid.engines._subprocess import run_command
from docforge.parsers.pdf_hybrid.engines.miner_u import adapt_mineru_output
from docforge.parsers.pdf_hybrid.engines.run_manifest import EngineRunManifest
from docforge.parsers.pdf_hybrid.models import PageCandidate

CODE_KEYWORD_PATTERN = re.compile(
    r"\b("
    r"function|class|interface|enum|const|let|var|def|return|returns|switch|case|"
    r"if|else|for|while|try|catch|throw|import|from|public|private|protected|"
    r"service|rpc|message|type|struct|func|go"
    r")\b",
    flags=re.IGNORECASE,
)
CODE_LINE_ENDINGS = (";", "{", "}", "});", ");", "],", "),")


def _detect_code_language(paragraph: str) -> str:
    lowered = paragraph.lower()
    if any(token in lowered for token in ("function ", "const ", "let ", "=>", "switch(")):
        return "javascript"
    if any(token in lowered for token in ("def ", "import ", "from ")) and ":" in paragraph:
        return "python"
    if "{" in paragraph and "}" in paragraph and ":" in paragraph and '"' in paragraph:
        return "json"
    return "text"


def _is_code_paragraph(paragraph: str) -> bool:
    lines = [line.rstrip() for line in paragraph.split("\n") if line.strip()]
    if not lines:
        return False

    joined = "\n".join(lines)
    if "```" in joined:
        return False

    keyword_hit = bool(CODE_KEYWORD_PATTERN.search(joined))
    indented_hit = any(line.startswith(("    ", "\t")) for line in lines)
    ending_hit = any(line.strip().endswith(CODE_LINE_ENDINGS) for line in lines)

    symbol_count = sum(joined.count(symbol) for symbol in "{}();[]=<>")
    symbol_density = symbol_count / max(1, len(joined))
    symbol_hit = symbol_count >= 6 or (symbol_count >= 4 and symbol_density >= 0.03)

    signals = sum((keyword_hit, indented_hit, ending_hit, symbol_hit))

    # Single line strong signals
    if len(lines) == 1:
        if signals >= 3:
            return True
        # If it has strong programming symbols and either keywords or typical endings
        if symbol_hit and (keyword_hit or ending_hit):
            return True
        return False

    if len(lines) >= 2:
        return signals >= 2
    return signals >= 3


def _mark_code_paragraphs(markdown_text: str) -> tuple[str, int]:
    lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output_lines: list[str] = []
    paragraph_buffer: list[str] = []
    inside_fence = False
    marked_blocks = 0

    def flush_paragraph() -> None:
        nonlocal marked_blocks
        if not paragraph_buffer:
            return
        paragraph = "\n".join(paragraph_buffer)
        if _is_code_paragraph(paragraph):
            language = _detect_code_language(paragraph)
            output_lines.append(f"```{language}")
            output_lines.extend(paragraph_buffer)
            output_lines.append("```")
            marked_blocks += 1
        else:
            output_lines.extend(paragraph_buffer)
        paragraph_buffer.clear()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            output_lines.append(line)
            inside_fence = not inside_fence
            continue

        if inside_fence:
            output_lines.append(line)
            continue

        if stripped == "":
            flush_paragraph()
            output_lines.append(line)
            continue

        paragraph_buffer.append(line)

    flush_paragraph()
    return "\n".join(output_lines), marked_blocks


def _postprocess_mineru_outputs(output_dir: Path) -> tuple[int, int]:
    updated_files = 0
    marked_blocks = 0

    # Update markdown files
    for markdown_path in sorted(output_dir.rglob("*.md")):
        original = markdown_path.read_text(encoding="utf-8")
        updated, marked = _mark_code_paragraphs(original)
        if marked > 0 and updated != original:
            markdown_path.write_text(updated, encoding="utf-8")
            updated_files += 1
            marked_blocks += marked

    # Update canonical JSON payload
    try:
        json_path = _select_mineru_json_payload(output_dir)
        with open(json_path, encoding="utf-8") as f:
            payload = json.load(f)

        json_updated = False

        if isinstance(payload, list):
            for block in payload:
                if block.get("type", "").lower() in (
                    "text",
                    "paragraph",
                    "text_block",
                    "unknown",
                    "discarded",
                ):
                    text = block.get("text", "")
                    if text:
                        new_text, marked = _mark_code_paragraphs(text)
                        if marked > 0 and new_text != text:
                            block["text"] = new_text
                            block["type"] = "code"
                            json_updated = True
        else:
            pdf_info = payload.get("pdf_info", payload)
            pages_list = pdf_info if isinstance(pdf_info, list) else pdf_info.get("pages", [])
            for page in pages_list:
                blocks = page.get("blocks", page.get("preproc_blocks", []))
                for block in blocks:
                    if block.get("type", "").lower() in (
                        "text",
                        "paragraph",
                        "text_block",
                        "unknown",
                        "discarded",
                    ):
                        text = block.get("text", "")
                        if text:
                            new_text, marked = _mark_code_paragraphs(text)
                            if marked > 0 and new_text != text:
                                block["text"] = new_text
                                block["type"] = "code"
                                json_updated = True

        if json_updated:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

    except Exception:
        # Ignore errors if JSON processing fails, we don't want to break the runner completely
        pass

    return updated_files, marked_blocks


def _select_mineru_json_payload(output_dir: Path) -> Path:
    """Selects the canonical JSON payload from MinerU output."""
    all_json = list(output_dir.rglob("*.json"))

    content_list_candidates = [p for p in all_json if p.name.endswith("_content_list.json")]
    if content_list_candidates:
        return max(content_list_candidates, key=lambda path: path.stat().st_size)

    middle_candidates = [p for p in all_json if p.name.endswith("_middle.json")]
    if middle_candidates:
        return max(middle_candidates, key=lambda path: path.stat().st_size)

    other_candidates = [p for p in all_json if p.name != "mineru_config.json"]
    if other_candidates:
        return max(other_candidates, key=lambda path: path.stat().st_size)

    raise RuntimeError("Extractor 'mineru' did not produce JSON output.")


def _build_mineru_config(
    output_dir: Path,
    models_dir: str,
    device: str,
    env: dict[str, str],
) -> Path:
    config_path = output_dir / "mineru_config.json"

    models_config = {"pipeline": models_dir, "vlm": models_dir}

    config_data = {
        "models-dir": models_config,
        "device-mode": device,
        "table-config": {"enable": True, "max_time": 400},
        "formula-config": {"enable": True},
        "layout-config": {},
        "bucket_info": {"[default]": ["", "", ""]},
    }

    if "GEMINI_API_KEY" in env or "GOOGLE_API_KEY" in env:
        gemini_model = env.get("GEMINI_MODEL", "gemini-3-flash-preview")
        gemini_base_url = env.get(
            "GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        gemini_key = env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY")

        shared_llm = {
            "api_key": gemini_key,
            "model": gemini_model,
            "base_url": gemini_base_url,
        }

        config_data["llm-aided-config"] = {
            "enable": True,
            **shared_llm,
            "title_aided": dict(shared_llm),
        }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    return config_path


class MineruRunner:
    def __init__(
        self,
        override_binary_path: str | None = None,
        env_overrides: dict[str, str] | None = None,
    ):
        self._override_binary_path = override_binary_path
        self._env_overrides = env_overrides or {}
        self._binary_path: str | None = None
        self._version: str | None = None

    def discover(self) -> str | None:
        if self._binary_path is not None:
            return self._binary_path

        if self._override_binary_path:
            self._binary_path = self._override_binary_path
            return self._binary_path

        # 1. Exact path from DOCFORGE_MINERU_BIN
        env_bin = os.environ.get("DOCFORGE_MINERU_BIN")
        if env_bin and os.path.exists(env_bin):
            self._binary_path = env_bin
            return self._binary_path

        # 2. {venv_path}/bin/mineru
        env_venv = os.environ.get("DOCFORGE_MINERU_VENV", "tools/mineru/.venv")
        venv_bin = Path(env_venv) / "bin" / "mineru"
        if venv_bin.exists():
            self._binary_path = str(venv_bin)
            return self._binary_path

        # 3. mineru in $PATH
        path_bin = shutil.which("mineru")
        if path_bin:
            self._binary_path = path_bin
            return self._binary_path

        return None

    def get_version(self) -> str | None:
        if self._version:
            return self._version

        bin_path = self.discover()
        if not bin_path:
            return None

        for flag in ["--version", "-V"]:
            result = run_command([bin_path, flag], timeout_s=5.0)
            for output in (result.stdout, result.stderr):
                match = re.search(r"(\d+\.\d+\.\d+)", output)
                if match:
                    self._version = match.group(1)
                    return self._version

        return None

    def is_available(self) -> bool:
        return self.discover() is not None

    def run(
        self,
        pdf_path: Path,
        output_dir: Path,
        timeout_s: float,
        *,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> EngineRunManifest:
        bin_path = self.discover()
        if not bin_path:
            return EngineRunManifest(
                engine_name="mineru",
                status="unavailable",
            )

        env = os.environ.copy()
        env.update(self._env_overrides)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine config values
        models_dir = env.get("DOCFORGE_MINERU_MODELS_DIR", os.path.expanduser("~/models"))
        device = env.get("DOCFORGE_MINERU_DEVICE", "cpu")

        # Write config
        config_path = _build_mineru_config(output_dir, models_dir, device, env)
        env["MINERU_TOOLS_CONFIG_JSON"] = str(config_path.absolute())

        start_time = time.monotonic()
        version = self.get_version()

        cmd = [bin_path, "-p", str(pdf_path), "-o", str(output_dir)]

        backend = env.get("DOCFORGE_MINERU_BACKEND", "pipeline")
        cmd.extend(["-b", backend])

        if start_page is not None:
            cmd.extend(["-s", str(start_page)])
        if end_page is not None:
            cmd.extend(["-e", str(end_page)])

        result = run_command(cmd, timeout_s=timeout_s, env=env)
        execution_time_s = time.monotonic() - start_time

        if result.timed_out:
            return EngineRunManifest(
                engine_name="mineru",
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
                engine_name="mineru",
                status="error",
                version=version,
                binary_path=bin_path,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time_s=execution_time_s,
                error_details=result.error_message
                or f"Process exited with code {result.returncode}",
            )

        # Post-process Markdown to fence detected code paragraphs
        _postprocess_mineru_outputs(output_dir)

        try:
            _select_mineru_json_payload(output_dir)
            return EngineRunManifest(
                engine_name="mineru",
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
                engine_name="mineru",
                status="error",
                version=version,
                binary_path=bin_path,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time_s=execution_time_s,
                error_details=str(e),
            )

    def load_and_adapt(self, manifest: EngineRunManifest) -> list[PageCandidate]:
        if manifest.status != "ok":
            return []

        if not manifest.raw_output_dir:
            return []

        output_dir = Path(manifest.raw_output_dir)
        try:
            payload_path = _select_mineru_json_payload(output_dir)
            with open(payload_path, encoding="utf-8") as f:
                raw_json = json.load(f)
            return adapt_mineru_output(raw_json, artifact_ref=str(output_dir))
        except Exception:
            return []
