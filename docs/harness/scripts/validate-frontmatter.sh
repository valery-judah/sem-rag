#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
repo_root="$(CDPATH='' cd -- "${script_dir}/../../.." && pwd)"

status=0

frontmatter_block() {
  local file="$1"
  local closing_line="$2"
  sed -n "2,$((closing_line - 1))p" "${file}"
}

has_frontmatter_key() {
  local frontmatter="$1"
  local key="$2"
  printf '%s\n' "${frontmatter}" | grep -Eq "^${key}:"
}

frontmatter_value() {
  local frontmatter="$1"
  local key="$2"
  printf '%s\n' "${frontmatter}" | sed -nE "s/^${key}:[[:space:]]*(.*)$/\\1/p" | head -n 1
}

while IFS= read -r file; do
  first_line="$(sed -n '1p' "${file}")"
  if [ "${first_line}" != "---" ]; then
    continue
  fi

  closing_line="$(awk 'NR > 1 && $0 == "---" { print NR; exit }' "${file}")"
  if [ -z "${closing_line}" ]; then
    printf 'Malformed frontmatter: missing closing delimiter in %s\n' "${file}" >&2
    status=1
    continue
  fi

  if [ "${closing_line}" -eq 2 ]; then
    printf 'Malformed frontmatter: empty frontmatter block in %s\n' "${file}" >&2
    status=1
  fi
done < <(find "${repo_root}/docs" -type f -name '*.md' | sort)

while IFS= read -r file; do
  closing_line="$(awk 'NR > 1 && $0 == "---" { print NR; exit }' "${file}")"
  if [ -z "${closing_line}" ] || [ "${closing_line}" -eq 2 ]; then
    continue
  fi
  frontmatter="$(frontmatter_block "${file}" "${closing_line}")"

  for key in artifact_kind id title work_type status owner created updated; do
    if ! has_frontmatter_key "${frontmatter}" "${key}"; then
      printf 'Missing required frontmatter key %s in %s\n' "${key}" "${file}" >&2
      status=1
    fi
  done

  artifact_kind="$(frontmatter_value "${frontmatter}" "artifact_kind")"
  if [ "${artifact_kind}" != "workstream" ]; then
    printf 'Invalid artifact_kind in %s: expected workstream\n' "${file}" >&2
    status=1
  fi

  workstream_id="$(frontmatter_value "${frontmatter}" "id")"
  if ! printf '%s\n' "${workstream_id}" | grep -Eq '^WS-[0-9][0-9][0-9]+$'; then
    printf 'Invalid id in %s: expected WS-###\n' "${file}" >&2
    status=1
  fi

  work_type="$(frontmatter_value "${frontmatter}" "work_type")"
  case "${work_type}" in
    feature|defect|refactor|spike|operations-infrastructure) ;;
    *)
      printf 'Invalid work_type in %s: %s\n' "${file}" "${work_type}" >&2
      status=1
      ;;
  esac

  work_status="$(frontmatter_value "${frontmatter}" "status")"
  case "${work_status}" in
    backlog|active|blocked|done|archived) ;;
    *)
      printf 'Invalid status in %s: %s\n' "${file}" "${work_status}" >&2
      status=1
      ;;
  esac

  created="$(frontmatter_value "${frontmatter}" "created")"
  if [ -z "${created}" ]; then
    printf 'Invalid created in %s: expected non-empty value\n' "${file}" >&2
    status=1
  fi

  updated="$(frontmatter_value "${frontmatter}" "updated")"
  if [ -z "${updated}" ]; then
    printf 'Invalid updated in %s: expected non-empty value\n' "${file}" >&2
    status=1
  fi
done < <(find "${repo_root}/docs/workstreams" -type f -name 'workstream.md' | sort)

exit "${status}"
