from __future__ import annotations

from pathlib import Path

from parity._contracts import SourceType
from parity.artifacts import NormalizedArtifact
from parity.extractors import MarkdownExtractor
from parity.normalizers import MarkdownNormalizer


def _source_path(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "sources" / name


def _normalized_snapshot_path(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "normalized" / name


def test_smoke_fixture_yields_expected_normalized_block_kinds() -> None:
    source = _source_path("smoke.md").read_bytes()
    extracted = MarkdownExtractor().extract(doc_id="fixture-smoke", raw_content=source)
    normalized = MarkdownNormalizer().normalize(extracted=extracted)

    assert normalized.source_type is SourceType.MARKDOWN
    assert [block.kind for block in normalized.blocks] == [
        "heading",
        "paragraph",
        "heading",
        "paragraph",
        "list_item",
        "quote",
        "code",
    ]


def test_design_exploration_snapshot_preserves_heading_paths() -> None:
    source = _source_path("design-exploration.md").read_bytes()
    extracted = MarkdownExtractor().extract(
        doc_id="fixture-design-exploration",
        raw_content=source,
    )
    normalized = MarkdownNormalizer().normalize(extracted=extracted)
    expected = NormalizedArtifact.model_validate_json(
        _normalized_snapshot_path("design-exploration.normalized.json").read_text(encoding="utf-8")
    )

    assert normalized == expected
    assert any(
        block.heading_path == ["Document Lifecycle Architecture for MVP", "Purpose"]
        for block in normalized.blocks
    )
    assert any(
        block.heading_path
        == [
            "Document Lifecycle Architecture for MVP",
            "Scope alignment",
            "Inputs",
        ]
        for block in normalized.blocks
    )


def test_mvp_snapshot_remains_stable_for_markdown_regressions() -> None:
    source = _source_path("mvp.md").read_bytes()
    extracted = MarkdownExtractor().extract(doc_id="fixture-mvp", raw_content=source)
    normalized = MarkdownNormalizer().normalize(extracted=extracted)
    expected = NormalizedArtifact.model_validate_json(
        _normalized_snapshot_path("mvp.normalized.json").read_text(encoding="utf-8")
    )

    assert normalized == expected
