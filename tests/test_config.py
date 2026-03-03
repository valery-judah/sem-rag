from __future__ import annotations

from pathlib import Path

import pydantic

from docforge.config import load_config
from docforge.models import DocumentTimestamps, RawDocument


def test_load_config_sources_shape(tmp_path: Path) -> None:
    config_file = tmp_path / "connectors.toml"
    config_file.write_text(
        """
[[sources]]
type = "local_file"
path = "data/mvp.pdf"
doc_id = "mvp_pdf"
content_type = "application/pdf"
metadata = { title = "MVP PDF" }
acl_scope = { visibility = "internal" }
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert len(config.sources) == 1
    source = config.sources[0]
    assert source.type == "local_file"
    assert source.path == "data/mvp.pdf"
    assert source.doc_id == "mvp_pdf"
    assert source.content_type == "application/pdf"
    assert source.metadata == {"title": "MVP PDF"}
    assert source.acl_scope == {"visibility": "internal"}


def test_models_import_cleanly() -> None:
    assert RawDocument.__name__ == "RawDocument"
    assert DocumentTimestamps.__name__ == "DocumentTimestamps"


def test_content_type_known_value_is_allowed(tmp_path: Path) -> None:
    config_file = tmp_path / "connectors.toml"
    config_file.write_text(
        """
[[sources]]
type = "local_file"
path = "data/mvp.pdf"
content_type = "application/pdf"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.sources[0].content_type == "application/pdf"


def test_content_type_unknown_value_remains_string(tmp_path: Path) -> None:
    config_file = tmp_path / "connectors.toml"
    config_file.write_text(
        """
[[sources]]
type = "local_file"
path = "data/mvp.pdf"
content_type = "application/x-custom"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.sources[0].content_type == "application/x-custom"


def test_load_config_missing_required_fields_fails(tmp_path: Path) -> None:
    config_file = tmp_path / "connectors.toml"
    config_file.write_text(
        """
[[sources]]
type = "local_file"
""".strip(),
        encoding="utf-8",
    )

    try:
        load_config(config_file)
    except pydantic.ValidationError:
        pass
    else:
        raise AssertionError("Expected pydantic.ValidationError")


def test_load_config_applies_segmentation_defaults(tmp_path: Path) -> None:
    config_file = tmp_path / "connectors.toml"
    config_file.write_text(
        """
[[sources]]
type = "local_file"
path = "data/mvp.md"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.segmentation.passage_tokens_target == 600
    assert config.segmentation.overlap_ratio == 0.1


def test_load_config_rejects_out_of_range_segmentation_values(tmp_path: Path) -> None:
    config_file = tmp_path / "connectors.toml"
    config_file.write_text(
        """
[[sources]]
type = "local_file"
path = "data/mvp.md"

[segmentation]
passage_tokens_target = 200
overlap_ratio = 0.20
""".strip(),
        encoding="utf-8",
    )

    try:
        load_config(config_file)
    except pydantic.ValidationError:
        pass
    else:
        raise AssertionError("Expected pydantic.ValidationError")
