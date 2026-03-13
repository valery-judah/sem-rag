from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _wrapper_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "container-log-wrapper.sh"


def test_container_log_wrapper_archives_json_lines_without_changing_stdout(tmp_path: Path) -> None:
    log_path = tmp_path / "runtime.jsonl"
    command = [
        str(_wrapper_path()),
        "python",
        "-c",
        ("import json; print(json.dumps({'event': 'wrapper-test', 'service': 'api'}))"),
    ]
    env = os.environ | {"DOC_FORGE_JSON_LOG_PATH": str(log_path)}

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert completed.returncode == 0
    stdout_line = completed.stdout.strip()
    assert json.loads(stdout_line) == {"event": "wrapper-test", "service": "api"}
    assert log_path.read_text(encoding="utf-8").strip() == stdout_line


def test_container_log_wrapper_preserves_child_exit_code(tmp_path: Path) -> None:
    log_path = tmp_path / "runtime.jsonl"
    command = [
        str(_wrapper_path()),
        "python",
        "-c",
        ("import json, sys; print(json.dumps({'event': 'wrapper-test-exit'})); sys.exit(7)"),
    ]
    env = os.environ | {"DOC_FORGE_JSON_LOG_PATH": str(log_path)}

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert completed.returncode == 7
    assert json.loads(log_path.read_text(encoding="utf-8").strip()) == {
        "event": "wrapper-test-exit"
    }


def test_container_log_wrapper_filters_non_json_lines_from_archive(tmp_path: Path) -> None:
    log_path = tmp_path / "runtime.jsonl"
    command = [
        str(_wrapper_path()),
        "python",
        "-c",
        (
            "import json, sys; "
            "print('plain-text-startup-line'); "
            "print(json.dumps({'event': 'json-line'})); "
            "sys.stderr.write('plain-text-warning\\n')"
        ),
    ]
    env = os.environ | {"DOC_FORGE_JSON_LOG_PATH": str(log_path)}

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert completed.returncode == 0
    assert "plain-text-startup-line" in completed.stdout
    assert "plain-text-warning" in completed.stdout
    assert log_path.read_text(encoding="utf-8").splitlines() == [
        json.dumps({"event": "json-line"})
    ]


def test_container_log_wrapper_skips_archiving_when_path_is_empty(tmp_path: Path) -> None:
    log_path = tmp_path / "runtime.jsonl"
    command = [
        str(_wrapper_path()),
        "python",
        "-c",
        "print('no-archive')",
    ]
    env = os.environ | {"DOC_FORGE_JSON_LOG_PATH": ""}

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert completed.returncode == 0
    assert completed.stdout.strip() == "no-archive"
    assert not log_path.exists()
