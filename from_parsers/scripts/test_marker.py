#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SOURCE = "data/llm-evals-course-notes-july.pdf"
DEFAULT_OUTPUT_ROOT = "artifacts/marker-smoke"
DEFAULT_OUTPUT_FORMATS = ("markdown", "json", "html")
SUPPORTED_OUTPUT_FORMATS = ("markdown", "json", "html", "chunks")
DEFAULT_MARKER_VENV = ".venvs/marker"
MARKER_VENV_ENV_VAR = "DOCFORGE_MARKER_VENV"
MARKER_BIN_ENV_VAR = "DOCFORGE_MARKER_BIN"
PROCESSOR_PROFILE_DEFAULT = "default"
PROCESSOR_PROFILE_MPS_SAFE = "mps-safe"
PROCESSOR_PROFILE_MPS_WITH_TABLES = "mps-with-tables"
SUPPORTED_PROCESSOR_PROFILES = (
    PROCESSOR_PROFILE_DEFAULT,
    PROCESSOR_PROFILE_MPS_SAFE,
    PROCESSOR_PROFILE_MPS_WITH_TABLES,
)
PROCESSORS_MPS_SAFE = (
    "marker.processors.order.OrderProcessor",
    "marker.processors.block_relabel.BlockRelabelProcessor",
    "marker.processors.line_merge.LineMergeProcessor",
    "marker.processors.blockquote.BlockquoteProcessor",
    "marker.processors.code.CodeProcessor",
    "marker.processors.document_toc.DocumentTOCProcessor",
    "marker.processors.equation.EquationProcessor",
    "marker.processors.footnote.FootnoteProcessor",
    "marker.processors.ignoretext.IgnoreTextProcessor",
    "marker.processors.line_numbers.LineNumbersProcessor",
    "marker.processors.list.ListProcessor",
    "marker.processors.page_header.PageHeaderProcessor",
    "marker.processors.sectionheader.SectionHeaderProcessor",
    "marker.processors.text.TextProcessor",
    "marker.processors.reference.ReferenceProcessor",
    "marker.processors.blank_page.BlankPageProcessor",
)
PROCESSORS_MPS_WITH_TABLES = PROCESSORS_MPS_SAFE + ("marker.processors.table.TableProcessor",)

CODE_KEYWORD_PATTERN = re.compile(
    r"\b("
    r"function|class|interface|enum|const|let|var|def|return|switch|case|"
    r"if|else|for|while|try|catch|throw|import|from|public|private|protected"
    r")\b",
    flags=re.IGNORECASE,
)
CODE_LINE_ENDINGS = (";", "{", "}", "});", ");", "],", "),")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Marker smoke test in this repository.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Runtime knobs:\n"
            f"  {MARKER_VENV_ENV_VAR} (default: {DEFAULT_MARKER_VENV})\n"
            f"  {MARKER_BIN_ENV_VAR} (optional explicit marker binary)\n"
            "  TORCH_DEVICE (optional)\n"
            "  PYTORCH_ALLOC_CONF (optional)"
        ),
    )
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        help=f"PDF file to parse (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_ROOT,
        help=f"Output root directory (default: {DEFAULT_OUTPUT_ROOT})",
    )
    parser.add_argument(
        "--install-marker",
        action="store_true",
        help=(
            "Create/update isolated marker venv and install marker-pdf[full] "
            "(does not modify pyproject.toml/uv.lock)"
        ),
    )
    parser.add_argument(
        "--output-format",
        default=",".join(DEFAULT_OUTPUT_FORMATS),
        help=(
            "Comma-separated Marker output formats "
            f"(supported: {', '.join(SUPPORTED_OUTPUT_FORMATS)}; "
            f"default: {','.join(DEFAULT_OUTPUT_FORMATS)})"
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker process count (marker CLI only).",
    )
    parser.add_argument(
        "--disable-multiprocessing",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Disable multiprocessing in Marker (default: enabled).",
    )
    parser.add_argument(
        "--disable-image-extraction",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Disable image extraction in Marker.",
    )
    parser.add_argument(
        "--page-range",
        default=None,
        help='Page range string understood by Marker (example: "0-4").',
    )
    parser.add_argument(
        "--processors",
        default=None,
        help='Marker processor list (example: "ocr,table").',
    )
    parser.add_argument(
        "--processor-profile",
        choices=SUPPORTED_PROCESSOR_PROFILES,
        default=PROCESSOR_PROFILE_DEFAULT,
        help=(
            "Processor profile when --processors is not provided "
            f"(default: {PROCESSOR_PROFILE_DEFAULT})"
        ),
    )
    parser.add_argument(
        "--config-json",
        default=None,
        help="Path to Marker config JSON file.",
    )
    parser.add_argument(
        "--mark-code-blocks",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Post-process Markdown and fence detected code paragraphs (default: enabled).",
    )
    return parser.parse_args(argv)


def run_cmd(
    cmd: Sequence[str],
    *,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(cmd, env=env, check=check)


def command_available(cmd: Sequence[str]) -> bool:
    try:
        result = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def resolve_marker_venv_dir(configured: str | None) -> Path:
    raw = configured.strip() if configured and configured.strip() else DEFAULT_MARKER_VENV
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def marker_venv_executable_path(
    venv_dir: Path,
    executable: str,
    *,
    windows: bool | None = None,
) -> Path:
    is_windows = os.name == "nt" if windows is None else windows
    if is_windows:
        return venv_dir / "Scripts" / f"{executable}.exe"
    return venv_dir / "bin" / executable


def marker_venv_python_path(venv_dir: Path, *, windows: bool | None = None) -> Path:
    return marker_venv_executable_path(venv_dir, "python", windows=windows)


def build_marker_install_commands(
    venv_dir: Path,
    *,
    windows: bool | None = None,
) -> list[list[str]]:
    python_path = marker_venv_python_path(venv_dir, windows=windows)
    return [
        ["uv", "venv", str(venv_dir), "--allow-existing"],
        ["uv", "pip", "install", "--python", str(python_path), "marker-pdf[full]"],
    ]


def _resolve_explicit_marker_binary(value: str) -> str | None:
    candidate = value.strip()
    if not candidate:
        return None
    if command_available([candidate, "--help"]):
        return candidate

    path = Path(candidate).expanduser()
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    normalized = str(path)
    if command_available([normalized, "--help"]):
        return normalized
    return None


def select_marker_binary(
    marker_venv_dir: Path,
    *,
    environ: Mapping[str, str] | None = None,
) -> tuple[str, str] | None:
    resolved_env = os.environ if environ is None else environ

    explicit_binary = resolved_env.get(MARKER_BIN_ENV_VAR, "").strip()
    if explicit_binary:
        resolved_binary = _resolve_explicit_marker_binary(explicit_binary)
        if resolved_binary is None:
            raise ValueError(f"{MARKER_BIN_ENV_VAR} is set but not executable: {explicit_binary}")
        return resolved_binary, Path(resolved_binary).name.lower()

    venv_marker_single = marker_venv_executable_path(marker_venv_dir, "marker_single")
    if command_available([str(venv_marker_single), "--help"]):
        return str(venv_marker_single), "marker_single"

    if command_available(["marker_single", "--help"]):
        return "marker_single", "marker_single"
    if command_available(["marker", "--help"]):
        return "marker", "marker"
    return None


def parse_output_formats(value: str) -> list[str]:
    raw_tokens = [token.strip().lower() for token in value.split(",")]
    formats: list[str] = []
    seen: set[str] = set()
    for token in raw_tokens:
        if not token or token in seen:
            continue
        if token not in SUPPORTED_OUTPUT_FORMATS:
            supported = ", ".join(SUPPORTED_OUTPUT_FORMATS)
            raise ValueError(f"unsupported output format: {token} (supported: {supported})")
        formats.append(token)
        seen.add(token)
    if not formats:
        raise ValueError("at least one output format must be provided")
    return formats


def resolve_processors(
    *,
    processor_profile: str,
    processors_arg: str | None,
) -> tuple[str | None, str]:
    if processors_arg and processors_arg.strip():
        return processors_arg.strip(), "cli"
    if processor_profile == PROCESSOR_PROFILE_DEFAULT:
        return None, f"profile:{PROCESSOR_PROFILE_DEFAULT}"
    if processor_profile == PROCESSOR_PROFILE_MPS_SAFE:
        return ",".join(PROCESSORS_MPS_SAFE), f"profile:{PROCESSOR_PROFILE_MPS_SAFE}"
    if processor_profile == PROCESSOR_PROFILE_MPS_WITH_TABLES:
        return ",".join(PROCESSORS_MPS_WITH_TABLES), f"profile:{PROCESSOR_PROFILE_MPS_WITH_TABLES}"
    raise ValueError(f"unsupported processor profile: {processor_profile}")


def count_output_files(output_dir: Path) -> tuple[int, int, int]:
    json_count = sum(1 for _ in output_dir.rglob("*.json"))
    markdown_count = sum(1 for _ in output_dir.rglob("*.md"))
    html_count = sum(1 for _ in output_dir.rglob("*.html"))
    return json_count, markdown_count, html_count


def print_sample_outputs(output_dir: Path) -> None:
    files = sorted(path for path in output_dir.rglob("*") if path.is_file())
    for path in files[:15]:
        print(path)


def detect_code_language(paragraph: str) -> str:
    lowered = paragraph.lower()
    if any(token in lowered for token in ("function ", "const ", "let ", "=>", "switch(")):
        return "javascript"
    if any(token in lowered for token in ("def ", "import ", "from ")) and ":" in paragraph:
        return "python"
    if "{" in paragraph and "}" in paragraph and ":" in paragraph and '"' in paragraph:
        return "json"
    return "text"


def is_code_paragraph(paragraph: str) -> bool:
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
    if len(lines) >= 2:
        return signals >= 2
    return signals >= 3


def mark_code_paragraphs(markdown_text: str) -> tuple[str, int]:
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
        if is_code_paragraph(paragraph):
            language = detect_code_language(paragraph)
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


def postprocess_markdown_code_blocks(output_dir: Path) -> tuple[int, int]:
    updated_files = 0
    marked_blocks = 0
    for markdown_path in sorted(output_dir.rglob("*.md")):
        original = markdown_path.read_text(encoding="utf-8")
        updated, marked = mark_code_paragraphs(original)
        if marked > 0 and updated != original:
            markdown_path.write_text(updated, encoding="utf-8")
            updated_files += 1
            marked_blocks += marked
    return updated_files, marked_blocks


def build_marker_command(
    *,
    marker_binary: str,
    marker_cli_name: str,
    input_path: Path,
    output_dir: Path,
    output_format: str,
    workers: int | None,
    disable_multiprocessing: bool,
    disable_image_extraction: bool,
    page_range: str | None,
    processors: str | None,
    config_json: str | None,
) -> list[str]:
    command = [
        marker_binary,
        str(input_path),
        "--output_dir",
        str(output_dir),
    ]

    command.extend(["--output_format", output_format])
    if disable_multiprocessing:
        command.append("--disable_multiprocessing")
    if disable_image_extraction:
        command.append("--disable_image_extraction")
    if workers is not None and marker_cli_name == "marker":
        command.extend(["--workers", str(workers)])
    if page_range:
        command.extend(["--page_range", page_range])
    if processors:
        command.extend(["--processors", processors])
    if config_json:
        command.extend(["--config_json", config_json])
    return command


def _print_marker_install_help(marker_venv_dir: Path) -> None:
    install_commands = build_marker_install_commands(marker_venv_dir)
    print("Try:", file=sys.stderr)
    print(f"  {shlex.join(install_commands[0])}", file=sys.stderr)
    print(f"  {shlex.join(install_commands[1])}", file=sys.stderr)
    print("or:", file=sys.stderr)
    print("  scripts/test_marker.sh --install-marker", file=sys.stderr)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)

    if shutil.which("uv") is None:
        print("Error: uv is required but not installed.", file=sys.stderr)
        return 127

    source_path = Path(args.source)
    if not source_path.is_file():
        print(f"Error: source PDF not found: {source_path}", file=sys.stderr)
        return 1
    if source_path.suffix.lower() != ".pdf":
        print(f"Error: source file must be a PDF: {source_path}", file=sys.stderr)
        return 2
    if args.workers is not None and args.workers < 1:
        print("Error: --workers must be >= 1.", file=sys.stderr)
        return 2
    try:
        output_formats = parse_output_formats(args.output_format)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    try:
        resolved_processors, processors_source = resolve_processors(
            processor_profile=args.processor_profile,
            processors_arg=args.processors,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    marker_venv_dir = resolve_marker_venv_dir(os.getenv(MARKER_VENV_ENV_VAR))

    try:
        if args.install_marker:
            print(f"Installing Marker into isolated venv: {marker_venv_dir}")
            for install_cmd in build_marker_install_commands(marker_venv_dir):
                run_cmd(install_cmd)

        print("Syncing/installing project dependencies...")
        run_cmd(["make", "install"])

        try:
            marker_selection = select_marker_binary(marker_venv_dir)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            _print_marker_install_help(marker_venv_dir)
            return 1

        if marker_selection is None:
            print(
                "Error: Marker CLI is not available. "
                f"Tried {MARKER_BIN_ENV_VAR}, {marker_venv_dir}, and PATH.",
                file=sys.stderr,
            )
            _print_marker_install_help(marker_venv_dir)
            return 1
        marker_binary, marker_cli_name = marker_selection

        run_id = datetime.now().strftime("%Y%m%dT%H%M%S")
        output_dir = Path(args.output_dir).expanduser() / run_id
        output_dir.mkdir(parents=True, exist_ok=True)

        print("Running Marker smoke test...")
        print(f"  cli={marker_cli_name}")
        print(f"  marker_binary={marker_binary}")
        print(f"  marker_venv={marker_venv_dir}")
        print(f"  source={source_path}")
        print(f"  output={output_dir}")
        print(f"  output_formats={','.join(output_formats)}")
        print(f"  processors={processors_source}")
        if (
            args.processor_profile == PROCESSOR_PROFILE_MPS_WITH_TABLES
            and processors_source.startswith("profile:")
            and os.getenv("TORCH_DEVICE", "").strip().lower() == "mps"
        ):
            print(
                "  note=Table processor enabled; "
                "Surya table recognition may fallback to CPU on mps."
            )

        def run_for_formats(input_path: Path) -> None:
            for output_format in output_formats:
                format_output_dir = output_dir / output_format
                format_output_dir.mkdir(parents=True, exist_ok=True)
                print(f"  format={output_format} -> {format_output_dir}")
                cmd = build_marker_command(
                    marker_binary=marker_binary,
                    marker_cli_name=marker_cli_name,
                    input_path=input_path,
                    output_dir=format_output_dir,
                    output_format=output_format,
                    workers=args.workers,
                    disable_multiprocessing=args.disable_multiprocessing,
                    disable_image_extraction=args.disable_image_extraction,
                    page_range=args.page_range,
                    processors=resolved_processors,
                    config_json=args.config_json,
                )
                run_cmd(cmd)

        if marker_cli_name == "marker":
            with TemporaryDirectory(prefix="docforge-marker-input.") as tmp_dir:
                staged_root = Path(tmp_dir)
                staged_pdf = staged_root / source_path.name
                shutil.copy2(source_path, staged_pdf)
                run_for_formats(staged_root)
        else:
            run_for_formats(source_path)

        markdown_dir = output_dir / "markdown"
        if args.mark_code_blocks and "markdown" in output_formats and markdown_dir.exists():
            updated_files, marked_blocks = postprocess_markdown_code_blocks(markdown_dir)
            if marked_blocks > 0:
                print(
                    "Post-processed Markdown code fences:"
                    f" files_updated={updated_files} blocks_marked={marked_blocks}"
                )

        json_count, md_count, html_count = count_output_files(output_dir)
        print("Smoke test finished.")
        print(f"  json_files={json_count}")
        print(f"  markdown_files={md_count}")
        print(f"  html_files={html_count}")
        print("  sample_output_files:")
        print_sample_outputs(output_dir)

        if json_count == 0 and md_count == 0 and html_count == 0:
            print("Error: no output artifacts were produced.", file=sys.stderr)
            return 1
        return 0

    except subprocess.CalledProcessError as exc:
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
