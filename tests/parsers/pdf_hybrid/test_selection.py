import math

from docforge.parsers.pdf_hybrid.config import PdfHybridConfig
from docforge.parsers.pdf_hybrid.models import (
    BlockCandidate,
    BlockSource,
    BlockType,
    PageCandidate,
    PageSignals,
    ParseStatus,
)
from docforge.parsers.pdf_hybrid.selection import (
    run_selection,
    score_candidate,
    select_candidate_for_page,
)


def _make_candidate(
    engine: str,
    status: ParseStatus,
    *,
    page_idx: int = 1,
    char_count: int = 0,
) -> PageCandidate:
    if status == ParseStatus.OK:
        block = BlockCandidate(
            block_id=f"b_{engine}",
            type=BlockType.PARA,
            text=f"test text {engine}",
            page_idx=page_idx,
            reading_order_key="0",
            source=BlockSource(
                engine=engine,
                engine_artifact_ref="ref",
                engine_block_ref="bref",
            ),
        )
        blocks = [block]
    else:
        blocks = []
        char_count = 0

    sig = PageSignals(char_count=char_count, block_count=len(blocks))
    return PageCandidate(page_idx=page_idx, blocks=blocks, status=status, signals=sig)


def test_score_candidate():
    config = PdfHybridConfig()
    cand = _make_candidate("marker", ParseStatus.OK, char_count=100)
    cand.signals.block_count = 5
    cand.signals.has_coords = True

    score = score_candidate(cand, config)
    # w_chars(1.0) * log1p(100) + w_blocks(0.2) * log1p(5) + w_coords(0.3) * 1.0 = ...
    expected = math.log1p(100) + 0.2 * math.log1p(5) + 0.3
    assert math.isclose(score, expected)


def test_select_candidate_for_page_all_failed():
    config = PdfHybridConfig()
    cands = {
        "marker": _make_candidate("marker", ParseStatus.ERROR),
        "mineru": _make_candidate("mineru", ParseStatus.TIMEOUT),
    }
    res = select_candidate_for_page(1, cands, config)
    assert res.selected_engine is None
    assert res.reason == "all_failed"
    assert res.candidate.status == ParseStatus.ERROR
    assert len(res.candidate.blocks) == 1
    assert res.candidate.blocks[0].text == "[UNPARSEABLE PAGE 1]"


def test_select_candidate_for_page_only_one_ok():
    config = PdfHybridConfig()
    cands = {
        "marker": _make_candidate("marker", ParseStatus.OK, char_count=50),
        "mineru": _make_candidate("mineru", ParseStatus.ERROR),
    }
    res = select_candidate_for_page(1, cands, config)
    assert res.selected_engine == "marker"
    assert res.reason == "only_one_ok"
    assert res.candidate.status == ParseStatus.OK


def test_select_candidate_for_page_ok_beats_empty():
    config = PdfHybridConfig()
    cands = {
        "marker": _make_candidate("marker", ParseStatus.OK, char_count=50),
        "mineru": _make_candidate("mineru", ParseStatus.EMPTY),
    }
    res = select_candidate_for_page(1, cands, config)
    assert res.selected_engine == "marker"
    assert res.candidate.status == ParseStatus.OK


def test_select_candidate_for_page_all_empty_prefers_marker():
    config = PdfHybridConfig()
    cands = {
        "marker": _make_candidate("marker", ParseStatus.EMPTY),
        "mineru": _make_candidate("mineru", ParseStatus.EMPTY),
    }
    res = select_candidate_for_page(1, cands, config)
    assert res.selected_engine == "marker"
    assert res.reason == "all_empty_prefer_marker"
    assert res.candidate.status == ParseStatus.EMPTY


def test_select_candidate_for_page_highest_score():
    config = PdfHybridConfig()
    cands = {
        "marker": _make_candidate("marker", ParseStatus.OK, char_count=50),
        "mineru": _make_candidate("mineru", ParseStatus.OK, char_count=1000),
    }
    res = select_candidate_for_page(1, cands, config)
    assert res.selected_engine == "mineru"
    assert res.reason == "highest_score"


def test_select_candidate_for_page_tie_break():
    config = PdfHybridConfig()
    # Same signals -> same score
    cands = {
        "marker": _make_candidate("marker", ParseStatus.OK, char_count=50),
        "mineru": _make_candidate("mineru", ParseStatus.OK, char_count=50),
    }
    res = select_candidate_for_page(1, cands, config)
    # Marker is preferred on tie
    assert res.selected_engine == "marker"
    assert res.reason == "score_tie_break_marker"


def test_select_candidate_for_page_force_engine():
    config = PdfHybridConfig(force_engine="mineru")
    cands = {
        "marker": _make_candidate("marker", ParseStatus.OK, char_count=1000),
        "mineru": _make_candidate("mineru", ParseStatus.OK, char_count=50),
    }
    res = select_candidate_for_page(1, cands, config)
    # Mineru forced despite Marker having higher score
    assert res.selected_engine == "mineru"
    assert res.reason == "forced_by_config"


def test_select_candidate_for_page_force_engine_empty():
    config = PdfHybridConfig(force_engine="mineru")
    cands = {
        "marker": _make_candidate("marker", ParseStatus.EMPTY),
        "mineru": _make_candidate("mineru", ParseStatus.EMPTY),
    }
    res = select_candidate_for_page(1, cands, config)
    assert res.selected_engine == "mineru"
    assert res.reason == "forced_by_config"
    assert res.candidate.status == ParseStatus.EMPTY


def test_run_selection():
    config = PdfHybridConfig()
    pages = {
        1: {
            "marker": _make_candidate("marker", ParseStatus.OK, char_count=50),
            "mineru": _make_candidate("mineru", ParseStatus.OK, char_count=1000),
        },
        2: {
            "marker": _make_candidate("marker", ParseStatus.ERROR),
            "mineru": _make_candidate("mineru", ParseStatus.TIMEOUT),
        },
    }
    results = run_selection(pages, config)
    assert len(results) == 2
    assert results[1].selected_engine == "mineru"
    assert results[2].selected_engine is None
    assert results[2].candidate.blocks[0].text == "[UNPARSEABLE PAGE 2]"
