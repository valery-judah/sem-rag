import json
from pathlib import Path

from docforge.parsers.pdf_hybrid.artifacts import (
    build_selection_log,
    write_extracted_document,
    write_selection_log,
)
from docforge.parsers.pdf_hybrid.config import PdfHybridConfig
from docforge.parsers.pdf_hybrid.models import (
    BlockCandidate,
    BlockSource,
    BlockType,
    PageCandidate,
    ParseStatus,
)
from docforge.parsers.pdf_hybrid.schema import (
    EngineRunInfo,
    ExtractedPage,
    ExtractedPdfDocument,
    PipelineInfo,
    SourcePdfInfo,
)
from docforge.parsers.pdf_hybrid.selection import SelectionResult


def test_schema_roundtrip():
    doc = ExtractedPdfDocument(
        doc_id="test_doc",
        source_pdf=SourcePdfInfo(
            content_hash="abc",
            page_count=2,
            metadata={"author": "test"},
        ),
        pipeline=PipelineInfo(
            pipeline_version="1.0",
            config_hash="def",
        ),
        engine_runs=[
            EngineRunInfo(
                engine="marker",
                engine_version="1.0",
                engine_config_hash="cfg",
                engine_artifact_ref="ref1",
                status="success",
            )
        ],
        pages=[
            ExtractedPage(
                page_idx=1,
                width=100.0,
                height=200.0,
                selected_engine="marker",
                selection_reason="highest_score",
                blocks=[
                    BlockCandidate(
                        block_id="b1",
                        type=BlockType.PARA,
                        text="Hello World",
                        page_idx=1,
                        reading_order_key="0",
                        source=BlockSource(
                            engine="marker",
                            engine_artifact_ref="ref1",
                            engine_block_ref="b_ref_1",
                        ),
                    )
                ],
                assets=[],
                diagnostics={"time": 1.2},
            )
        ],
    )

    json_str = doc.model_dump_json()
    doc2 = ExtractedPdfDocument.model_validate_json(json_str)

    assert doc.model_dump() == doc2.model_dump()
    assert len(doc2.pages) == 1
    assert doc2.pages[0].blocks[0].text == "Hello World"


def test_artifact_emission(tmp_path: Path):
    doc = ExtractedPdfDocument(
        doc_id="test_doc",
        source_pdf=SourcePdfInfo(content_hash="abc", page_count=1),
        pipeline=PipelineInfo(pipeline_version="1.0", config_hash="def"),
        engine_runs=[],
        pages=[],
    )

    doc_path = tmp_path / "extracted_pdf_document.json"
    write_extracted_document(doc, doc_path)

    assert doc_path.exists()
    content = doc_path.read_text(encoding="utf-8")
    loaded = json.loads(content)
    assert loaded["doc_id"] == "test_doc"
    assert loaded["source_pdf"]["content_hash"] == "abc"


def test_build_and_write_selection_log(tmp_path: Path):
    config = PdfHybridConfig()

    marker_cand = PageCandidate(
        page_idx=1,
        blocks=[
            BlockCandidate(
                block_id="m1",
                type=BlockType.PARA,
                text="A para",
                page_idx=1,
                reading_order_key="0",
                source=BlockSource(engine="marker", engine_artifact_ref="m"),
            )
        ],
        assets=[],
        status=ParseStatus.OK,
    )
    # Compute signals
    marker_cand.signals = marker_cand.signals.compute(marker_cand.blocks, marker_cand.assets)

    mineru_cand = PageCandidate.empty(page_idx=1)

    all_candidates = {1: {"marker": marker_cand, "mineru": mineru_cand}}

    selection_results = {
        1: SelectionResult(selected_engine="marker", reason="highest_score", candidate=marker_cand)
    }

    log_entries = build_selection_log(all_candidates, selection_results, config)

    assert len(log_entries) == 1
    assert log_entries[0].page_idx == 1
    assert log_entries[0].selected_engine == "marker"
    assert log_entries[0].reason == "highest_score"
    assert "marker" in log_entries[0].scores
    assert "mineru" in log_entries[0].scores
    assert log_entries[0].statuses["mineru"] == "empty"
    assert log_entries[0].statuses["marker"] == "ok"

    log_path = tmp_path / "selection_log.jsonl"
    write_selection_log(log_entries, log_path)

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["selected_engine"] == "marker"
    assert parsed["reason"] == "highest_score"
    assert parsed["page_idx"] == 1
