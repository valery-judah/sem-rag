from __future__ import annotations

import json
from pathlib import Path

from docforge.experiment.config import VariantConfig
from docforge.experiment.pipeline import run_baseline_pipeline


def test_variant_config_defaults_from_toml(tmp_path: Path) -> None:
    variant_path = tmp_path / "minimal.toml"
    variant_path.write_text('extractor = "synthetic_text"\n', encoding="utf-8")

    config = VariantConfig.from_toml_path(variant_path)

    assert config.variant_id == "minimal"
    assert config.extractor == "synthetic_text"
    assert config.chunking.target_chars == 1200
    assert config.postprocess.dehyphenate
    assert config.postprocess.strip_repeated_margin_boilerplate


def test_baseline_pipeline_writes_expected_artifacts(tmp_path: Path) -> None:
    source_path = tmp_path / "sample.txt"
    source_path.write_text(
        "Chapter title\n"
        "Chapter title\n"
        "A hyphen-\n"
        "ated sentence lives here.\f"
        "Second page with enough content for chunking.",
        encoding="utf-8",
    )

    variant_path = tmp_path / "variant.toml"
    variant_path.write_text(
        "\n".join(
            [
                'variant_id = "wave0-synthetic"',
                'extractor = "synthetic_text"',
                "[chunking]",
                "target_chars = 20",
                "overlap_chars = 5",
                "min_chars = 8",
                "[postprocess]",
                "dehyphenate = true",
                "dedupe_repeated_lines = true",
                "strip_blank_lines = true",
            ]
        ),
        encoding="utf-8",
    )

    config = VariantConfig.from_toml_path(variant_path)
    result = run_baseline_pipeline(
        source_path=source_path,
        variant=config,
        output_root=tmp_path / "artifacts",
    )

    assert result.output_dir.exists()

    parsed = json.loads(result.parsed_document_path.read_text(encoding="utf-8"))
    assert parsed["page_count"] == 2
    assert parsed["doc_id"].startswith("sample-")
    assert "A hyphenated sentence" in parsed["pages"][0]["canonical_text"]
    assert len(parsed["chunks"]) >= 2

    chunks_path = result.output_dir / "chunks.jsonl"
    chunk_lines = chunks_path.read_text(encoding="utf-8").strip().splitlines()
    assert chunk_lines

    router_path = result.output_dir / "router_decisions.jsonl"
    router_lines = router_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(router_lines) == 2

    metrics_path = result.output_dir / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "must_pass_gates" in metrics

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["variant_config"]["variant_id"] == "wave0-synthetic"
    assert manifest["source"]["path"] == str(source_path)

    for filename in [
        "needles_report.json",
        "gold_eval.json",
        "human_review.csv",
        "chunks_review.md",
    ]:
        assert (result.output_dir / filename).exists()


def test_pipeline_strips_repeated_margin_boilerplate(tmp_path: Path) -> None:
    source_path = tmp_path / "boilerplate.txt"
    source_path.write_text(
        "\f".join(
            [
                "\n".join(
                    [
                        "Draft - Do Not Share",
                        f"application-centric ai evals for engineers and technical pms {index}",
                        f"Body line for page {index}",
                    ]
                )
                for index in range(1, 6)
            ]
        ),
        encoding="utf-8",
    )

    config = VariantConfig.from_mapping(
        {
            "variant_id": "wave0-boilerplate-strip",
            "extractor": "synthetic_text",
            "postprocess": {
                "strip_repeated_margin_boilerplate": True,
            },
        }
    )
    result = run_baseline_pipeline(
        source_path=source_path,
        variant=config,
        output_root=tmp_path / "artifacts",
    )

    parsed = json.loads(result.parsed_document_path.read_text(encoding="utf-8"))
    canonical_pages = [page["canonical_text"] for page in parsed["pages"]]

    assert all("Draft - Do Not Share" not in page for page in canonical_pages)
    assert all(
        "application-centric ai evals for engineers and technical pms" not in page
        for page in canonical_pages
    )
    assert all("Body line for page" in page for page in canonical_pages)


def test_hybrid_routing_falls_back_to_secondary_extractor(tmp_path: Path) -> None:
    source_path = tmp_path / "hybrid-source.txt"
    source_path.write_text(
        "Hybrid route page one.\fHybrid route page two.",
        encoding="utf-8",
    )

    config = VariantConfig.from_mapping(
        {
            "variant_id": "wave2-hybrid-fallback",
            "extractor": "hybrid",
            "routing": {
                "extractors": ["missing_extractor", "synthetic_text"],
                "default_order": ["missing_extractor", "synthetic_text"],
                "scan_likely_order": ["missing_extractor", "synthetic_text"],
                "scan_char_threshold": 999999,
                "min_tokens": 1,
            },
        }
    )

    result = run_baseline_pipeline(
        source_path=source_path,
        variant=config,
        output_root=tmp_path / "artifacts",
    )

    router_lines = (
        (result.output_dir / "router_decisions.jsonl").read_text(encoding="utf-8").splitlines()
    )
    decisions = [json.loads(line) for line in router_lines if line.strip()]
    assert decisions
    assert all(decision["extractor"] == "synthetic_text" for decision in decisions)
    assert all(
        "missing_extractor" in (decision.get("fallback_reason") or "") for decision in decisions
    )

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["failures"]["count"] >= 1
    assert any(
        reason["extractor"] == "missing_extractor" for reason in manifest["failures"]["reasons"]
    )

    markdown_review = result.chunks_markdown_path.read_text(encoding="utf-8")
    assert markdown_review.startswith("# Chunk Review:")
    assert "Hybrid route page one." in markdown_review
