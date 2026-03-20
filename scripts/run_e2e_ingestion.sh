#!/usr/bin/env bash

set -eou pipefail

# Ensure cleanup on exit (even if earlier steps fail)
cleanup() {
    echo "====================================="
    echo "Tearing down the stack..."
    echo "====================================="
    make docker-down
    if [[ -n "${TMP_FILE:-}" && -f "${TMP_FILE:-}" ]]; then
        rm "$TMP_FILE"
    fi
}
trap cleanup EXIT

echo "====================================="
echo "1. Starting docker stack..."
echo "====================================="
make docker-up-build

echo "====================================="
echo "2. Waiting for API to be reachable..."
echo "====================================="
MAX_RETRIES=60
RETRY_COUNT=0
until curl -s http://127.0.0.1:8000/readyz > /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "API failed to start in time."
        exit 1
    fi
    sleep 2
done
echo "API is healthy!"

echo "====================================="
echo "3. Creating synthetic markdown file..."
echo "====================================="
TMP_FILE=$(mktemp /tmp/test_doc_XXXXXX.md)
cat << 'EOF' > "$TMP_FILE"
# Test Document
This is a synthetic document for e2e testing.

## Section 1
Here is some content for section 1.
EOF
echo "Created temporary file at $TMP_FILE"

echo "====================================="
echo "4. Uploading document..."
echo "====================================="
RESPONSE=$(curl -s -X POST -F "file=@$TMP_FILE" -F "workspace_id=test_workspace" http://127.0.0.1:8000/documents)
# Using python to parse JSON defensively in case jq is not installed
DOC_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('doc_id', ''))" 2>/dev/null || true)

if [ -z "$DOC_ID" ]; then
    echo "Failed to extract doc_id from response: $RESPONSE"
    exit 1
fi
echo "Document uploaded successfully. doc_id: $DOC_ID"

echo "====================================="
echo "5. Polling document status..."
echo "====================================="
MAX_POLL=60
POLL_COUNT=0
STATUS=""
while [ $POLL_COUNT -lt $MAX_POLL ]; do
    STATUS_RESPONSE=$(curl -s "http://127.0.0.1:8000/documents/$DOC_ID/status")
    STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ingest_status', ''))" 2>/dev/null || true)
    
    if [ "$STATUS" = "ready" ]; then
        echo "Document is ready!"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "Document ingestion failed: $STATUS_RESPONSE"
        exit 1
    fi
    
    POLL_COUNT=$((POLL_COUNT+1))
    echo "Current status: '$STATUS'. Waiting... ($POLL_COUNT/$MAX_POLL)"
    sleep 2
done

if [ "$STATUS" != "ready" ]; then
    echo "Document ingestion timed out. Last status: $STATUS"
    exit 1
fi

echo "====================================="
echo "6. Verifying chunks in database..."
echo "====================================="
docker compose exec -T db psql -U doc-forge -d doc-forge -c "SELECT chunk_id, text FROM chunks WHERE doc_id='$DOC_ID';"
docker compose exec -T db psql -U doc-forge -d doc-forge -c "SELECT chunk_id, embedding_model FROM chunk_embeddings WHERE doc_id='$DOC_ID';"

echo "====================================="
echo "End-to-end ingestion test passed successfully!"
echo "====================================="
