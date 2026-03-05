from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docforge import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="docforge", description="Project CLI entrypoint.")
    parser.add_argument("--version", action="store_true", help="Print version and exit.")

    subparsers = parser.add_subparsers(dest="command")

    experiment_parser = subparsers.add_parser(
        "experiment",
        help="Run PDF parser experiments.",
    )
    experiment_subparsers = experiment_parser.add_subparsers(
        dest="experiment_command",
        required=True,
    )
    run_parser = experiment_subparsers.add_parser(
        "run",
        help="Run the baseline experiment pipeline.",
    )
    run_parser.add_argument(
        "--source", required=True, help="Path to input file (PDF or synthetic text)."
    )
    run_parser.add_argument("--variant", required=True, help="Path to variant TOML configuration.")
    run_parser.add_argument(
        "--output-dir",
        default="artifacts",
        help="Root directory for generated artifacts.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(__version__)
        return 0

    if args.command == "experiment" and args.experiment_command == "run":
        return _run_experiment(source=args.source, variant=args.variant, output_dir=args.output_dir)

    try:
        from rich.console import Console

        console = Console(
            force_terminal=False,
            color_system=None,
            markup=False,
            highlight=False,
        )
        console.print("docforge: OK")
    except ModuleNotFoundError:
        print("docforge: OK")
    return 0


def _run_experiment(*, source: str, variant: str, output_dir: str) -> int:
    try:
        from docforge.experiment.config import VariantConfig
        from docforge.experiment.pipeline import run_baseline_pipeline

        source_path = Path(source)
        variant_path = Path(variant)
        output_root = Path(output_dir)
        loaded_variant = VariantConfig.from_toml_path(variant_path)
        result = run_baseline_pipeline(
            source_path=source_path,
            variant=loaded_variant,
            output_root=output_root,
        )
    except Exception as exc:
        print(f"docforge experiment: ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"docforge experiment: OK ({result.output_dir})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
