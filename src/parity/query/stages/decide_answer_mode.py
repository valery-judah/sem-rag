"""Answer-mode decision stage placeholder."""

from __future__ import annotations

from parity.query.contracts import QueryStageName
from parity.query.errors import QueryStageNotImplementedError

STAGE_NAME = QueryStageName.DECIDE_ANSWER_MODE


def run() -> None:
    """Placeholder Stage 0 entrypoint for answer-mode decision."""

    raise QueryStageNotImplementedError(f"{STAGE_NAME.value} stage is not implemented")
