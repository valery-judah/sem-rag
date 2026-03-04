from pathlib import Path
from unittest.mock import patch

import pytest

from docforge.parsers.pdf_hybrid.engines._subprocess import SubprocessResult
from docforge.parsers.pdf_hybrid.engines.marker_cli import (
    MarkerRunner,
    _select_marker_json_payload,
)
from docforge.parsers.pdf_hybrid.engines.run_manifest import EngineRunManifest


@pytest.fixture
def temp_output_dir(tmp_path: Path):
    d = tmp_path / "output"
    d.mkdir()
    return d


@pytest.fixture
def mock_run_command():
    with patch("docforge.parsers.pdf_hybrid.engines.marker_cli.run_command") as mock:
        yield mock


@pytest.fixture
def mock_discover():
    with patch.object(MarkerRunner, "discover", return_value="/mock/bin/marker") as mock:
        yield mock


def test_select_marker_json_payload(temp_output_dir):
    # Setup some dummy files
    (temp_output_dir / "test_meta.json").write_text("{}")

    payload1 = temp_output_dir / "test.json"
    payload1.write_text('{"small": true}')

    payload2 = temp_output_dir / "large.json"
    payload2.write_text('{"large": ' + "true" * 100 + "}")

    # It should pick the largest non-meta JSON file
    selected = _select_marker_json_payload(temp_output_dir)
    assert selected == payload2


def test_select_marker_json_payload_no_json(temp_output_dir):
    with pytest.raises(RuntimeError, match="did not produce JSON output"):
        _select_marker_json_payload(temp_output_dir)


class TestMarkerRunnerDiscovery:
    @patch.dict("os.environ", {"DOCFORGE_MARKER_BIN": "/custom/path/marker"})
    @patch("os.path.exists", return_value=True)
    def test_discover_env_bin(self, mock_exists):
        runner = MarkerRunner()
        assert runner.discover() == "/custom/path/marker"

    @patch.dict("os.environ", clear=True)
    @patch("pathlib.Path.exists", return_value=True)
    def test_discover_venv(self, mock_exists):
        runner = MarkerRunner()
        assert runner.discover() == "tools/marker/.venv/bin/marker_single"

    @patch.dict("os.environ", clear=True)
    @patch("pathlib.Path.exists", return_value=False)
    @patch(
        "shutil.which",
        side_effect=lambda x: "/usr/bin/marker_single" if x == "marker_single" else None,
    )
    def test_discover_path_single(self, mock_which, mock_exists):
        runner = MarkerRunner()
        assert runner.discover() == "/usr/bin/marker_single"

    @patch.dict("os.environ", clear=True)
    @patch("pathlib.Path.exists", return_value=False)
    @patch("shutil.which", side_effect=lambda x: "/usr/bin/marker" if x == "marker" else None)
    def test_discover_path_standard(self, mock_which, mock_exists):
        runner = MarkerRunner()
        assert runner.discover() == "/usr/bin/marker"

    @patch.dict("os.environ", clear=True)
    @patch("pathlib.Path.exists", return_value=False)
    @patch("shutil.which", return_value=None)
    def test_discover_not_found(self, mock_which, mock_exists):
        runner = MarkerRunner()
        assert runner.discover() is None

    def test_discover_override(self):
        runner = MarkerRunner(override_binary_path="/my/bin/marker")
        assert runner.discover() == "/my/bin/marker"


class TestMarkerRunnerVersion:
    def test_get_version_success(self, mock_run_command, mock_discover):
        mock_run_command.return_value = SubprocessResult(
            returncode=0, stdout="marker 1.2.3\n", stderr="", timed_out=False, error_message=None
        )
        runner = MarkerRunner()
        assert runner.get_version() == "1.2.3"

    def test_get_version_fallback_stderr(self, mock_run_command, mock_discover):
        mock_run_command.return_value = SubprocessResult(
            returncode=0, stdout="", stderr="Version: 4.5.6", timed_out=False, error_message=None
        )
        runner = MarkerRunner()
        assert runner.get_version() == "4.5.6"

    def test_get_version_not_found(self, mock_run_command, mock_discover):
        mock_run_command.return_value = SubprocessResult(
            returncode=0, stdout="unknown", stderr="unknown", timed_out=False, error_message=None
        )
        runner = MarkerRunner()
        assert runner.get_version() is None


class TestMarkerRunnerRun:
    @patch.object(MarkerRunner, "get_version", return_value="1.0.0")
    def test_run_success(self, mock_version, mock_run_command, mock_discover, temp_output_dir):
        def write_dummy_json(*args, **kwargs):
            (temp_output_dir / "result.json").write_text('{"success": true}')
            return SubprocessResult(
                returncode=0, stdout="done", stderr="", timed_out=False, error_message=None
            )

        mock_run_command.side_effect = write_dummy_json

        runner = MarkerRunner()
        manifest = runner.run(Path("dummy.pdf"), temp_output_dir, timeout_s=10)

        assert manifest.status == "ok"
        assert manifest.engine_name == "marker"
        assert manifest.version == "1.0.0"
        assert manifest.raw_output_dir == str(temp_output_dir)
        assert manifest.stdout == "done"

        # Verify environment injection
        call_args = mock_run_command.call_args
        env = call_args.kwargs["env"]
        assert env["TORCH_DEVICE"] == "cpu"
        assert env["PYTORCH_ALLOC_CONF"] == "expandable_segments:True"

        # Verify required args
        cmd = call_args.args[0]
        assert "--output_dir" in cmd
        assert "--output_format" in cmd
        assert "json" in cmd
        assert "markdown" in cmd

    @patch.object(MarkerRunner, "get_version", return_value="1.0.0")
    def test_run_with_env_overrides(
        self, mock_version, mock_run_command, mock_discover, temp_output_dir
    ):
        def write_dummy_json(*args, **kwargs):
            (temp_output_dir / "result.json").write_text('{"success": true}')
            return SubprocessResult(
                returncode=0, stdout="done", stderr="", timed_out=False, error_message=None
            )

        mock_run_command.side_effect = write_dummy_json

        runner = MarkerRunner(env_overrides={"TORCH_DEVICE": "mps", "INFERENCE_RAM": "24"})
        manifest = runner.run(Path("dummy.pdf"), temp_output_dir, timeout_s=10)

        assert manifest.status == "ok"
        call_args = mock_run_command.call_args
        env = call_args.kwargs["env"]
        assert env["TORCH_DEVICE"] == "mps"
        assert env["INFERENCE_RAM"] == "24"
        assert env["PYTORCH_ALLOC_CONF"] == "expandable_segments:True"

    @patch.object(MarkerRunner, "get_version", return_value="1.0.0")
    def test_run_timeout(self, mock_version, mock_run_command, mock_discover, temp_output_dir):
        mock_run_command.return_value = SubprocessResult(
            returncode=None, stdout="", stderr="", timed_out=True, error_message="Timeout"
        )

        runner = MarkerRunner()
        manifest = runner.run(Path("dummy.pdf"), temp_output_dir, timeout_s=10)

        assert manifest.status == "timeout"
        assert manifest.error_details == "Timeout"

    @patch.object(MarkerRunner, "get_version", return_value="1.0.0")
    def test_run_crash(self, mock_version, mock_run_command, mock_discover, temp_output_dir):
        mock_run_command.return_value = SubprocessResult(
            returncode=1, stdout="", stderr="OOM Error", timed_out=False, error_message=None
        )

        runner = MarkerRunner()
        manifest = runner.run(Path("dummy.pdf"), temp_output_dir, timeout_s=10)

        assert manifest.status == "error"
        assert manifest.stderr == "OOM Error"

    def test_run_unavailable(self):
        with patch.object(MarkerRunner, "discover", return_value=None):
            runner = MarkerRunner()
            manifest = runner.run(Path("dummy.pdf"), Path("out"), timeout_s=10)
            assert manifest.status == "unavailable"

    @patch.object(MarkerRunner, "get_version", return_value="1.0.0")
    def test_run_no_json_output(
        self, mock_version, mock_run_command, mock_discover, temp_output_dir
    ):
        # Return 0 but do not create any JSON file
        mock_run_command.return_value = SubprocessResult(
            returncode=0, stdout="done", stderr="", timed_out=False, error_message=None
        )

        runner = MarkerRunner()
        manifest = runner.run(Path("dummy.pdf"), temp_output_dir, timeout_s=10)

        assert manifest.status == "error"
        assert "did not produce JSON output" in manifest.error_details


class TestMarkerRunnerLoadAndAdapt:
    def test_load_and_adapt_not_ok(self):
        runner = MarkerRunner()
        manifest = EngineRunManifest(engine_name="marker", status="error")
        assert runner.load_and_adapt(manifest) == []

    @patch("docforge.parsers.pdf_hybrid.engines.marker_cli.adapt_marker_output")
    def test_load_and_adapt_success(self, mock_adapt, temp_output_dir):
        # Setup dummy json
        payload = temp_output_dir / "result.json"
        payload.write_text('{"test": "data"}')

        mock_adapt.return_value = ["fake_candidate"]

        runner = MarkerRunner()
        manifest = EngineRunManifest(
            engine_name="marker", status="ok", raw_output_dir=str(temp_output_dir)
        )

        candidates = runner.load_and_adapt(manifest)

        assert candidates == ["fake_candidate"]
        mock_adapt.assert_called_once()
        assert mock_adapt.call_args.args[0] == {"test": "data"}

    def test_load_and_adapt_no_dir(self):
        runner = MarkerRunner()
        manifest = EngineRunManifest(engine_name="marker", status="ok", raw_output_dir=None)
        assert runner.load_and_adapt(manifest) == []
