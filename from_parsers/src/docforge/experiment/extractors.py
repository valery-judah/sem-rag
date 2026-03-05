from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MARKER_VENV = ".venvs/marker"
MARKER_VENV_ENV_VAR = "DOCFORGE_MARKER_VENV"
MARKER_BIN_ENV_VAR = "DOCFORGE_MARKER_BIN"


@dataclass(slots=True)
class ExtractedPage:
    page_index: int
    text: str
    width: float | None = None
    height: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)


class Extractor(Protocol):
    def extract(self, source_path: Path) -> list[ExtractedPage]: ...


class SyntheticTextExtractor:
    """Baseline extractor for local testing.

    It expects a UTF-8 text file and splits pages by form-feed (`\f`).
    """

    def extract(self, source_path: Path) -> list[ExtractedPage]:
        text = source_path.read_text(encoding="utf-8")
        page_texts = text.split("\f")
        return [
            ExtractedPage(page_index=index, text=page_text)
            for index, page_text in enumerate(page_texts)
        ]


class PyPdfExtractor:
    """Lightweight PDF text extraction via pypdf (optional dependency)."""

    def extract(self, source_path: Path) -> list[ExtractedPage]:
        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "Extractor 'pypdf' requires the optional dependency 'pypdf'. "
                "Install it with: uv add pypdf"
            ) from exc

        reader = PdfReader(str(source_path))
        pages: list[ExtractedPage] = []
        for index, page in enumerate(reader.pages):
            extracted_text = page.extract_text() or ""
            width: float | None = None
            height: float | None = None

            mediabox = getattr(page, "mediabox", None)
            if mediabox is not None:
                width = float(mediabox.width)
                height = float(mediabox.height)

            pages.append(
                ExtractedPage(
                    page_index=index,
                    text=extracted_text,
                    width=width,
                    height=height,
                )
            )
        return pages


class PyMuPdfExtractor:
    """PDF text extraction via PyMuPDF/fitz (optional dependency)."""

    def extract(self, source_path: Path) -> list[ExtractedPage]:
        try:
            import fitz  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "Extractor 'pymupdf' requires the optional dependency 'pymupdf'. "
                "Install it with: uv add pymupdf"
            ) from exc

        document = fitz.open(source_path)
        pages: list[ExtractedPage] = []
        try:
            for index, page in enumerate(document):
                text = page.get_text("text") or ""
                width = float(page.rect.width)
                height = float(page.rect.height)
                pages.append(
                    ExtractedPage(
                        page_index=index,
                        text=text,
                        width=width,
                        height=height,
                    )
                )
        finally:
            document.close()
        return pages


class MarkerExtractor:
    """Layout-first extraction through marker CLI."""

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self._options = options or {}

    def extract(self, source_path: Path) -> list[ExtractedPage]:
        marker_binary = _resolve_marker_binary(self._options)
        if marker_binary is None:
            marker_venv_dir = _resolve_marker_venv_dir()
            marker_python = _marker_venv_python_path(marker_venv_dir)
            marker_venv_binary = _marker_venv_executable_path(marker_venv_dir, "marker_single")
            raise RuntimeError(
                "Extractor 'marker' requires Marker CLI and none was found. "
                f"Tried option 'binary', {MARKER_BIN_ENV_VAR}, "
                f"{marker_venv_binary}, and PATH.\n"
                "Install Marker in an isolated venv with:\n"
                f"  uv venv {marker_venv_dir} --allow-existing\n"
                f"  uv pip install --python {marker_python} 'marker-pdf[full]'"
            )

        with tempfile.TemporaryDirectory(prefix="docforge-marker-") as temp_dir:
            output_dir = Path(temp_dir)
            command = [
                marker_binary,
                str(source_path),
                "--output_dir",
                str(output_dir),
                "--output_format",
                "json",
            ]
            if _as_bool(self._options.get("disable_multiprocessing"), default=True):
                command.append("--disable_multiprocessing")
            if _as_bool(self._options.get("disable_image_extraction"), default=False):
                command.append("--disable_image_extraction")

            page_range = self._options.get("page_range")
            if isinstance(page_range, str) and page_range.strip():
                command.extend(["--page_range", page_range.strip()])

            processors = self._options.get("processors")
            if isinstance(processors, str) and processors.strip():
                command.extend(["--processors", processors.strip()])

            config_json = self._options.get("config_json")
            if isinstance(config_json, str) and config_json.strip():
                command.extend(["--config_json", config_json.strip()])

            llm_service = self._options.get("llm_service")
            if isinstance(llm_service, str) and llm_service.strip():
                command.extend(["--llm_service", llm_service.strip()])

            converter_cls = self._options.get("converter_cls")
            if isinstance(converter_cls, str) and converter_cls.strip():
                command.extend(["--converter_cls", converter_cls.strip()])

            environment = os.environ.copy()
            torch_device = self._options.get("torch_device")
            if isinstance(torch_device, str) and torch_device.strip():
                environment["TORCH_DEVICE"] = torch_device.strip()
            pytorch_alloc_conf = self._options.get("pytorch_alloc_conf")
            if isinstance(pytorch_alloc_conf, str) and pytorch_alloc_conf.strip():
                environment["PYTORCH_ALLOC_CONF"] = pytorch_alloc_conf.strip()

            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            if completed.returncode != 0:
                stderr = completed.stderr.strip()
                stdout = completed.stdout.strip()
                details = stderr or stdout or "unknown marker error"
                raise RuntimeError(f"Extractor 'marker' failed: {details}")

            json_payload_path = _select_marker_json_payload(output_dir)
            payload = json.loads(json_payload_path.read_text(encoding="utf-8"))
            pages = _marker_payload_to_pages(payload)
            if not pages:
                raise RuntimeError("Extractor 'marker' produced no pages from JSON payload.")
            return pages


class MineruExtractor:
    """Layout-first extraction through MinerU (`mineru` or `magic-pdf` CLI)."""

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self._options = options or {}

    def extract(self, source_path: Path) -> list[ExtractedPage]:
        configured_binary = self._options.get("binary")
        mineru_binary: str | None
        if isinstance(configured_binary, str) and configured_binary.strip():
            mineru_binary = configured_binary.strip()
        else:
            mineru_binary = _resolve_mineru_binary()
        if mineru_binary is None:
            raise RuntimeError(
                "Extractor 'mineru' requires MinerU CLI in PATH (supported binaries: mineru)."
            )

        with tempfile.TemporaryDirectory(prefix="docforge-mineru-") as temp_dir:
            temp_root = Path(temp_dir)
            output_dir = temp_root / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            config_path = temp_root / "magic-pdf.json"
            _write_mineru_config(config_path)

            environment = os.environ.copy()
            environment.setdefault("MINERU_TOOLS_CONFIG_JSON", str(config_path))

            command = _build_mineru_command(
                binary=mineru_binary,
                source_path=source_path,
                output_dir=output_dir,
                options=self._options,
            )
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            if completed.returncode != 0:
                stderr = completed.stderr.strip()
                stdout = completed.stdout.strip()
                details = stderr or stdout or "unknown mineru error"
                raise RuntimeError(f"Extractor 'mineru' failed: {details}")

            pages = _load_mineru_pages(output_dir)
            if not pages:
                raise RuntimeError("Extractor 'mineru' produced no parseable output.")
            return pages


def _select_marker_json_payload(output_dir: Path) -> Path:
    candidates = [
        path for path in output_dir.rglob("*.json") if not path.name.endswith("_meta.json")
    ]
    if not candidates:
        raise RuntimeError("Extractor 'marker' did not produce JSON output.")
    return max(candidates, key=lambda path: path.stat().st_size)


def _marker_payload_to_pages(payload: dict[str, Any]) -> list[ExtractedPage]:
    blocks_raw = payload.get("blocks")
    page_info_raw = payload.get("page_info")

    if isinstance(blocks_raw, list):
        return _marker_flat_payload_to_pages(blocks_raw=blocks_raw, page_info_raw=page_info_raw)

    children_raw = payload.get("children")
    if isinstance(children_raw, list):
        return _marker_tree_payload_to_pages(children_raw=children_raw)

    return []


def _marker_flat_payload_to_pages(
    *, blocks_raw: list[Any], page_info_raw: Any
) -> list[ExtractedPage]:
    page_lines: dict[int, list[str]] = {}

    for block in blocks_raw:
        if not isinstance(block, dict):
            continue
        page_index = _marker_page_index(block)
        if page_index is None:
            continue
        text = _html_to_plain_text(str(block.get("html", "")))
        if not text:
            continue
        page_lines.setdefault(page_index, []).append(text)

    page_info: dict[str, Any]
    if isinstance(page_info_raw, dict):
        page_info = page_info_raw
    else:
        page_info = {}

    all_page_indexes = set(page_lines)
    for key in page_info:
        try:
            all_page_indexes.add(int(key))
        except ValueError:
            continue

    pages: list[ExtractedPage] = []
    for page_index in sorted(all_page_indexes):
        width: float | None = None
        height: float | None = None

        page_dimensions = page_info.get(str(page_index))
        if isinstance(page_dimensions, dict):
            bbox_raw = page_dimensions.get("bbox")
            if (
                isinstance(bbox_raw, list)
                and len(bbox_raw) == 4
                and all(isinstance(value, (int, float)) for value in bbox_raw)
            ):
                width = float(bbox_raw[2]) - float(bbox_raw[0])
                height = float(bbox_raw[3]) - float(bbox_raw[1])

        text = "\n".join(page_lines.get(page_index, [])).strip()
        pages.append(
            ExtractedPage(
                page_index=page_index,
                text=text,
                width=width,
                height=height,
            )
        )

    return pages


def _marker_tree_payload_to_pages(*, children_raw: list[Any]) -> list[ExtractedPage]:
    pages: list[ExtractedPage] = []

    for child in children_raw:
        if not isinstance(child, dict):
            continue

        page_index = _marker_page_index(child)
        if page_index is None:
            continue

        width: float | None = None
        height: float | None = None
        bbox_raw = child.get("bbox")
        if (
            isinstance(bbox_raw, list)
            and len(bbox_raw) == 4
            and all(isinstance(value, (int, float)) for value in bbox_raw)
        ):
            width = float(bbox_raw[2]) - float(bbox_raw[0])
            height = float(bbox_raw[3]) - float(bbox_raw[1])

        lines: list[str] = []
        nested_children = child.get("children")
        if isinstance(nested_children, list):
            for block in nested_children:
                if not isinstance(block, dict):
                    continue
                text = _html_to_plain_text(str(block.get("html", "")))
                if text:
                    lines.append(text)

        pages.append(
            ExtractedPage(
                page_index=page_index,
                text="\n".join(lines).strip(),
                width=width,
                height=height,
            )
        )

    pages.sort(key=lambda page: page.page_index)
    return pages


def _marker_page_index(block: dict[str, Any]) -> int | None:
    block_id_raw = block.get("id")
    if isinstance(block_id_raw, str):
        match = re.search(r"/page/(\d+)/", block_id_raw)
        if match is not None:
            return int(match.group(1))

    page_value = block.get("page")
    if isinstance(page_value, int) and page_value >= 0:
        return page_value
    return None


def _html_to_plain_text(value: str) -> str:
    normalized = value
    normalized = normalized.replace("<br/>", "\n").replace("<br>", "\n")
    normalized = normalized.replace("</p>", "\n").replace("</tr>", "\n")
    normalized = re.sub(r"<[^>]+>", "", normalized)
    normalized = html.unescape(normalized)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _write_mineru_config(config_path: Path) -> None:
    default_models_dir = str(Path.home() / "models")
    models_dir = os.getenv("DOCFORGE_MINERU_MODELS_DIR", default_models_dir)
    models_dir_normalized = models_dir.strip() or default_models_dir
    models_dir_config = {"pipeline": models_dir_normalized, "vlm": models_dir_normalized}

    config_payload: dict[str, Any] = {
        "models-dir": models_dir_config,
        "device-mode": os.getenv("DOCFORGE_MINERU_DEVICE", "cpu"),
        "table-config": {"enable": True, "max_time": 400},
        "formula-config": {"enable": True},
        "layout-config": {},
        "bucket_info": {"[default]": ["", "", ""]},
    }

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        gemini_base_url = os.getenv(
            "GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        shared_llm_config = {
            "api_key": gemini_key,
            "model": gemini_model,
            "base_url": gemini_base_url,
        }
        config_payload["llm-aided-config"] = {
            "enable": True,
            **shared_llm_config,
            # Keep both flat and nested keys so newer/older MinerU versions can parse it.
            "title_aided": dict(shared_llm_config),
        }

    serialized = json.dumps(config_payload, indent=2, sort_keys=True)
    config_path.write_text(serialized + "\n", encoding="utf-8")


def _load_mineru_pages(output_dir: Path) -> list[ExtractedPage]:
    json_paths = sorted(output_dir.rglob("*.json"))
    for json_path in json_paths:
        pages = _parse_mineru_json_payload(json_path)
        if pages:
            return pages

    markdown_paths = sorted(output_dir.rglob("*.md"))
    for markdown_path in markdown_paths:
        text = markdown_path.read_text(encoding="utf-8")
        if text.strip():
            return [ExtractedPage(page_index=0, text=text)]
    return []


def _parse_mineru_json_payload(path: Path) -> list[ExtractedPage]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if isinstance(payload, dict):
        pdf_info = payload.get("pdf_info")
        if isinstance(pdf_info, list):
            pdf_pages: list[ExtractedPage] = []
            for index, page_payload in enumerate(pdf_info):
                text = _collect_text_fragments(page_payload)
                pdf_pages.append(ExtractedPage(page_index=index, text=text))
            return pdf_pages

    if isinstance(payload, list):
        list_pages: list[ExtractedPage] = []
        for index, page_payload in enumerate(payload):
            text = _collect_text_fragments(page_payload)
            list_pages.append(ExtractedPage(page_index=index, text=text))
        return list_pages

    return []


def _collect_text_fragments(node: Any) -> str:
    fragments: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                fragments.append(stripped)
            return
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if isinstance(value, dict):
            for preferred_key in ("text", "content", "md_content", "html", "latex"):
                preferred_value = value.get(preferred_key)
                if isinstance(preferred_value, str) and preferred_value.strip():
                    fragments.append(preferred_value.strip())
            for child in value.values():
                if isinstance(child, (dict, list)):
                    visit(child)
            return

    visit(node)
    text = "\n".join(fragments)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _as_bool(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return default


def _is_windows() -> bool:
    return os.name == "nt"


def _resolve_marker_venv_dir() -> Path:
    configured = os.getenv(MARKER_VENV_ENV_VAR, DEFAULT_MARKER_VENV)
    normalized = configured.strip() if configured and configured.strip() else DEFAULT_MARKER_VENV
    path = Path(normalized).expanduser()
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def _marker_venv_executable_path(
    venv_dir: Path,
    executable: str,
    *,
    windows: bool | None = None,
) -> Path:
    is_windows = _is_windows() if windows is None else windows
    if is_windows:
        return venv_dir / "Scripts" / f"{executable}.exe"
    return venv_dir / "bin" / executable


def _marker_venv_python_path(venv_dir: Path, *, windows: bool | None = None) -> Path:
    return _marker_venv_executable_path(venv_dir, "python", windows=windows)


def _resolve_marker_binary(options: dict[str, Any] | None = None) -> str | None:
    resolved_options = options or {}

    configured_binary = resolved_options.get("binary")
    if isinstance(configured_binary, str) and configured_binary.strip():
        return configured_binary.strip()

    marker_bin_override = os.getenv(MARKER_BIN_ENV_VAR, "").strip()
    if marker_bin_override:
        return marker_bin_override

    marker_venv_dir = _resolve_marker_venv_dir()
    venv_marker_binary = _marker_venv_executable_path(marker_venv_dir, "marker_single")
    if venv_marker_binary.is_file():
        return str(venv_marker_binary)

    return shutil.which("marker_single") or shutil.which("marker")


def _resolve_mineru_binary() -> str | None:
    return shutil.which("mineru")


def _build_mineru_command(
    *,
    binary: str,
    source_path: Path,
    output_dir: Path,
    options: dict[str, Any],
) -> list[str]:
    command = [binary, "-p", str(source_path), "-o", str(output_dir)]

    backend_raw = options.get("backend")
    if isinstance(backend_raw, str) and backend_raw.strip():
        backend = backend_raw.strip()
    else:
        backend = os.getenv("DOCFORGE_MINERU_BACKEND", "pipeline")
    if backend:
        command.extend(["-b", backend])
    return command


def build_extractor(name: str, options: dict[str, Any] | None = None) -> Extractor:
    normalized_name = name.strip().lower()
    if normalized_name == "pypdf":
        return PyPdfExtractor()
    if normalized_name == "pymupdf":
        return PyMuPdfExtractor()
    if normalized_name == "marker":
        return MarkerExtractor(options=options)
    if normalized_name == "mineru":
        return MineruExtractor(options=options)
    if normalized_name == "synthetic_text":
        return SyntheticTextExtractor()
    raise ValueError(f"Unsupported extractor '{name}'.")
