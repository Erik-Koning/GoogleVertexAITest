# Quick Start Guide

This guide walks you through setting up local development and testing with PDF documents.

## Prerequisites

- Python 3.11+
- A GCP project with the following APIs enabled:
  - Vertex AI API
  - Discovery Engine API (Vertex AI Search)
  - Cloud Storage API
- A Google API key (for Gemini access in dev mode)
- Vertex AI Search data store and engine already created (via Terraform or console)

## Step 1: Environment Setup

### 1.1 Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 1.2 Configure Environment Variables

Copy the example env file and edit it:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```bash
# Required for local development
ENVIRONMENT=dev
GCP_PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1

# Your Google API key (get from https://aistudio.google.com/app/apikey)
GOOGLE_API_KEY=AIzaSy...your-api-key

# Vertex AI Search (create via Terraform or GCP console)
VERTEX_SEARCH_DATA_STORE_ID=fund-knowledge-base
VERTEX_SEARCH_ENGINE_ID=fund-search-engine

# GCS bucket for PDFs
GCS_BUCKET_NAME=your-project-id-fund-documents

# PDF sync settings
SYNC_PDFS_IN_DEV=false  # Set to true when you want to sync PDFs
PDF_BASE_URL=https://yoursite.com/funds

# Optional
GEMINI_MODEL=gemini-1.5-pro
```

### 1.3 GCP Authentication for Vertex AI Search

Even in dev mode, Vertex AI Search requires GCP project authentication:

```bash
# Login with your GCP account
gcloud auth application-default login

# Set your project
gcloud config set project your-gcp-project-id
```

## Step 2: Adding PDF Documents

### 2.1 Add PDF Files

Place your PDF files in the `/pdfs` directory:

```bash
cp /path/to/your-fund-facts.pdf pdfs/
cp /path/to/tfsa-guide.pdf pdfs/
```

### 2.2 Add Metadata

Edit `src/startup/metadata.py` to add metadata for each PDF:

```python
PDF_METADATA = {
    "your-fund-facts.pdf": {
        "display_name": "Your Fund - Fund Facts",
        "source_url": "https://yoursite.com/funds/your-fund-facts.pdf",
        "category": "fund_facts",  # Options: fund_facts, tfsa, rrsp
        "fund_code": "YOUR-FUND",
    },
    "tfsa-guide.pdf": {
        "display_name": "TFSA Complete Guide",
        "source_url": "https://yoursite.com/guides/tfsa-guide.pdf",
        "category": "tfsa",
    },
    # Add more PDFs...
}
```

**Category determines routing:**
- `fund_facts` → FundFactsTool
- `tfsa` → TFSATool
- `rrsp` → RRSPTool

## Step 3: Sync PDFs to Vertex AI Search

### 3.1 Enable PDF Sync

Set the environment variable to enable syncing:

```bash
export SYNC_PDFS_IN_DEV=true
```

Or update your `.env` file:
```bash
SYNC_PDFS_IN_DEV=true
```

### 3.2 Run the Application

Start the server - PDFs will sync automatically on startup:

```bash
uvicorn src.main:app --reload --port 8080
```

You should see output like:
```
Starting Fund RAG Agent...
Uploaded: your-fund-facts.pdf
Uploaded: tfsa-guide.pdf
Triggering Vertex AI Search import for 2 files...
Import operation started: projects/.../operations/...
Fund RAG Agent ready.
```

### 3.3 Wait for Import

The Vertex AI Search import runs asynchronously. Check status in the GCP console:
1. Go to [Vertex AI Search](https://console.cloud.google.com/gen-app-builder/engines)
2. Select your data store
3. Check the "Documents" tab for import status

Import typically takes 2-5 minutes for a few PDFs.

## Step 4: Test Your Setup

### 4.1 Test via API Docs

Open http://localhost:8080/docs in your browser and use the interactive API.

### 4.2 Test via cURL

```bash
# Basic query
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is a TFSA?"}'

# Query with chart
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Compare the MER of all funds and show me a chart"}'

# Fund-specific query
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the risk rating for Fund A?"}'
```

### 4.3 Test via Python

```python
import requests

response = requests.post(
    "http://localhost:8080/chat",
    json={"message": "What are the TFSA contribution limits?"}
)

data = response.json()
print("Reply:", data["reply"])
print("Sources:", data["sources"])

# If chart was generated
if data.get("image_base64"):
    print("Chart type:", data["chart_type"])
    # Save the chart
    import base64
    img_data = data["image_base64"].replace("data:image/png;base64,", "")
    with open("chart.png", "wb") as f:
        f.write(base64.b64decode(img_data))
```

### 4.4 Run Automated Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py
```

## Step 5: Troubleshooting

### Common Issues

**"No relevant documents found"**
- Check that PDFs were uploaded to GCS: `gsutil ls gs://your-bucket/documents/`
- Verify Vertex AI Search import completed in GCP console
- Ensure PDF metadata has correct `category` matching your query

**"GOOGLE_API_KEY not set"**
- Make sure `.env` file exists and has `GOOGLE_API_KEY` set
- Or export it: `export GOOGLE_API_KEY=your-key`

**"Permission denied" errors**
- Run `gcloud auth application-default login`
- Verify your account has access to the GCP project

**PDF sync not running**
- Check `SYNC_PDFS_IN_DEV=true` is set
- Verify PDFs exist in `/pdfs` directory
- Check GCS bucket exists and you have write access

### Checking Logs

```bash
# Run with debug output
ENVIRONMENT=dev uvicorn src.main:app --reload --port 8080 --log-level debug
```

### Verify GCS Upload

```bash
# List uploaded PDFs
gsutil ls gs://your-bucket/documents/

# Check metadata
gsutil stat gs://your-bucket/documents/your-fund-facts.pdf
```

### Verify Vertex AI Search

```bash
# Search via gcloud (requires alpha commands)
gcloud alpha discovery-engine search \
  --project=your-project-id \
  --location=global \
  --engine=fund-search-engine \
  --query="TFSA contribution"
```

## Quick Reference

### Environment Variables Summary

| Variable | Required | Example |
|----------|----------|---------|
| `ENVIRONMENT` | Yes | `dev` |
| `GCP_PROJECT_ID` | Yes | `my-project-123` |
| `GOOGLE_API_KEY` | Yes (dev) | `AIzaSy...` |
| `GCS_BUCKET_NAME` | Yes | `my-project-123-fund-documents` |
| `VERTEX_SEARCH_DATA_STORE_ID` | Yes | `fund-knowledge-base` |
| `VERTEX_SEARCH_ENGINE_ID` | Yes | `fund-search-engine` |
| `SYNC_PDFS_IN_DEV` | No | `true` or `false` |
| `PDF_BASE_URL` | No | `https://example.com/funds` |
| `GCP_REGION` | No | `us-central1` |
| `GEMINI_MODEL` | No | `gemini-1.5-pro` |

### Useful Commands

```bash
# Start server
uvicorn src.main:app --reload --port 8080

# Run tests
pytest

# Lint code
ruff check . && ruff format .

# Sync PDFs manually (via startup)
SYNC_PDFS_IN_DEV=true python -c "import asyncio; from src.startup import sync_pdfs_on_startup; asyncio.run(sync_pdfs_on_startup())"

# Trigger Vertex import manually
./scripts/import_docs.sh
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send message, get response |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API docs |
| `/` | GET | API info |
