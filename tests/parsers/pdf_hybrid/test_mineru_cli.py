import json
from pathlib import Path
from unittest.mock import patch

import pytest

from docforge.parsers.pdf_hybrid.engines._subprocess import SubprocessResult
from docforge.parsers.pdf_hybrid.engines.mineru_cli import (
    MineruRunner,
    _select_mineru_json_payload,
)
from docforge.parsers.pdf_hybrid.engines.run_manifest import EngineRunManifest


@pytest.fixture
def temp_output_dir(tmp_path: Path):
    d = tmp_path / "output"
    d.mkdir()
    return d


@pytest.fixture
def mock_run_command():
    with patch("docforge.parsers.pdf_hybrid.engines.mineru_cli.run_command") as mock:
        yield mock


@pytest.fixture
def mock_discover():
    with patch.object(MineruRunner, "discover", return_value="/mock/bin/mineru") as mock:
        yield mock


class TestMineruPayloadSelection:
    def test_select_mineru_content_list(self, temp_output_dir):
        (temp_output_dir / "mineru_config.json").write_text("{}")
        (temp_output_dir / "test_middle.json").write_text('{"middle": true}')

        target = temp_output_dir / "test_content_list.json"
        target.write_text('{"content": true}')

        # Should prefer content_list even if middle is present
        assert _select_mineru_json_payload(temp_output_dir) == target

    def test_select_mineru_middle(self, temp_output_dir):
        (temp_output_dir / "mineru_config.json").write_text("{}")
        (temp_output_dir / "test.json").write_text('{"test": true}')

        target = temp_output_dir / "test_middle.json"
        target.write_text('{"middle": true}')

        # Should prefer middle over regular json
        assert _select_mineru_json_payload(temp_output_dir) == target

    def test_select_mineru_largest_json(self, temp_output_dir):
        (temp_output_dir / "mineru_config.json").write_text("{}")

        payload1 = temp_output_dir / "test.json"
        payload1.write_text('{"small": true}')

        payload2 = temp_output_dir / "large.json"
        payload2.write_text('{"large": ' + "true" * 100 + "}")

        # Should prefer largest non-config json
        assert _select_mineru_json_payload(temp_output_dir) == payload2

    def test_select_mineru_no_json(self, temp_output_dir):
        (temp_output_dir / "mineru_config.json").write_text("{}")
        with pytest.raises(RuntimeError, match="did not produce JSON output"):
            _select_mineru_json_payload(temp_output_dir)


class TestMineruRunnerDiscovery:
    @patch.dict("os.environ", {"DOCFORGE_MINERU_BIN": "/custom/path/mineru"})
    @patch("os.path.exists", return_value=True)
    def test_discover_env_bin(self, mock_exists):
        runner = MineruRunner()
        assert runner.discover() == "/custom/path/mineru"

    @patch.dict("os.environ", clear=True)
    @patch("pathlib.Path.exists", return_value=True)
    def test_discover_venv_mineru(self, mock_exists):
        runner = MineruRunner()
        assert runner.discover() == "tools/mineru/.venv/bin/mineru"

    @patch.dict("os.environ", clear=True)
    @patch("pathlib.Path.exists", return_value=False)
    @patch(
        "shutil.which",
        side_effect=lambda x: "/usr/bin/mineru" if x == "mineru" else None,
    )
    def test_discover_path_mineru(self, mock_which, mock_exists):
        runner = MineruRunner()
        assert runner.discover() == "/usr/bin/mineru"

    @patch.dict("os.environ", clear=True)
    @patch("pathlib.Path.exists", return_value=False)
    @patch("shutil.which", return_value=None)
    def test_discover_not_found(self, mock_which, mock_exists):
        runner = MineruRunner()
        assert runner.discover() is None

    def test_discover_override(self):
        runner = MineruRunner(override_binary_path="/my/bin/mineru")
        assert runner.discover() == "/my/bin/mineru"


class TestMineruRunnerVersion:
    def test_get_version_success_stdout(self, mock_run_command, mock_discover):
        mock_run_command.return_value = SubprocessResult(
            returncode=0, stdout="mineru 1.2.3\n", stderr="", timed_out=False, error_message=None
        )
        runner = MineruRunner()
        assert runner.get_version() == "1.2.3"

    def test_get_version_fallback_stderr(self, mock_run_command, mock_discover):
        mock_run_command.side_effect = [
            SubprocessResult(
                returncode=1, stdout="", stderr="error", timed_out=False, error_message=None
            ),
            SubprocessResult(
                returncode=0,
                stdout="",
                stderr="Version: 4.5.6",
                timed_out=False,
                error_message=None,
            ),
        ]
        runner = MineruRunner()
        assert runner.get_version() == "4.5.6"

    def test_get_version_not_found(self, mock_run_command, mock_discover):
        mock_run_command.return_value = SubprocessResult(
            returncode=0, stdout="unknown", stderr="unknown", timed_out=False, error_message=None
        )
        runner = MineruRunner()
        assert runner.get_version() is None


class TestMineruRunnerRun:
    @patch.object(MineruRunner, "get_version", return_value="1.0.0")
    def test_run_success_modern(
        self, mock_version, mock_run_command, mock_discover, temp_output_dir
    ):
        def write_dummy_json(*args, **kwargs):
            (temp_output_dir / "result_content_list.json").write_text('{"success": true}')
            return SubprocessResult(
                returncode=0, stdout="done", stderr="", timed_out=False, error_message=None
            )

        mock_run_command.side_effect = write_dummy_json

        runner = MineruRunner()
        manifest = runner.run(
            Path("dummy.pdf"), temp_output_dir, timeout_s=10, start_page=1, end_page=2
        )

        assert manifest.status == "ok"
        assert manifest.engine_name == "mineru"
        assert manifest.version == "1.0.0"
        assert manifest.raw_output_dir == str(temp_output_dir)
        assert manifest.stdout == "done"

        # Verify command and config
        call_args = mock_run_command.call_args
        cmd = call_args.args[0]
        env = call_args.kwargs["env"]

        assert "-p" in cmd
        assert "-o" in cmd
        assert "-b" in cmd
        assert "pipeline" in cmd
        assert "-s" in cmd
        assert "1" in cmd
        assert "-e" in cmd
        assert "2" in cmd

        config_path = Path(env["MINERU_TOOLS_CONFIG_JSON"])
        assert config_path.exists()

        with open(config_path) as f:
            config = json.load(f)
            assert "pipeline" in config["models-dir"]

    @patch.object(MineruRunner, "get_version", return_value="1.0.0")
    def test_run_timeout(self, mock_version, mock_run_command, mock_discover, temp_output_dir):
        mock_run_command.return_value = SubprocessResult(
            returncode=None, stdout="", stderr="", timed_out=True, error_message="Timeout"
        )

        runner = MineruRunner()
        manifest = runner.run(Path("dummy.pdf"), temp_output_dir, timeout_s=10)

        assert manifest.status == "timeout"
        assert manifest.error_details == "Timeout"

    @patch.object(MineruRunner, "get_version", return_value="1.0.0")
    def test_run_crash(self, mock_version, mock_run_command, mock_discover, temp_output_dir):
        mock_run_command.return_value = SubprocessResult(
            returncode=1, stdout="", stderr="OOM Error", timed_out=False, error_message=None
        )

        runner = MineruRunner()
        manifest = runner.run(Path("dummy.pdf"), temp_output_dir, timeout_s=10)

        assert manifest.status == "error"
        assert manifest.stderr == "OOM Error"

    def test_run_unavailable(self):
        with patch.object(MineruRunner, "discover", return_value=None):
            runner = MineruRunner()
            manifest = runner.run(Path("dummy.pdf"), Path("out"), timeout_s=10)
            assert manifest.status == "unavailable"


class TestMineruRunnerLoadAndAdapt:
    def test_load_and_adapt_not_ok(self):
        runner = MineruRunner()
        manifest = EngineRunManifest(engine_name="mineru", status="error")
        assert runner.load_and_adapt(manifest) == []

    @patch("docforge.parsers.pdf_hybrid.engines.mineru_cli.adapt_mineru_output")
    def test_load_and_adapt_success(self, mock_adapt, temp_output_dir):
        # Setup dummy json
        payload = temp_output_dir / "result_content_list.json"
        payload.write_text('{"test": "data"}')

        mock_adapt.return_value = ["fake_candidate"]

        runner = MineruRunner()
        manifest = EngineRunManifest(
            engine_name="mineru", status="ok", raw_output_dir=str(temp_output_dir)
        )

        candidates = runner.load_and_adapt(manifest)

        assert candidates == ["fake_candidate"]
        mock_adapt.assert_called_once()
        assert mock_adapt.call_args.args[0] == {"test": "data"}
