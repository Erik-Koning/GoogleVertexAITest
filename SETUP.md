# Environment Setup Guide

This guide explains how to configure your `.env` file and `terraform.tfvars` for different environments.

## Quick Reference

| Environment | `.env` ENVIRONMENT | Auth Method | Use Case |
|-------------|-------------------|-------------|----------|
| Local Dev | `dev` | API Key (`GOOGLE_API_KEY`) | Local machine development |
| Cloud Workstation | `workstation` | Service Account (ADC) | GCP Cloud Workstation |
| Production | `prod` | Service Account (ADC) | Cloud Run deployment |

## Prerequisites

- Terraform infrastructure deployed (see [README.md](README.md#deploy-infrastructure-with-terraform))
- Python 3.11 installed
- Google Cloud CLI installed and authenticated

## Step 1: Get Terraform Outputs

After running `terraform apply`, retrieve the created resource IDs:

```bash
cd infra

# View all outputs
terraform output

# Example output:
# cloud_run_url = "https://fund-rag-agent-xxxxx-uc.a.run.app"
# gcs_bucket_name = "vertex-ai-rag-agent17-fund-documents"
# service_account_email = "fund-rag-agent-sa@vertex-ai-rag-agent17.iam.gserviceaccount.com"
# vertex_search_data_store_id = "fund-knowledge-base"
# vertex_search_engine_id = "fund-search-engine"
```

## Step 2: Create Your .env File

### Option A: Manual Creation

Create `.env` in the project root:

```bash
cd /path/to/rag-knowledge-assistant

cat > .env << EOF
# Environment
ENVIRONMENT=dev

# GCP Project
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Gemini API Key (get from https://aistudio.google.com/app/apikey)
GOOGLE_API_KEY=your-api-key-here

# Vertex AI Search (from terraform output)
VERTEX_SEARCH_DATA_STORE_ID=fund-knowledge-base
VERTEX_SEARCH_ENGINE_ID=fund-search-engine

# GCS Bucket (from terraform output)
GCS_BUCKET_NAME=your-project-id-fund-documents

# Optional settings
GEMINI_MODEL=gemini-2.5-flash
SYNC_PDFS_IN_DEV=false
PDF_BASE_URL=
EOF
```

### Option B: Auto-Generate from Terraform

Run this script from the `infra/` directory to auto-generate `.env`:

```bash
cd infra

cat > ../.env << EOF
# Environment
ENVIRONMENT=dev

# GCP Project
GCP_PROJECT_ID=$(terraform output -raw gcs_bucket_name | sed 's/-fund-documents$//')
GCP_REGION=us-central1

# Gemini API Key (replace with your actual key)
GOOGLE_API_KEY=REPLACE_WITH_YOUR_API_KEY

# Vertex AI Search (from terraform output)
VERTEX_SEARCH_DATA_STORE_ID=$(terraform output -raw vertex_search_data_store_id)
VERTEX_SEARCH_ENGINE_ID=$(terraform output -raw vertex_search_engine_id)

# GCS Bucket (from terraform output)
GCS_BUCKET_NAME=$(terraform output -raw gcs_bucket_name)

# Optional settings
GEMINI_MODEL=gemini-2.5-flash
SYNC_PDFS_IN_DEV=false
PDF_BASE_URL=
EOF

echo "Created .env file. Don't forget to add your GOOGLE_API_KEY!"
```

## Step 3: Add Your Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key and add it to your `.env` file:

```bash
# Edit .env and replace REPLACE_WITH_YOUR_API_KEY with your actual key
GOOGLE_API_KEY=AIzaSy...your-actual-key
```

## Step 4: Verify Configuration

Test that your configuration is correct:

```bash
# Activate virtual environment
source .venv/bin/activate

# Test configuration loads
python -c "
from src.config import get_settings
s = get_settings()
print(f'Environment: {s.environment}')
print(f'Project ID: {s.gcp_project_id}')
print(f'API Key set: {bool(s.google_api_key)}')
print(f'Data Store: {s.vertex_search_data_store_id}')
print(f'Engine ID: {s.vertex_search_engine_id}')
print(f'GCS Bucket: {s.gcs_bucket_name}')
"
```

Expected output:
```
Environment: dev
Project ID: your-project-id
API Key set: True
Data Store: fund-knowledge-base
Engine ID: fund-search-engine
GCS Bucket: your-project-id-fund-documents
```

## Step 5: Run the Application

```bash
# Start the server
uvicorn src.main:app --reload --port 8080

# Test it works
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is a TFSA?"}'
```

## Environment Variables Reference

| Variable | Required | Source | Description |
|----------|----------|--------|-------------|
| `ENVIRONMENT` | Yes | Manual | `dev`, `workstation`, or `prod` |
| `GCP_PROJECT_ID` | Yes | Manual | Your GCP project ID |
| `GCP_REGION` | No | Manual | Default: `us-central1` |
| `GOOGLE_API_KEY` | Dev only | [AI Studio](https://aistudio.google.com/app/apikey) | Gemini API key (dev only) |
| `VERTEX_SEARCH_DATA_STORE_ID` | Yes | `terraform output` | Vertex AI Search data store |
| `VERTEX_SEARCH_ENGINE_ID` | Yes | `terraform output` | Vertex AI Search engine |
| `GCS_BUCKET_NAME` | Yes | `terraform output` | GCS bucket for PDFs |
| `GEMINI_MODEL` | No | Manual | Default: `gemini-2.5-flash` |
| `ALLOW_GENERAL_KNOWLEDGE_FALLBACK` | No | Manual | Default: `true` - use Gemini knowledge when no docs |
| `SYNC_PDFS_IN_DEV` | No | Manual | Set `true` to sync PDFs locally |
| `PDF_BASE_URL` | No | Manual | Base URL for PDF source links |

## Example .env Files

### Local Development (API Key)

```bash
# .env for local development
ENVIRONMENT=dev
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GOOGLE_API_KEY=AIzaSy...your-api-key    # Required for dev
VERTEX_SEARCH_DATA_STORE_ID=fund-knowledge-base
VERTEX_SEARCH_ENGINE_ID=fund-search-engine
GCS_BUCKET_NAME=your-project-id-fund-documents
GEMINI_MODEL=gemini-2.5-flash
```

### Cloud Workstation (Service Account)

```bash
# .env for Cloud Workstation - NO API KEY NEEDED
ENVIRONMENT=workstation
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
# NO GOOGLE_API_KEY - uses attached service account
VERTEX_SEARCH_DATA_STORE_ID=fund-knowledge-base
VERTEX_SEARCH_ENGINE_ID=fund-search-engine
GCS_BUCKET_NAME=your-project-id-fund-documents
GEMINI_MODEL=gemini-2.5-flash
```

### Production / Docker (Service Account)

```bash
# .env for production/Docker - NO API KEY NEEDED
ENVIRONMENT=prod
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
# NO GOOGLE_API_KEY - uses service account via ADC
VERTEX_SEARCH_DATA_STORE_ID=fund-knowledge-base
VERTEX_SEARCH_ENGINE_ID=fund-search-engine
GCS_BUCKET_NAME=your-project-id-fund-documents
GEMINI_MODEL=gemini-2.5-flash
```

## Terraform Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `project_id` | Yes | - | Your GCP project ID |
| `region` | No | `us-central1` | GCP region |
| `data_store_id` | No | `fund-knowledge-base` | Vertex AI Search data store ID |
| `engine_id` | No | `fund-search-engine` | Vertex AI Search engine ID |
| `deploy_cloud_run` | No | `false` | Deploy Cloud Run service |
| `build_container` | No | `false` | Build Docker image before deploy |
| `container_image` | No | auto-generated | Custom container image URL |

### Example terraform.tfvars

```hcl
# For Cloud Workstation / Local Dev (no Cloud Run)
project_id       = "your-project-id"
deploy_cloud_run = false

# For Production (with Cloud Run)
project_id       = "your-project-id"
deploy_cloud_run = true
build_container  = true
```

## Troubleshooting

### "GOOGLE_API_KEY not set"

Make sure your `.env` file has the API key:
```bash
grep GOOGLE_API_KEY .env
```

### "Permission denied" on Vertex AI Search

Authenticate with Application Default Credentials:
```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

### "Data store not found"

Verify the data store exists:
```bash
gcloud alpha discovery-engine data-stores list \
  --location=global \
  --project=YOUR_PROJECT_ID
```

### Config not loading from .env

Make sure:
1. `.env` is in the project root (same level as `src/`)
2. No syntax errors in `.env` (no spaces around `=`)
3. Virtual environment is activated

## Security Notes

- **Never commit `.env` to git** - it's already in `.gitignore`
- **Never commit `key.json`** - service account keys should stay local
- **Rotate API keys** if accidentally exposed
- **Use service accounts** in production, not API keys
