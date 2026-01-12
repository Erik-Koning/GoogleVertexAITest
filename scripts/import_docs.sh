#!/bin/bash
# Trigger Vertex AI Search document import from GCS

set -e

PROJECT_ID="${GCP_PROJECT_ID:-}"
DATA_STORE_ID="${VERTEX_SEARCH_DATA_STORE_ID:-fund-knowledge-base}"
BUCKET_NAME="${GCS_BUCKET_NAME:-${PROJECT_ID}-fund-documents}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID is not set"
    exit 1
fi

echo "Triggering document import..."
echo "Project: ${PROJECT_ID}"
echo "Data Store: ${DATA_STORE_ID}"
echo "Bucket: ${BUCKET_NAME}"

# Use gcloud to trigger import
gcloud alpha discovery-engine documents import \
    --project="${PROJECT_ID}" \
    --location="global" \
    --data-store="${DATA_STORE_ID}" \
    --gcs-uri="gs://${BUCKET_NAME}/documents/*.pdf" \
    --reconciliation-mode="incremental"

echo "Import triggered. Check the Discovery Engine console for status."
