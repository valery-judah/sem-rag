import os
import subprocess
import sys
from unittest.mock import patch

from docforge.parsers.pdf_hybrid.engines._subprocess import run_command


def test_run_command_success():
    """Test successful command execution."""
    # Use a simple cross-platform command
    result = run_command([sys.executable, "-c", "print('hello world')"], timeout_s=5.0)

    assert result.returncode == 0
    assert result.stdout.strip() == "hello world"
    assert result.stderr == ""
    assert result.timed_out is False
    assert result.error_message is None


def test_run_command_failure():
    """Test command execution that returns a non-zero exit code."""
    result = run_command([sys.executable, "-c", "import sys; sys.exit(1)"], timeout_s=5.0)

    assert result.returncode == 1
    assert result.timed_out is False
    assert result.error_message is None


def test_run_command_timeout():
    """Test command execution that times out."""
    result = run_command([sys.executable, "-c", "import time; time.sleep(2)"], timeout_s=0.1)

    assert result.returncode is None
    assert result.timed_out is True
    assert "timed out" in result.error_message


def test_run_command_env_vars():
    """Test that environment variables are passed to the subprocess."""
    env = os.environ.copy()
    env["TEST_VAR"] = "test_value"

    result = run_command(
        [sys.executable, "-c", "import os; print(os.environ.get('TEST_VAR'))"],
        timeout_s=5.0,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "test_value"


def test_run_command_exception():
    """Test handling of unexpected exceptions (e.g., command not found)."""
    result = run_command(["nonexistent_command_that_should_fail"], timeout_s=5.0)

    assert result.returncode is None
    assert result.timed_out is False
    assert result.error_message is not None
    assert "No such file or directory" in result.error_message


@patch("subprocess.run")
def test_run_command_timeout_with_output(mock_run):
    """Test timeout when partial output is captured."""
    mock_run.side_effect = subprocess.TimeoutExpired(
        cmd=["dummy"],
        timeout=0.1,
        output="partial stdout",
        stderr="partial stderr",
    )

    result = run_command(["dummy"], timeout_s=0.1)

    assert result.returncode is None
    assert result.timed_out is True
    assert result.stdout == "partial stdout"
    assert result.stderr == "partial stderr"
