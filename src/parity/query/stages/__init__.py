"""Placeholder query stage modules for the staged query lifecycle."""

from .assess_support import STAGE_NAME as ASSESS_SUPPORT_STAGE
from .context import STAGE_NAME as CONTEXT_STAGE
from .decide_answer_mode import STAGE_NAME as DECIDE_ANSWER_MODE_STAGE
from .evidence_sets import STAGE_NAME as EVIDENCE_SETS_STAGE
from .generate import STAGE_NAME as GENERATE_STAGE
from .interpret import STAGE_NAME as INTERPRET_STAGE
from .render_citations import STAGE_NAME as RENDER_CITATIONS_STAGE
from .retrieve import STAGE_NAME as RETRIEVE_STAGE
from .select import STAGE_NAME as SELECT_STAGE

__all__ = [
    "ASSESS_SUPPORT_STAGE",
    "CONTEXT_STAGE",
    "DECIDE_ANSWER_MODE_STAGE",
    "EVIDENCE_SETS_STAGE",
    "GENERATE_STAGE",
    "INTERPRET_STAGE",
    "RENDER_CITATIONS_STAGE",
    "RETRIEVE_STAGE",
    "SELECT_STAGE",
]
