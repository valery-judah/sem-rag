from __future__ import annotations

import json
from pathlib import Path

from docforge.experiment.extractors import (
    _build_mineru_command,
    _marker_venv_executable_path,
    _marker_venv_python_path,
    _resolve_marker_binary,
    _resolve_marker_venv_dir,
    _resolve_mineru_binary,
    _write_mineru_config,
)


def test_resolve_mineru_binary_prefers_modern_cli(monkeypatch) -> None:
    def fake_which(name: str) -> str | None:
        if name == "mineru":
            return "/usr/local/bin/mineru"
        return None

    monkeypatch.setattr("docforge.experiment.extractors.shutil.which", fake_which)

    assert _resolve_mineru_binary() == "/usr/local/bin/mineru"


def test_marker_venv_executable_path_posix() -> None:
    venv_dir = Path("/tmp/marker-venv")
    assert _marker_venv_executable_path(venv_dir, "marker_single", windows=False) == Path(
        "/tmp/marker-venv/bin/marker_single"
    )
    assert _marker_venv_python_path(venv_dir, windows=False) == Path("/tmp/marker-venv/bin/python")


def test_marker_venv_executable_path_windows() -> None:
    venv_dir = Path("/tmp/marker-venv")
    assert _marker_venv_executable_path(venv_dir, "marker_single", windows=True) == Path(
        "/tmp/marker-venv/Scripts/marker_single.exe"
    )
    assert _marker_venv_python_path(venv_dir, windows=True) == Path(
        "/tmp/marker-venv/Scripts/python.exe"
    )


def test_resolve_marker_venv_dir_defaults_to_repo_relative(monkeypatch) -> None:
    monkeypatch.delenv("DOCFORGE_MARKER_VENV", raising=False)
    monkeypatch.setattr("docforge.experiment.extractors.PROJECT_ROOT", Path("/repo"))

    assert _resolve_marker_venv_dir() == Path("/repo/.venvs/marker")


def test_resolve_marker_binary_prefers_option(monkeypatch) -> None:
    monkeypatch.delenv("DOCFORGE_MARKER_BIN", raising=False)

    assert (
        _resolve_marker_binary({"binary": "/custom/bin/marker_single"})
        == "/custom/bin/marker_single"
    )


def test_resolve_marker_binary_prefers_env_override(monkeypatch) -> None:
    monkeypatch.setenv("DOCFORGE_MARKER_BIN", "/env/bin/marker_single")

    assert _resolve_marker_binary() == "/env/bin/marker_single"


def test_resolve_marker_binary_prefers_repo_venv(monkeypatch, tmp_path: Path) -> None:
    marker_venv = tmp_path / "marker-venv"
    marker_binary = marker_venv / "bin" / "marker_single"
    marker_binary.parent.mkdir(parents=True, exist_ok=True)
    marker_binary.write_text("", encoding="utf-8")

    monkeypatch.setenv("DOCFORGE_MARKER_VENV", str(marker_venv))
    monkeypatch.delenv("DOCFORGE_MARKER_BIN", raising=False)
    monkeypatch.setattr(
        "docforge.experiment.extractors.shutil.which", lambda _: "/usr/local/bin/marker"
    )

    assert _resolve_marker_binary() == str(marker_binary)


def test_resolve_marker_binary_falls_back_to_marker_single_in_path(
    monkeypatch, tmp_path: Path
) -> None:
    marker_venv = tmp_path / "missing-venv"
    monkeypatch.setenv("DOCFORGE_MARKER_VENV", str(marker_venv))
    monkeypatch.delenv("DOCFORGE_MARKER_BIN", raising=False)

    def fake_which(name: str) -> str | None:
        if name == "marker_single":
            return "/usr/local/bin/marker_single"
        return None

    monkeypatch.setattr("docforge.experiment.extractors.shutil.which", fake_which)

    assert _resolve_marker_binary() == "/usr/local/bin/marker_single"


def test_resolve_marker_binary_falls_back_to_marker_in_path(monkeypatch, tmp_path: Path) -> None:
    marker_venv = tmp_path / "missing-venv"
    monkeypatch.setenv("DOCFORGE_MARKER_VENV", str(marker_venv))
    monkeypatch.delenv("DOCFORGE_MARKER_BIN", raising=False)

    def fake_which(name: str) -> str | None:
        if name == "marker":
            return "/usr/local/bin/marker"
        return None

    monkeypatch.setattr("docforge.experiment.extractors.shutil.which", fake_which)

    assert _resolve_marker_binary() == "/usr/local/bin/marker"


def test_resolve_marker_binary_returns_none_when_unavailable(monkeypatch, tmp_path: Path) -> None:
    marker_venv = tmp_path / "missing-venv"
    monkeypatch.setenv("DOCFORGE_MARKER_VENV", str(marker_venv))
    monkeypatch.delenv("DOCFORGE_MARKER_BIN", raising=False)
    monkeypatch.setattr("docforge.experiment.extractors.shutil.which", lambda _: None)

    assert _resolve_marker_binary() is None


def test_build_mineru_command_for_modern_cli_defaults_to_pipeline(monkeypatch) -> None:
    monkeypatch.delenv("DOCFORGE_MINERU_BACKEND", raising=False)

    command = _build_mineru_command(
        binary="/usr/local/bin/mineru",
        source_path=Path("/tmp/input.pdf"),
        output_dir=Path("/tmp/out"),
        options={},
    )

    assert command == [
        "/usr/local/bin/mineru",
        "-p",
        "/tmp/input.pdf",
        "-o",
        "/tmp/out",
        "-b",
        "pipeline",
    ]


def test_write_mineru_config_includes_gemini_settings(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("GEMINI_BASE_URL", "https://example.com/openai/")
    monkeypatch.delenv("DOCFORGE_MINERU_MODELS_DIR", raising=False)

    config_path = tmp_path / "mineru_config.json"
    _write_mineru_config(config_path)

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    expected_models_dir = str(Path.home() / "models")
    assert payload["models-dir"] == {
        "pipeline": expected_models_dir,
        "vlm": expected_models_dir,
    }
    llm_config = payload["llm-aided-config"]
    assert llm_config["enable"] is True
    assert llm_config["api_key"] == "test-key"
    assert llm_config["model"] == "gemini-2.5-flash"
    assert llm_config["base_url"] == "https://example.com/openai/"
    assert llm_config["title_aided"] == {
        "api_key": "test-key",
        "model": "gemini-2.5-flash",
        "base_url": "https://example.com/openai/",
    }


def test_write_mineru_config_uses_explicit_models_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DOCFORGE_MINERU_MODELS_DIR", "/tmp/mineru-models")

    config_path = tmp_path / "mineru.json"
    _write_mineru_config(config_path)

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["models-dir"] == {
        "pipeline": "/tmp/mineru-models",
        "vlm": "/tmp/mineru-models",
    }
