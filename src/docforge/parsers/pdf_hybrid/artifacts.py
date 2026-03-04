import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .config import PdfHybridConfig
from .models import PageCandidate
from .schema import ExtractedPdfDocument
from .selection import SelectionResult, score_candidate

logger = logging.getLogger(__name__)


class SelectionLogEntry(BaseModel):
    page_idx: int
    selected_engine: str | None
    reason: str
    scores: dict[str, float]
    statuses: dict[str, str]
    signals: dict[str, dict[str, Any]]


def build_selection_log(
    all_candidates: dict[int, dict[str, PageCandidate]],
    selection_results: dict[int, SelectionResult],
    config: PdfHybridConfig,
) -> list[SelectionLogEntry]:
    """
    Constructs log entries detailing why engines were selected per page.
    (Recomputes scores via score_candidate for detailed logging).
    """
    log_entries = []

    for page_idx in sorted(all_candidates.keys()):
        cands = all_candidates[page_idx]
        sel_res = selection_results.get(page_idx)

        selected_engine = sel_res.selected_engine if sel_res else None
        reason = sel_res.reason if sel_res else "unknown"

        scores = {}
        statuses = {}
        signals = {}

        for engine in sorted(cands.keys()):
            cand = cands[engine]
            statuses[engine] = str(cand.status.value)
            signals[engine] = cand.signals.model_dump()

            # Recompute score for logging if we can
            try:
                score = score_candidate(cand, config)
                scores[engine] = score
            except Exception:
                logger.exception(
                    "Failed to recompute score for selection log (page_idx=%s, engine=%s)",
                    page_idx,
                    engine,
                )
                scores[engine] = 0.0

        entry = SelectionLogEntry(
            page_idx=page_idx,
            selected_engine=selected_engine,
            reason=reason,
            scores=scores,
            statuses=statuses,
            signals=signals,
        )
        log_entries.append(entry)

    return log_entries


def write_selection_log(log: list[SelectionLogEntry], path: Path) -> None:
    """
    Writes the selection log as JSONL to the given path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for entry in log:
            f.write(entry.model_dump_json() + "\n")


def write_extracted_document(doc: ExtractedPdfDocument, path: Path) -> None:
    """
    Writes the ExtractedPdfDocument schema as pretty JSON.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(doc.model_dump_json(indent=2))
