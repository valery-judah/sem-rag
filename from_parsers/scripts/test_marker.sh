#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is required but not installed." >&2
  exit 127
fi

exec uv run python scripts/test_marker.py "$@"
