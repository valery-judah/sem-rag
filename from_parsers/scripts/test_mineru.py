#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

DEFAULT_SOURCE = "data/llm-evals-course-notes-july.pdf"
DEFAULT_OUTPUT_ROOT = "artifacts/mineru-smoke"
DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"
DEFAULT_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_DEVICE = "mps"
DEFAULT_MODELS_DIR = str(Path.home() / "models")
DEFAULT_BACKEND = "pipeline"
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
        description="Run a MinerU smoke test in this repository.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Gemini (optional, for LLM-aided title extraction):\n"
            "  GEMINI_API_KEY or GOOGLE_API_KEY\n"
            f"  GEMINI_MODEL (default: {DEFAULT_GEMINI_MODEL})\n"
            f"  GEMINI_BASE_URL (default: {DEFAULT_GEMINI_BASE_URL})\n"
            "\n"
            "Runtime knobs:\n"
            f"  DOCFORGE_MINERU_DEVICE (default: {DEFAULT_DEVICE})\n"
            f"  DOCFORGE_MINERU_MODELS_DIR (default: {DEFAULT_MODELS_DIR})\n"
            f"  DOCFORGE_MINERU_BACKEND (default: {DEFAULT_BACKEND})"
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
        "--install-mineru",
        action="store_true",
        help='Install/upgrade MinerU in this repo via uv add "mineru[all]"',
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=None,
        help="Start page index (0-based, inclusive).",
    )
    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help="End page index (0-based, inclusive).",
    )
    parser.add_argument(
        "--mark-code-blocks",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Post-process output Markdown and fence detected code paragraphs (default: enabled)."
        ),
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


def select_mineru_cli() -> str | None:
    if command_available(["uv", "run", "mineru", "--help"]):
        return "mineru"
    return None


def normalize_models_dir(value: str | None) -> str:
    if value and value.strip():
        return value.strip()
    return DEFAULT_MODELS_DIR


def write_mineru_config(
    config_path: Path,
    *,
    device: str,
    models_dir: str,
    mineru_cli: str,
    gemini_key: str | None,
    gemini_model: str,
    gemini_base_url: str,
) -> None:
    payload: dict[str, object] = {
        "device-mode": device,
        "table-config": {"enable": True, "max_time": 400},
        "formula-config": {"enable": True},
        "layout-config": {},
        "bucket_info": {"[default]": ["", "", ""]},
    }

    payload["models-dir"] = {"pipeline": models_dir, "vlm": models_dir}

    if gemini_key:
        shared_llm = {
            "api_key": gemini_key,
            "model": gemini_model,
            "base_url": gemini_base_url,
        }
        payload["llm-aided-config"] = {
            "enable": True,
            **shared_llm,
            "title_aided": dict(shared_llm),
        }

    config_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def count_output_files(output_dir: Path) -> tuple[int, int]:
    json_count = sum(1 for _ in output_dir.rglob("*.json"))
    markdown_count = sum(1 for _ in output_dir.rglob("*.md"))
    return json_count, markdown_count


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


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)

    if shutil.which("uv") is None:
        print("Error: uv is required but not installed.", file=sys.stderr)
        return 127

    source_path = Path(args.source)
    if not source_path.is_file():
        print(f"Error: source PDF not found: {source_path}", file=sys.stderr)
        return 1
    if args.start_page is not None and args.start_page < 0:
        print("Error: --start-page must be >= 0.", file=sys.stderr)
        return 2
    if args.end_page is not None and args.end_page < 0:
        print("Error: --end-page must be >= 0.", file=sys.stderr)
        return 2
    if (
        args.start_page is not None
        and args.end_page is not None
        and args.start_page > args.end_page
    ):
        print("Error: --start-page cannot be greater than --end-page.", file=sys.stderr)
        return 2

    try:
        if args.install_mineru:
            print("Installing MinerU into the repo environment...")
            run_cmd(["uv", "add", "mineru[all]"])

        print("Syncing/installing project dependencies...")
        run_cmd(["make", "install"])

        mineru_cli = select_mineru_cli()
        if not mineru_cli:
            print(
                "Error: `mineru` CLI is not available in the uv environment.",
                file=sys.stderr,
            )
            print("Try:", file=sys.stderr)
            print("  scripts/test_mineru.sh --install-mineru", file=sys.stderr)
            return 1

        env = os.environ.copy()
        env.setdefault("DOCFORGE_MINERU_DEVICE", DEFAULT_DEVICE)
        env.setdefault("DOCFORGE_MINERU_BACKEND", DEFAULT_BACKEND)
        env.setdefault("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        env.setdefault("GEMINI_BASE_URL", DEFAULT_GEMINI_BASE_URL)
        env["DOCFORGE_MINERU_CLI"] = mineru_cli

        run_id = datetime.now().strftime("%Y%m%dT%H%M%S")
        output_dir = Path(args.output_dir).expanduser() / run_id
        output_dir.mkdir(parents=True, exist_ok=True)

        models_dir = normalize_models_dir(env.get("DOCFORGE_MINERU_MODELS_DIR"))

        with TemporaryDirectory(prefix="docforge-mineru-smoke.") as tmp_dir:
            config_path = Path(tmp_dir) / "mineru-config.json"
            env["MINERU_TOOLS_CONFIG_JSON"] = str(config_path)

            gemini_key = env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY")
            write_mineru_config(
                config_path,
                device=env["DOCFORGE_MINERU_DEVICE"],
                models_dir=models_dir,
                mineru_cli=mineru_cli,
                gemini_key=gemini_key,
                gemini_model=env["GEMINI_MODEL"],
                gemini_base_url=env["GEMINI_BASE_URL"],
            )

            expected_model = Path(models_dir) / "MFD/YOLO/yolo_v8_ft.pt"
            if not expected_model.is_file():
                print(f"Warning: MinerU model weights were not found at: {models_dir}")
                print(f"  expected file: {expected_model}")
                print("  model download command:")
                print(f'  uv run mineru-models-download --output-dir "{models_dir}"')
                print("  or:")
                print(
                    "  uv run mineru-models-download --source huggingface "
                    f'--output-dir "{models_dir}"'
                )
                if not command_available(["uv", "run", "mineru-models-download", "--help"]):
                    print("  If you install the official MinerU CLI, run:")
                    print(f'  uv run mineru-models-download --output-dir "{models_dir}"')
                    print("  or:")
                    print(
                        "  uv run mineru-models-download --source huggingface "
                        f'--output-dir "{models_dir}"'
                    )

            cmd = [
                "uv",
                "run",
                "mineru",
                "-p",
                str(source_path),
                "-o",
                str(output_dir),
                "-b",
                env["DOCFORGE_MINERU_BACKEND"],
            ]
            if args.start_page is not None:
                cmd.extend(["-s", str(args.start_page)])
            if args.end_page is not None:
                cmd.extend(["-e", str(args.end_page)])

            print("Running MinerU smoke test...")
            print(f"  cli={mineru_cli}")
            print(f"  source={source_path}")
            print(f"  output={output_dir}")
            if gemini_key:
                print(f"  gemini_model={env['GEMINI_MODEL']}")
            else:
                print("  gemini_model=disabled (set GEMINI_API_KEY or GOOGLE_API_KEY to enable)")

            run_cmd(cmd, env=env)

        if args.mark_code_blocks:
            updated_files, marked_blocks = postprocess_markdown_code_blocks(output_dir)
            if marked_blocks > 0:
                print(
                    "Post-processed Markdown code fences:"
                    f" files_updated={updated_files} blocks_marked={marked_blocks}"
                )

        json_count, md_count = count_output_files(output_dir)
        print("Smoke test finished.")
        print(f"  json_files={json_count}")
        print(f"  markdown_files={md_count}")
        print("  sample_output_files:")
        print_sample_outputs(output_dir)

        if json_count == 0 and md_count == 0:
            print("Error: no JSON/Markdown outputs were produced.", file=sys.stderr)
            return 1
        return 0

    except subprocess.CalledProcessError as exc:
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
