"""Interpretation stage placeholder."""

from __future__ import annotations

from parity.query.contracts import QueryStageName
from parity.query.errors import QueryStageNotImplementedError

STAGE_NAME = QueryStageName.INTERPRET


def run() -> None:
    """Placeholder Stage 0 entrypoint for interpretation."""

    raise QueryStageNotImplementedError(f"{STAGE_NAME.value} stage is not implemented")
