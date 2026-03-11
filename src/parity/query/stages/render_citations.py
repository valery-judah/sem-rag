"""Citation rendering stage placeholder."""

from __future__ import annotations

from parity.query.contracts import QueryStageName
from parity.query.errors import QueryStageNotImplementedError

STAGE_NAME = QueryStageName.RENDER_CITATIONS


def run() -> None:
    """Placeholder Stage 0 entrypoint for citation rendering."""

    raise QueryStageNotImplementedError(f"{STAGE_NAME.value} stage is not implemented")
