#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"

"${script_dir}/validate-frontmatter.sh"

printf 'Docs lint checks passed\n'
