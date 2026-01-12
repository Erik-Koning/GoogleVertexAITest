#!/bin/bash
# Debug credentials and start server
# Usage: ./scripts/debug_server.sh

set -e

cd "$(dirname "$0")/.."

echo "============================================================"
echo "Debug: Credentials Check"
echo "============================================================"
echo ""

# Check if key.json exists
if [ -f "./key.json" ]; then
    echo "[1] Found key.json - using service account"
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"
else
    echo "[1] No key.json found - using Application Default Credentials"
    echo "    To use service account, run:"
    echo "    gcloud iam service-accounts keys create ./key.json \\"
    echo "      --iam-account=fund-rag-agent-sa@\$(gcloud config get-value project).iam.gserviceaccount.com"
fi

echo ""
echo "[2] GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
echo ""

echo "[3] Checking credentials with Python..."
python3 << 'PYEOF'
import os
print(f"    Env var: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'NOT SET')}")

from google.auth import default
creds, project = default()
print(f"    Project: {project}")
print(f"    Creds type: {type(creds).__name__}")
if hasattr(creds, 'service_account_email'):
    print(f"    Service account: {creds.service_account_email}")
PYEOF

echo ""
echo "[4] Testing Vertex AI Search..."
python3 scripts/test_search.py
if [ $? -ne 0 ]; then
    echo ""
    echo "Search test failed. Fix the issue above before starting server."
    exit 1
fi

echo ""
echo "============================================================"
echo "Starting Server"
echo "============================================================"
echo ""
echo "Server will be available at: http://localhost:8080"
echo "API docs at: http://localhost:8080/docs"
echo ""

uvicorn src.main:app --reload --port 8080
