from parity.query.answer_generation import _build_comparison_answer_text
from parity.query.contracts import ContextItem, ContextManifest


def test_build_comparison_answer_text_groups_single_document_items_by_header_title() -> None:
    manifest = ContextManifest(
        ordered_evidence_set_ids=["es-atlas", "es-beacon"],
        included_evidence_set_ids=["es-atlas", "es-beacon"],
        inclusion_reasons={
            "es-atlas": "included_primary_support_priority",
            "es-beacon": "included_within_budget",
        },
        token_budget=4000,
        token_budget_used=64,
        context_items=[
            ContextItem(
                evidence_set_id="es-atlas",
                assembly_rank=1,
                rendered_text=(
                    "Atlas Cache Design | direct_support | Atlas > Caching\n"
                    "[p. 2] Atlas uses a write-through cache.\n"
                    "[p. 3] Atlas performs immediate invalidation after each control-plane update.\n"
                    "[p. 4] Operators treat stale reads as unacceptable."
                ),
                contributing_doc_ids=["doc-atlas"],
                heading_paths=[["Atlas", "Caching"]],
                locators=["p. 2", "p. 3", "p. 4"],
                estimated_token_count=32,
            ),
            ContextItem(
                evidence_set_id="es-beacon",
                assembly_rank=2,
                rendered_text=(
                    "Beacon Dashboard Cache | direct_support | Beacon > Caching\n"
                    "[p. 2] Beacon uses a 15-minute TTL cache for dashboards.\n"
                    "[p. 3] Stale reads are allowed within the TTL window.\n"
                    "[p. 4] Beacon is latency-first."
                ),
                contributing_doc_ids=["doc-beacon"],
                heading_paths=[["Beacon", "Caching"]],
                locators=["p. 2", "p. 3", "p. 4"],
                estimated_token_count=32,
            ),
        ],
    )

    answer_text = _build_comparison_answer_text(manifest)

    assert answer_text is not None
    assert "Atlas Cache Design has stricter freshness guarantees" in answer_text
    assert "Beacon Dashboard Cache is looser" in answer_text
    assert "corpus has stricter freshness guarantees" not in answer_text
