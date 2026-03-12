#!/usr/bin/env bash

set -euo pipefail

API_URL="http://127.0.0.1:8000"
HOST_OLLAMA_URL="http://127.0.0.1:11434"
WORKSPACE="ws-answer-compare-$(date +%s)"
QUESTION="Compare Atlas and Beacon caching strategies. Which system has stricter freshness guarantees, and why?"
OLLAMA_MODEL="tinyllama"
USE_HOST_OLLAMA="${USE_HOST_OLLAMA:-}"

if [ -z "$USE_HOST_OLLAMA" ]; then
  if [ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ]; then
    USE_HOST_OLLAMA="1"
  else
    USE_HOST_OLLAMA="0"
  fi
fi

if [ "$USE_HOST_OLLAMA" = "1" ]; then
  OLLAMA_BASE_URL_FOR_CONTAINERS="${OLLAMA_BASE_URL:-http://host.docker.internal:11434}"
  OLLAMA_HEALTH_URL="${HOST_OLLAMA_URL}/api/tags"
else
  OLLAMA_BASE_URL_FOR_CONTAINERS="${OLLAMA_BASE_URL:-http://ollama:11434}"
  OLLAMA_HEALTH_URL="${HOST_OLLAMA_URL}/api/tags"
fi

SCRATCH_DIR="$(mktemp -d)"
DOC_TITLES=()
DOC_IDS=()
HOST_OLLAMA_PID=""

cleanup() {
  local exit_code=$?

  echo ""
  echo "==> Cleaning up..."
  make docker-down >/dev/null 2>&1 || docker compose down >/dev/null 2>&1 || true
  if [ -n "$HOST_OLLAMA_PID" ]; then
    kill "$HOST_OLLAMA_PID" >/dev/null 2>&1 || true
    wait "$HOST_OLLAMA_PID" >/dev/null 2>&1 || true
  fi
  rm -rf "$SCRATCH_DIR"

  if [ "$exit_code" -eq 0 ]; then
    echo "==> Done."
  else
    echo "==> Failed with exit code $exit_code."
  fi
}

trap cleanup EXIT

die() {
  echo "Error: $*" >&2
  exit 1
}

wait_for_http_ready() {
  local label=$1
  local url=$2
  local attempts=${3:-30}
  local delay_seconds=${4:-2}
  local i

  for ((i = 1; i <= attempts; i++)); do
    if curl -fsS "$url" >/dev/null; then
      echo "$label is ready."
      return 0
    fi
    echo "Waiting for $label... ($i/$attempts)"
    sleep "$delay_seconds"
  done

  return 1
}

ensure_host_ollama() {
  command -v ollama >/dev/null 2>&1 \
    || die "host Ollama CLI is required for GPU-backed local generation on Apple Silicon"

  if ! wait_for_http_ready "host Ollama" "$OLLAMA_HEALTH_URL" 5 1; then
    echo "==> Starting host Ollama service..."
    ollama serve >"$SCRATCH_DIR/host-ollama.log" 2>&1 &
    HOST_OLLAMA_PID=$!
    wait_for_http_ready "host Ollama" "$OLLAMA_HEALTH_URL" 30 2 \
      || die "host Ollama did not become ready at $OLLAMA_HEALTH_URL"
  fi

  ollama pull "$OLLAMA_MODEL" >/dev/null \
    || die "failed to pull host Ollama model '$OLLAMA_MODEL'"
}

upload_document() {
  local title=$1
  local file_path=$2
  local response_file="$SCRATCH_DIR/upload-response.json"
  local http_code
  local doc_id

  http_code=$(
    curl -sS -o "$response_file" -w "%{http_code}" \
      -X POST "$API_URL/documents" \
      -F "workspace_id=$WORKSPACE" \
      -F "title=$title" \
      -F "file=@$file_path;type=text/markdown"
  )

  if [ "$http_code" != "201" ]; then
    echo "Upload response body:" >&2
    cat "$response_file" >&2
    docker compose logs api >&2 || true
    die "upload failed for '$title' (HTTP $http_code)"
  fi

  doc_id=$(jq -er '.doc_id' "$response_file") || die "missing doc_id for '$title'"
  printf '%s\n' "$doc_id"
}

wait_for_document_ready() {
  local doc_id=$1
  local title=$2
  local status_file="$SCRATCH_DIR/status-$doc_id.json"
  local attempts=${3:-45}
  local delay_seconds=${4:-2}
  local i
  local ingest_status

  for ((i = 1; i <= attempts; i++)); do
    curl -fsS -o "$status_file" "$API_URL/documents/$doc_id/status" \
      || die "failed to fetch status for '$title' ($doc_id)"
    ingest_status=$(jq -er '.ingest_status' "$status_file") \
      || die "missing ingest_status for '$title' ($doc_id)"

    if [ "$ingest_status" = "ready" ]; then
      echo "$title is READY."
      return 0
    fi
    if [ "$ingest_status" = "failed" ]; then
      echo "Status payload for failed document:" >&2
      cat "$status_file" >&2
      die "document ingestion failed for '$title' ($doc_id)"
    fi

    echo "$title status: $ingest_status. Waiting... ($i/$attempts)"
    sleep "$delay_seconds"
  done

  echo "Last status payload before timeout:" >&2
  cat "$status_file" >&2
  die "document ingestion timed out for '$title' ($doc_id)"
}

run_query() {
  local label=$1
  local output_file=$2
  local payload_file="$SCRATCH_DIR/query-payload-$label.json"
  local response_file="$SCRATCH_DIR/query-response-$label.json"
  local http_code

  jq -n \
    --arg q "$QUESTION" \
    --arg ws "$WORKSPACE" \
    '{question: $q, workspace_id: $ws}' >"$payload_file"

  http_code=$(
    curl -sS -o "$response_file" -w "%{http_code}" \
      -X POST "$API_URL/queries" \
      -H "Content-Type: application/json" \
      -d @"$payload_file"
  )

  if [ "$http_code" != "200" ]; then
    echo "Query response body for $label:" >&2
    cat "$response_file" >&2
    docker compose logs api worker >&2 || true
    die "query failed for $label (HTTP $http_code)"
  fi

  cp "$response_file" "$output_file"

  jq -er '
    .query_id
    and .answer.answer_text
    and .support_state
    and .answer_mode
    and .answer.generator_version
    and .citations.material_doc_ids
  ' "$output_file" >/dev/null || die "missing comparison fields for $label"
}

register_doc() {
  local title=$1
  local doc_id=$2

  DOC_TITLES+=("$title")
  DOC_IDS+=("$doc_id")
}

title_for_doc_id() {
  local target_doc_id=$1
  local i

  for ((i = 0; i < ${#DOC_IDS[@]}; i++)); do
    if [ "${DOC_IDS[$i]}" = "$target_doc_id" ]; then
      printf '%s' "${DOC_TITLES[$i]}"
      return 0
    fi
  done

  printf '%s' "$target_doc_id"
}

format_material_docs() {
  local json_file=$1
  local found=0
  local doc_id
  local title
  local pieces=""

  while IFS= read -r doc_id; do
    [ -n "$doc_id" ] || continue
    title=$(title_for_doc_id "$doc_id")
    if [ "$found" -eq 1 ]; then
      pieces="$pieces, "
    fi
    pieces="$pieces$title ($doc_id)"
    found=1
  done < <(jq -r '.citations.material_doc_ids[]?' "$json_file")

  if [ "$found" -eq 0 ]; then
    printf 'none'
    return 0
  fi

  printf '%s' "$pieces"
}

require_material_doc() {
  local json_file=$1
  local label=$2
  local doc_id=$3
  local title

  if ! jq -e --arg doc_id "$doc_id" '.citations.material_doc_ids | index($doc_id) != null' \
    "$json_file" >/dev/null; then
    title=$(title_for_doc_id "$doc_id")
    die "$label did not cite required document '$title' ($doc_id)"
  fi
}

extract_scalar() {
  local json_file=$1
  local jq_expr=$2

  jq -er "$jq_expr" "$json_file"
}

echo "==> Configuring Docker permissions..."
export PARITY_UID="$(id -u)"
export PARITY_GID="$(id -g)"

echo "==> Setting shared backend variables..."
export PARITY_EMBEDDING_BACKEND="sentence-transformers"
export PARITY_ANSWER_GENERATOR_BACKEND="deterministic"
export OLLAMA_BASE_URL="$OLLAMA_BASE_URL_FOR_CONTAINERS"
unset PARITY_ANSWER_GENERATOR_MODEL

if [ "$USE_HOST_OLLAMA" = "1" ]; then
  echo "==> Using host Ollama for GPU-backed generation..."
  ensure_host_ollama
  echo "==> Starting application stack without the Docker Ollama service..."
  docker compose up -d --build db migrate api worker
else
  echo "==> Starting application stack via docker-compose..."
  make docker-up-build
fi

echo "==> Waiting for API to become ready..."
wait_for_http_ready "API" "$API_URL/readyz" 30 2 \
  || {
    docker compose logs api db worker migrate
    die "API did not become ready in time"
  }

echo "==> Generating synthetic markdown corpus..."
ATLAS_DOC_PATH="$SCRATCH_DIR/atlas.md"
BEACON_DOC_PATH="$SCRATCH_DIR/beacon.md"
COMET_DOC_PATH="$SCRATCH_DIR/comet.md"

cat >"$ATLAS_DOC_PATH" <<'MD'
# Atlas Cache Design

## Caching Strategy
Atlas uses a write-through cache. Every write updates the backing store and cache in the same operation.

## Freshness Guarantees
Atlas performs immediate cache invalidation after each control-plane update. Operators treat stale reads as unacceptable.

## Tradeoff
Atlas is consistency-first and accepts higher write latency to preserve stricter freshness guarantees.
MD

cat >"$BEACON_DOC_PATH" <<'MD'
# Beacon Dashboard Cache

## Caching Strategy
Beacon uses a time-to-live cache for dashboard reads. Cached entries remain available for 15 minutes before refresh.

## Freshness Guarantees
Beacon explicitly allows stale reads within the TTL window when that improves response time for high-traffic dashboards.

## Tradeoff
Beacon is latency-first and accepts weaker freshness in exchange for lower read latency.
MD

cat >"$COMET_DOC_PATH" <<'MD'
# Comet Background Notes

## Overview
Comet is an unrelated batch analytics service focused on overnight report generation.

## Scheduling
Comet runs nightly aggregation jobs and does not define an online request cache policy.
MD

echo "==> Uploading markdown corpus..."
ATLAS_DOC_ID=$(upload_document "Atlas Cache Design" "$ATLAS_DOC_PATH")
register_doc "Atlas Cache Design" "$ATLAS_DOC_ID"
echo "Uploaded Atlas Cache Design as $ATLAS_DOC_ID"

BEACON_DOC_ID=$(upload_document "Beacon Dashboard Cache" "$BEACON_DOC_PATH")
register_doc "Beacon Dashboard Cache" "$BEACON_DOC_ID"
echo "Uploaded Beacon Dashboard Cache as $BEACON_DOC_ID"

COMET_DOC_ID=$(upload_document "Comet Background Notes" "$COMET_DOC_PATH")
register_doc "Comet Background Notes" "$COMET_DOC_ID"
echo "Uploaded Comet Background Notes as $COMET_DOC_ID"

echo "==> Waiting for all documents to reach READY..."
wait_for_document_ready "$ATLAS_DOC_ID" "Atlas Cache Design"
wait_for_document_ready "$BEACON_DOC_ID" "Beacon Dashboard Cache"
wait_for_document_ready "$COMET_DOC_ID" "Comet Background Notes"

echo "==> Verifying embedding execution from worker logs..."
if ! docker compose logs worker | grep -q "embedding model generated"; then
  die "embedding log proof not found in worker logs"
fi
docker compose logs worker | grep "embedding model generated" | tail -n 1

DETERMINISTIC_QUERY_JSON="$SCRATCH_DIR/query-deterministic.json"
OLLAMA_QUERY_JSON="$SCRATCH_DIR/query-ollama.json"

echo "==> Running deterministic query..."
echo "Question: $QUESTION"
run_query "deterministic" "$DETERMINISTIC_QUERY_JSON"

DET_QUERY_ID=$(extract_scalar "$DETERMINISTIC_QUERY_JSON" '.query_id')
DET_ANSWER=$(extract_scalar "$DETERMINISTIC_QUERY_JSON" '.answer.answer_text')
DET_SUPPORT_STATE=$(extract_scalar "$DETERMINISTIC_QUERY_JSON" '.support_state')
DET_ANSWER_MODE=$(extract_scalar "$DETERMINISTIC_QUERY_JSON" '.answer_mode')
DET_GENERATOR_VERSION=$(extract_scalar "$DETERMINISTIC_QUERY_JSON" '.answer.generator_version')

[ -n "$DET_ANSWER" ] || die "deterministic answer text is empty"
[ "$DET_SUPPORT_STATE" = "sufficient" ] \
  || die "deterministic support_state must be sufficient, got '$DET_SUPPORT_STATE'"
[ "$DET_GENERATOR_VERSION" = "answer_generation.deterministic.v1" ] \
  || die "unexpected deterministic generator version '$DET_GENERATOR_VERSION'"
require_material_doc "$DETERMINISTIC_QUERY_JSON" "deterministic run" "$ATLAS_DOC_ID"
require_material_doc "$DETERMINISTIC_QUERY_JSON" "deterministic run" "$BEACON_DOC_ID"

echo "==> Preparing Ollama for the second query run..."
if [ "$USE_HOST_OLLAMA" = "1" ]; then
  ensure_host_ollama
else
  wait_for_http_ready "Ollama" "$OLLAMA_HEALTH_URL" 30 2 \
    || die "Ollama did not become ready in time"
  docker compose exec ollama ollama pull "$OLLAMA_MODEL"
fi

echo "==> Recreating only the API service with Ollama generation..."
export PARITY_ANSWER_GENERATOR_BACKEND="ollama"
export PARITY_ANSWER_GENERATOR_MODEL="$OLLAMA_MODEL"
docker compose up -d --force-recreate api

wait_for_http_ready "API" "$API_URL/readyz" 30 2 \
  || {
    docker compose logs api db worker migrate
    die "API did not become ready after switching to Ollama"
  }

echo "==> Running Ollama query against the existing corpus..."
run_query "ollama" "$OLLAMA_QUERY_JSON"

if [ "$USE_HOST_OLLAMA" = "1" ]; then
  echo "==> Host Ollama processor snapshot..."
  ollama ps || true
fi

OLLAMA_QUERY_ID=$(extract_scalar "$OLLAMA_QUERY_JSON" '.query_id')
OLLAMA_ANSWER=$(extract_scalar "$OLLAMA_QUERY_JSON" '.answer.answer_text')
OLLAMA_SUPPORT_STATE=$(extract_scalar "$OLLAMA_QUERY_JSON" '.support_state')
OLLAMA_ANSWER_MODE=$(extract_scalar "$OLLAMA_QUERY_JSON" '.answer_mode')
OLLAMA_GENERATOR_VERSION=$(extract_scalar "$OLLAMA_QUERY_JSON" '.answer.generator_version')

[ -n "$OLLAMA_ANSWER" ] || die "Ollama answer text is empty"
[ "$OLLAMA_GENERATOR_VERSION" = "answer_generation.ollama.v1" ] \
  || die "unexpected Ollama generator version '$OLLAMA_GENERATOR_VERSION'"
require_material_doc "$OLLAMA_QUERY_JSON" "ollama run" "$ATLAS_DOC_ID"
require_material_doc "$OLLAMA_QUERY_JSON" "ollama run" "$BEACON_DOC_ID"

SUPPORT_STATE_MATCH="false"
ANSWER_MODE_MATCH="false"
ANSWER_TEXTS_DIFFER="true"

if [ "$DET_SUPPORT_STATE" = "$OLLAMA_SUPPORT_STATE" ]; then
  SUPPORT_STATE_MATCH="true"
else
  die "support_state mismatch: deterministic='$DET_SUPPORT_STATE', ollama='$OLLAMA_SUPPORT_STATE'"
fi

if [ "$DET_ANSWER_MODE" = "$OLLAMA_ANSWER_MODE" ]; then
  ANSWER_MODE_MATCH="true"
else
  die "answer_mode mismatch: deterministic='$DET_ANSWER_MODE', ollama='$OLLAMA_ANSWER_MODE'"
fi

if [ "$DET_ANSWER" = "$OLLAMA_ANSWER" ]; then
  ANSWER_TEXTS_DIFFER="false"
fi

echo "==> Verifying Ollama generation from API logs..."
if ! docker compose logs api | grep -q "llm generated"; then
  die "Ollama log proof not found in API logs"
fi
docker compose logs api | grep "llm generated" | tail -n 1

DET_MATERIAL_DOCS=$(format_material_docs "$DETERMINISTIC_QUERY_JSON")
OLLAMA_MATERIAL_DOCS=$(format_material_docs "$OLLAMA_QUERY_JSON")

echo ""
echo "=================================================="
echo "Multi-Document Answer Comparison Report"
echo "=================================================="
echo "Workspace: $WORKSPACE"
echo "Question: $QUESTION"
echo ""
echo "Deterministic run:"
echo "  query_id: $DET_QUERY_ID"
echo "  support_state: $DET_SUPPORT_STATE"
echo "  answer_mode: $DET_ANSWER_MODE"
echo "  generator_version: $DET_GENERATOR_VERSION"
echo "  cited_docs: $DET_MATERIAL_DOCS"
echo "  answer: $DET_ANSWER"
echo ""
echo "Ollama run:"
echo "  query_id: $OLLAMA_QUERY_ID"
echo "  support_state: $OLLAMA_SUPPORT_STATE"
echo "  answer_mode: $OLLAMA_ANSWER_MODE"
echo "  generator_version: $OLLAMA_GENERATOR_VERSION"
echo "  cited_docs: $OLLAMA_MATERIAL_DOCS"
echo "  answer: $OLLAMA_ANSWER"
echo ""
echo "Comparison:"
echo "  support_state_match: $SUPPORT_STATE_MATCH"
echo "  answer_mode_match: $ANSWER_MODE_MATCH"
echo "  deterministic_cites_atlas_and_beacon: true"
echo "  ollama_cites_atlas_and_beacon: true"
echo "  answer_texts_differ: $ANSWER_TEXTS_DIFFER"
