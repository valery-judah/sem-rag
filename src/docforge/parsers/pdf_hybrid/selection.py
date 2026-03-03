import math

from pydantic import BaseModel

from .config import PdfHybridConfig
from .models import (
    PageCandidate,
    ParseStatus,
)

SUCCESS_STATUSES: frozenset[ParseStatus] = frozenset({ParseStatus.OK, ParseStatus.EMPTY})


class SelectionResult(BaseModel):
    selected_engine: str | None
    reason: str
    candidate: PageCandidate


def is_success_status(status: ParseStatus) -> bool:
    return status in SUCCESS_STATUSES


def engine_priority(engine: str) -> int:
    # Lower is better
    if engine == "marker":
        return 0
    if engine == "mineru":
        return 1
    return 2


def score_candidate(candidate: PageCandidate, config: PdfHybridConfig) -> float:
    """
    Computes deterministic score based on signals and weights.
    """
    w = config.selection_weights
    sig = candidate.signals

    score = (
        w.w_chars * math.log1p(sig.char_count)
        + w.w_blocks * math.log1p(sig.block_count)
        - w.w_dupes * sig.duplicate_line_ratio
        + w.w_coords * (1.0 if sig.has_coords else 0.0)
        + w.w_headings * math.log1p(sig.heading_like_count)
        + w.w_assets * math.log1p(sig.asset_count)
    )
    return score


def select_candidate_for_page(
    page_idx: int, candidates: dict[str, PageCandidate], config: PdfHybridConfig
) -> SelectionResult:
    # 1. Handle force_engine mitigation
    if config.force_engine and config.force_engine in candidates:
        cand = candidates[config.force_engine]
        if is_success_status(cand.status):
            return SelectionResult(
                selected_engine=config.force_engine,
                reason="forced_by_config",
                candidate=cand,
            )

    # 2. Filter successful candidates. Note: EMPTY is a success (blank page).
    successful_candidates = {k: v for k, v in candidates.items() if is_success_status(v.status)}

    if not successful_candidates:
        return SelectionResult(
            selected_engine=None,
            reason="all_failed",
            candidate=PageCandidate.placeholder_error(page_idx),
        )

    ok_candidates = {k: v for k, v in successful_candidates.items() if v.status == ParseStatus.OK}
    if ok_candidates:
        candidates_to_score = ok_candidates
        only_one_reason = "only_one_ok"
    else:
        # All successful candidates are EMPTY.
        candidates_to_score = successful_candidates
        only_one_reason = "only_one_empty"

    if len(candidates_to_score) == 1:
        engine = list(candidates_to_score.keys())[0]
        return SelectionResult(
            selected_engine=engine,
            reason=only_one_reason,
            candidate=candidates_to_score[engine],
        )

    # If this page is empty across engines, pick deterministically without scoring noise.
    if not ok_candidates:
        best_engine = min(candidates_to_score.keys(), key=engine_priority)
        return SelectionResult(
            selected_engine=best_engine,
            reason=f"all_empty_prefer_{best_engine}",
            candidate=candidates_to_score[best_engine],
        )

    # 3. Both ok, compute score
    scores = {engine: score_candidate(cand, config) for engine, cand in candidates_to_score.items()}

    # 4. Tie-breaking rules
    # Sort primarily by score descending, secondarily by engine preference
    sorted_candidates = sorted(
        scores.items(),
        key=lambda item: (-item[1], engine_priority(item[0])),
    )
    best_engine = sorted_candidates[0][0]

    # Check if there is a tie between the top two
    if len(sorted_candidates) > 1 and math.isclose(
        sorted_candidates[0][1], sorted_candidates[1][1], rel_tol=1e-9, abs_tol=1e-9
    ):
        reason = f"score_tie_break_{best_engine}"
    else:
        reason = "highest_score"

    return SelectionResult(
        selected_engine=best_engine,
        reason=reason,
        candidate=candidates_to_score[best_engine],
    )


def run_selection(
    page_candidates: dict[int, dict[str, PageCandidate]], config: PdfHybridConfig
) -> dict[int, SelectionResult]:
    """
    Returns the selected candidates per page.
    If a page fails, the SelectionResult will have a placeholder candidate.
    """
    results = {}
    for page_idx, cands in page_candidates.items():
        results[page_idx] = select_candidate_for_page(page_idx, cands, config)
    return results
