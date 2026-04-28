from __future__ import annotations

from pathlib import Path

from doc_forge.devtools import repo_clean


def test_build_cleanup_plan_includes_generated_state_and_preserves_inputs(tmp_path: Path) -> None:
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".coverage").write_text("data", encoding="utf-8")
    (tmp_path / "data" / "raw" / "workspace").mkdir(parents=True)
    (tmp_path / "data" / "huggingface" / "hub").mkdir(parents=True)
    (tmp_path / "data" / "llm-evals-course-notes-july.pdf").write_text(
        "pdf",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "__pycache__").mkdir(parents=True)
    (tmp_path / "tools" / "mineru" / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / "tools" / "mineru" / "README.md").write_text("tool docs", encoding="utf-8")
    (tmp_path / ".venv" / "lib" / "__pycache__").mkdir(parents=True)
    (tmp_path / ".tmp_mineru" / "pkg" / "__pycache__").mkdir(parents=True)

    targets = repo_clean.build_cleanup_plan(tmp_path)
    planned_paths = {target.relative_path for target in targets}

    assert ".pytest_cache" in planned_paths
    assert ".coverage" in planned_paths
    assert "data/raw" in planned_paths
    assert "tests/__pycache__" in planned_paths
    assert "tools/mineru/.venv" in planned_paths
    assert "data/huggingface" not in planned_paths
    assert "data/llm-evals-course-notes-july.pdf" not in planned_paths
    assert "tools/mineru/README.md" not in planned_paths
    assert ".venv/lib/__pycache__" not in planned_paths
    assert ".tmp_mineru/pkg/__pycache__" not in planned_paths


def test_main_dry_run_reports_targets_without_deleting(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    logs_dir = tmp_path / "data" / "logs"
    logs_dir.mkdir(parents=True)
    monkeypatch.setattr(repo_clean, "_resolve_repo_root", lambda: tmp_path)

    exit_code = repo_clean.main(["--dry-run"])

    assert exit_code == 0
    assert logs_dir.exists()
    assert "Would remove 1 path(s):" in capsys.readouterr().out


def test_main_removes_optional_model_cache_when_requested(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    model_cache = tmp_path / "data" / "huggingface" / "hub"
    model_cache.mkdir(parents=True)
    monkeypatch.setattr(repo_clean, "_resolve_repo_root", lambda: tmp_path)

    exit_code = repo_clean.main(["--include-model-cache"])

    assert exit_code == 0
    assert not (tmp_path / "data" / "huggingface").exists()
    assert "data/huggingface" in capsys.readouterr().out
