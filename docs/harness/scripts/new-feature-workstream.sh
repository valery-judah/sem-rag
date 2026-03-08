#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s <slug>\n' "$(basename "$0")" >&2
}

if [ "$#" -ne 1 ]; then
  usage
  exit 1
fi

slug="$1"

case "${slug}" in
  *[!a-z0-9-]*|'')
    printf 'Expected lowercase slug with letters, numbers, or hyphens\n' >&2
    exit 1
    ;;
esac

script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
repo_root="$(CDPATH='' cd -- "${script_dir}/../../.." && pwd)"
workstreams_dir="${repo_root}/docs/workstreams"
today="$(date +%F)"

mkdir -p "${workstreams_dir}"

last_id="$(
  find "${workstreams_dir}" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; |
    sed -nE 's/^WS-([0-9]+)-.*$/\1/p' |
    sort -n |
    tail -n 1
)"

if [ -n "${last_id}" ]; then
  next_num=$((10#${last_id} + 1))
else
  next_num=1
fi

ws_id="$(printf 'WS-%03d' "${next_num}")"
workstream_dir="${workstreams_dir}/${ws_id}-${slug}"

if [ -e "${workstream_dir}" ]; then
  printf 'Workstream already exists: %s\n' "${workstream_dir}" >&2
  exit 1
fi

title="$(
  printf '%s\n' "${slug}" |
    awk -F- '{
      OFS = " "
      for (i = 1; i <= NF; i++) {
        if (length($i) > 0) {
          $i = toupper(substr($i, 1, 1)) substr($i, 2)
        }
      }
      print $0
    }'
)"

mkdir -p "${workstream_dir}"

cat > "${workstream_dir}/workstream.md" <<EOF
---
artifact_kind: workstream
id: ${ws_id}
title: ${title}
work_type: feature
status: active
owner:
created: ${today}
updated: ${today}
tags: []
affected_paths: []
affected_components: []
blockers: []
depends_on: []
evergreen_targets: []
adr_links: []
rfc_links: []
validation_evidence: []
gate: none
context_dependencies: []
commands: []
boundaries: []
---

# Summary
Short description of the feature workstream and intended result.

## Objective
State the desired outcome clearly enough that completion is recognizable.

## Non-goals
- List what is explicitly out of scope.

## Current status
Describe what is already true, what changed recently, and what still matters.

## Next step
- Record one concrete next action.

## Relevant context
- paths:
- components:
- constraints:
- read first:

## Workflow steps
1. Frame the feature scope and relevant constraints.
2. Shape the implementation and validation approach.
3. Execute and validate the workstream.

## Validation
- List the tests, checks, or evidence needed before closure.

## Linked artifacts
- Add related notes, decisions, evidence, ADRs, and evergreen docs here when they exist.
EOF

printf 'Created %s\n' "${workstream_dir}"
