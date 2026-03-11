"""Selection stage placeholder."""

from __future__ import annotations

from parity.query.contracts import QueryStageName
from parity.query.errors import QueryStageNotImplementedError

STAGE_NAME = QueryStageName.SELECT


def run() -> None:
    """Placeholder Stage 0 entrypoint for selection."""

    raise QueryStageNotImplementedError(f"{STAGE_NAME.value} stage is not implemented")
