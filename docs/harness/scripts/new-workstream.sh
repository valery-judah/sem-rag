#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s WS-001 my-workstream-slug\n' "$(basename "$0")" >&2
}

if [ "$#" -ne 2 ]; then
  usage
  exit 1
fi

ws_id="$1"
ws_slug="$2"

case "${ws_id}" in
  WS-[0-9][0-9][0-9]*) ;;
  *)
    printf 'Expected workstream id like WS-001\n' >&2
    exit 1
    ;;
esac

case "${ws_slug}" in
  *[!a-z0-9-]*|'')
    printf 'Expected lowercase slug with letters, numbers, or hyphens\n' >&2
    exit 1
    ;;
esac

script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
repo_root="$(CDPATH='' cd -- "${script_dir}/../../.." && pwd)"
workstreams_dir="${repo_root}/docs/workstreams"
workstream_dir="${workstreams_dir}/${ws_id}-${ws_slug}"
today="$(date +%F)"

mkdir -p "${workstreams_dir}"

if [ -e "${workstream_dir}" ]; then
  printf 'Workstream already exists: %s\n' "${workstream_dir}" >&2
  exit 1
fi

mkdir -p "${workstream_dir}"

cat > "${workstream_dir}/workstream.md" <<EOF
# ${ws_id} ${ws_slug}

- Status: proposed
- Owner:
- Created: ${today}
- Updated: ${today}

## Problem

## Scope

## Non-Goals

## Plan
- Capture the problem and target outcome.
- Record decisions and evidence as work progresses.

## Related Notes
- Decisions: \`decisions.md\`
- Evidence: \`evidence.md\`
- Handoff: \`handoff.md\`
- ADRs:
EOF

cat > "${workstream_dir}/decisions.md" <<'EOF'
# Decisions

## YYYY-MM-DD - Decision Title
- Decision:
- Rationale:
- Impact:
- Follow-ups:
- Elevate to ADR: no
EOF

cat > "${workstream_dir}/evidence.md" <<'EOF'
# Evidence

## YYYY-MM-DD
- Changes made:
- Tests run:
- Validation notes:
- Risks or regressions checked:
- Artifacts or links:
EOF

cat > "${workstream_dir}/handoff.md" <<'EOF'
# Handoff

## Current State

## Remaining Work
- 

## Risks
- 

## Open Questions
- 

## Next Recommended Actions
1. 
EOF

cat > "${workstream_dir}/notes.md" <<'EOF'
# Notes

- Capture local findings, references, and working notes here.
EOF

printf 'Created %s\n' "${workstream_dir}"
