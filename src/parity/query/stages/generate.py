"""Grounded generation stage placeholder."""

from __future__ import annotations

from parity.query.contracts import QueryStageName
from parity.query.errors import QueryStageNotImplementedError

STAGE_NAME = QueryStageName.GENERATE


def run() -> None:
    """Placeholder Stage 0 entrypoint for answer generation."""

    raise QueryStageNotImplementedError(f"{STAGE_NAME.value} stage is not implemented")
