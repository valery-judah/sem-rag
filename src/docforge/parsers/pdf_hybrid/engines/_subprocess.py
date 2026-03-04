import subprocess


class SubprocessResult:
    def __init__(
        self,
        returncode: int | None,
        stdout: str,
        stderr: str,
        timed_out: bool,
        error_message: str | None,
    ):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out
        self.error_message = error_message


def run_command(
    cmd: list[str],
    timeout_s: float,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> SubprocessResult:
    """
    Executes a command and returns a normalized result, catching TimeoutExpired
    and other exceptions. Accepts optional env overrides.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=cwd,
            env=env,
            check=False,
            encoding="utf-8",
        )
        return SubprocessResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=False,
            error_message=None,
        )
    except subprocess.TimeoutExpired as e:
        return SubprocessResult(
            returncode=None,
            stdout=e.stdout.decode("utf-8") if isinstance(e.stdout, bytes) else (e.stdout or ""),
            stderr=e.stderr.decode("utf-8") if isinstance(e.stderr, bytes) else (e.stderr or ""),
            timed_out=True,
            error_message=f"Command timed out after {timeout_s} seconds",
        )
    except Exception as e:
        return SubprocessResult(
            returncode=None,
            stdout="",
            stderr="",
            timed_out=False,
            error_message=str(e),
        )
