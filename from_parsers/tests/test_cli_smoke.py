from __future__ import annotations

from pathlib import Path

from docforge.cli import main


def test_cli_smoke(capsys) -> None:
    code = main([])
    assert code == 0
    out = capsys.readouterr().out.strip()
    assert out == "docforge: OK"


def test_cli_version(capsys) -> None:
    code = main(["--version"])
    assert code == 0
    out = capsys.readouterr().out.strip()
    assert out


def test_rich_optional_import() -> None:
    try:
        import rich  # noqa: F401
    except ModuleNotFoundError:
        # Rich is intentionally optional until added via `make add-rich`.
        pass


def test_cli_experiment_run(tmp_path: Path, capsys) -> None:
    source_path = tmp_path / "sample.txt"
    source_path.write_text("Alpha page.\fBeta page.", encoding="utf-8")

    variant_path = tmp_path / "baseline.toml"
    variant_path.write_text(
        "\n".join(
            [
                'variant_id = "wave0-synthetic"',
                'extractor = "synthetic_text"',
            ]
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "artifacts"
    code = main(
        [
            "experiment",
            "run",
            "--source",
            str(source_path),
            "--variant",
            str(variant_path),
            "--output-dir",
            str(output_dir),
        ]
    )
    assert code == 0

    out = capsys.readouterr().out.strip()
    assert out.startswith("docforge experiment: OK")
