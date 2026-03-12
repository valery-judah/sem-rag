"""Simple section-first chunking policy."""

from __future__ import annotations

import re

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
MAX_TOKENS_PER_CHUNK = 120


def count_tokens(text: str) -> int:
    """Count coarse retrieval tokens for chunk sizing/debug metadata."""

    return len(TOKEN_RE.findall(text))
