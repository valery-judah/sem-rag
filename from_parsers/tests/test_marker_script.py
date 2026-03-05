from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _load_marker_script_module() -> ModuleType:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "test_marker.py"
    spec = importlib.util.spec_from_file_location("docforge_test_marker_script", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_marker_install_commands_posix() -> None:
    marker_script = _load_marker_script_module()

    commands = marker_script.build_marker_install_commands(
        Path("/tmp/marker-venv"),
        windows=False,
    )

    assert commands == [
        ["uv", "venv", "/tmp/marker-venv", "--allow-existing"],
        [
            "uv",
            "pip",
            "install",
            "--python",
            "/tmp/marker-venv/bin/python",
            "marker-pdf[full]",
        ],
    ]


def test_build_marker_install_commands_windows() -> None:
    marker_script = _load_marker_script_module()

    commands = marker_script.build_marker_install_commands(
        Path("C:/repo/.venvs/marker"),
        windows=True,
    )

    assert commands == [
        ["uv", "venv", "C:/repo/.venvs/marker", "--allow-existing"],
        [
            "uv",
            "pip",
            "install",
            "--python",
            "C:/repo/.venvs/marker/Scripts/python.exe",
            "marker-pdf[full]",
        ],
    ]


def test_resolve_marker_venv_dir_defaults_to_project_root() -> None:
    marker_script = _load_marker_script_module()
    marker_script.PROJECT_ROOT = Path("/repo")

    assert marker_script.resolve_marker_venv_dir(None) == Path("/repo/.venvs/marker")


def test_select_marker_binary_prefers_venv_candidate_over_path() -> None:
    marker_script = _load_marker_script_module()
    marker_venv = Path("/repo/.venvs/marker")
    expected_binary = marker_venv / "bin" / "marker_single"

    def fake_available(cmd: list[str]) -> bool:
        return cmd[0] == str(expected_binary) or cmd[0] == "marker_single"

    marker_script.command_available = fake_available

    marker_binary, marker_cli_name = marker_script.select_marker_binary(marker_venv, environ={})

    assert marker_binary == str(expected_binary)
    assert marker_cli_name == "marker_single"


def test_select_marker_binary_errors_for_invalid_env_override() -> None:
    marker_script = _load_marker_script_module()
    marker_script._resolve_explicit_marker_binary = lambda _: None

    with pytest.raises(ValueError, match="DOCFORGE_MARKER_BIN"):
        marker_script.select_marker_binary(
            Path("/repo/.venvs/marker"),
            environ={"DOCFORGE_MARKER_BIN": "/does/not/exist"},
        )


def test_resolve_processors_default_profile_returns_none() -> None:
    marker_script = _load_marker_script_module()

    processors, source = marker_script.resolve_processors(
        processor_profile=marker_script.PROCESSOR_PROFILE_DEFAULT,
        processors_arg=None,
    )

    assert processors is None
    assert source == "profile:default"


def test_resolve_processors_mps_safe_profile_excludes_table_processor() -> None:
    marker_script = _load_marker_script_module()

    processors, source = marker_script.resolve_processors(
        processor_profile=marker_script.PROCESSOR_PROFILE_MPS_SAFE,
        processors_arg=None,
    )

    assert processors is not None
    assert "marker.processors.table.TableProcessor" not in processors
    assert source == "profile:mps-safe"


def test_resolve_processors_mps_with_tables_profile_includes_table_processor() -> None:
    marker_script = _load_marker_script_module()

    processors, source = marker_script.resolve_processors(
        processor_profile=marker_script.PROCESSOR_PROFILE_MPS_WITH_TABLES,
        processors_arg=None,
    )

    assert processors is not None
    assert "marker.processors.table.TableProcessor" in processors
    assert source == "profile:mps-with-tables"


def test_resolve_processors_prefers_cli_override_over_profile() -> None:
    marker_script = _load_marker_script_module()

    processors, source = marker_script.resolve_processors(
        processor_profile=marker_script.PROCESSOR_PROFILE_MPS_WITH_TABLES,
        processors_arg="custom.processor.Foo,custom.processor.Bar",
    )

    assert processors == "custom.processor.Foo,custom.processor.Bar"
    assert source == "cli"
