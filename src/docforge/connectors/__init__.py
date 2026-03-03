from __future__ import annotations

from docforge.config import SourceConfig
from docforge.connectors.local_file import LocalFileConnector


def make_connector(source: SourceConfig) -> LocalFileConnector:
    if source.type == "local_file":
        return LocalFileConnector(source)
    msg = f"Unsupported source type: {source.type}"
    raise ValueError(msg)


__all__ = ["LocalFileConnector", "make_connector"]
