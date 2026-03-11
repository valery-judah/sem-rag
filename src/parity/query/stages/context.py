"""Context assembly stage placeholder."""

from __future__ import annotations

from parity.query.contracts import QueryStageName
from parity.query.errors import QueryStageNotImplementedError

STAGE_NAME = QueryStageName.ASSEMBLE_CONTEXT


def run() -> None:
    """Placeholder Stage 0 entrypoint for context assembly."""

    raise QueryStageNotImplementedError(f"{STAGE_NAME.value} stage is not implemented")
