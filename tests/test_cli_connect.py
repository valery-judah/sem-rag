from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from docforge.cli import main


def test_cli_connect_writes_raw_and_blob_artifacts_with_matching_hash(
    tmp_path: Path, capsys
) -> None:
    pdf_path = tmp_path / "input.pdf"
    content = b"%PDF-1.7\nhello\n"
    pdf_path.write_bytes(content)

    config_path = tmp_path / "connectors.toml"
    config_path.write_text(
        f"""
[[sources]]
type = "local_file"
path = "{pdf_path}"
doc_id = "sample_pdf"
metadata = {{ title = "Sample PDF" }}
acl_scope = {{ visibility = "internal" }}
""".strip(),
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    code = main(["connect", "--config", str(config_path), "--out", str(out_dir)])
    assert code == 0

    raw_files = sorted((out_dir / "raw").glob("*.json"))
    blob_files = sorted((out_dir / "blobs").glob("*.bin"))
    assert len(raw_files) == 1
    assert len(blob_files) == 1

    sidecar = json.loads(raw_files[0].read_text(encoding="utf-8"))
    blob_bytes = blob_files[0].read_bytes()
    expected_sha = sha256(blob_bytes).hexdigest()
    assert sidecar["doc_id"] == "sample_pdf"
    assert sidecar["content_sha256"] == expected_sha
    assert sidecar["content_bytes_len"] == len(blob_bytes)
    assert "content_bytes" not in sidecar

    out = capsys.readouterr().out
    assert "doc_id=sample_pdf" in out
    assert f"sha256={expected_sha}" in out


def test_cli_connect_relative_paths_resolve_from_config_dir_and_preserve_source_ref(
    tmp_path: Path, capsys
) -> None:
    pdf_path = tmp_path / "input.pdf"
    content = b"%PDF-1.7\nhello\n"
    pdf_path.write_bytes(content)

    config_path = tmp_path / "connectors.toml"
    config_path.write_text(
        """
[[sources]]
type = "local_file"
path = "./input.pdf"
metadata = { title = "Rel PDF" }
acl_scope = { visibility = "internal" }
""".strip(),
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    code = main(["connect", "--config", str(config_path), "--out", str(out_dir)])
    assert code == 0

    raw_files = sorted((out_dir / "raw").glob("*.json"))
    blob_files = sorted((out_dir / "blobs").glob("*.bin"))
    assert len(raw_files) == 1
    assert len(blob_files) == 1

    sidecar = json.loads(raw_files[0].read_text(encoding="utf-8"))
    blob_bytes = blob_files[0].read_bytes()
    expected_sha = sha256(blob_bytes).hexdigest()

    expected_doc_id = f"local_file:{sha256(b'./input.pdf').hexdigest()}"
    assert sidecar["doc_id"] == expected_doc_id
    assert sidecar["source_ref"] == "./input.pdf"
    assert sidecar["url"] == "file:./input.pdf"
    assert sidecar["content_sha256"] == expected_sha
    assert sidecar["content_bytes_len"] == len(blob_bytes)
    assert sidecar["content_type"] == "application/pdf"
    assert "content_bytes" not in sidecar

    out = capsys.readouterr().out
    assert f"doc_id={expected_doc_id}" in out
    assert f"sha256={expected_sha}" in out


def test_cli_connect_missing_file_returns_non_zero_and_error(tmp_path: Path, capsys) -> None:
    missing_path = tmp_path / "missing.pdf"
    config_path = tmp_path / "connectors.toml"
    config_path.write_text(
        f"""
[[sources]]
type = "local_file"
path = "{missing_path}"
doc_id = "missing"
""".strip(),
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    code = main(["connect", "--config", str(config_path), "--out", str(out_dir)])
    assert code == 1
    err = capsys.readouterr().err
    assert "docforge connect error:" in err
    assert "missing.pdf" in err
