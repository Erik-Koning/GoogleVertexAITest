# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fund RAG Agent - A RAG-powered assistant for Fund Facts, TFSA, and RRSP information. Built with Python, FastAPI, LangChain, Vertex AI Search, and Gemini.

## Development Commands

```bash
# Quick start
./scripts/local_dev.sh

# Manual setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Then edit with your config

# Run the application
uvicorn src.main:app --reload --port 8080

# Run tests
pytest                          # All tests
pytest tests/test_charts.py     # Single file
pytest -k "test_bar_chart"      # Single test by name

# Linting
ruff check .
ruff format .
mypy .
```

## Architecture

```
POST /chat → Orchestrator → Tool (TFSA/RRSP/Fund Facts) → Response
                  ↓               ↓
           Route + Chart?    Vertex AI Search + Gemini RAG
                                  ↓
                           Chart Generator (optional)
```

### Core Components

- **`src/main.py`** - FastAPI app with `/chat` endpoint, PDF sync on startup
- **`src/orchestrator/router.py`** - LangChain router that determines tool + chart parameters
- **`src/tools/`** - Specialist tools (TFSATool, RRSPTool, FundFactsTool) with Vertex AI Search RAG
- **`src/tools/vertex_search.py`** - Vertex AI Search client for document retrieval
- **`src/charts/`** - Matplotlib chart generation with Gemini structured output for data extraction
- **`src/startup/pdf_sync.py`** - Syncs PDFs from `/pdfs` to GCS and triggers Vertex import

### Request Flow

1. User sends message to `POST /chat`
2. Orchestrator routes query to appropriate tool (tfsa/rrsp/fund_facts) and detects chart requests
3. Tool queries Vertex AI Search with topic-specific filter
4. Tool generates RAG response via Gemini with retrieved context
5. If `generate_chart=True`, extracts data via Gemini structured output and generates Matplotlib chart
6. Returns response with reply, sources, and optional base64 chart image

## Key Patterns

### Adding a New Tool

1. Create `src/tools/new_tool.py` extending `BaseTool`
2. Set `search_filter` for Vertex AI Search (e.g., `"category:new_topic"`)
3. Set `system_prompt` with domain-specific instructions
4. Register in `src/tools/__init__.py` and `src/orchestrator/router.py`

### Tool Base Class Pattern

```python
class MyTool(BaseTool):
    search_filter = "category:my_category"
    system_prompt = "You are an expert in..."

    @property
    def name(self) -> str:
        return "my_tool"
```

### Adding PDF Documents

1. Add PDFs to `/pdfs` directory
2. Add metadata to `src/startup/metadata.py` in `PDF_METADATA` dict
3. On startup, PDFs auto-sync to GCS and trigger Vertex AI import

## Configuration

### Environment Variables

```bash
ENVIRONMENT=dev                      # dev | prod
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GCS_BUCKET_NAME=your-bucket
VERTEX_SEARCH_DATA_STORE_ID=fund-knowledge-base
VERTEX_SEARCH_ENGINE_ID=fund-search-engine
GEMINI_MODEL=gemini-1.5-pro
GOOGLE_API_KEY=your-key              # Dev only
SYNC_PDFS_IN_DEV=false               # Set true to sync locally
PDF_BASE_URL=https://yoursite.com/funds
```

### Authentication

| Environment | Method | Usage |
|-------------|--------|-------|
| dev | API Key | Set `GOOGLE_API_KEY` env var |
| prod | ADC | Service account on Cloud Run |

Dev uses `langchain_google_genai`, prod uses `langchain_google_vertexai`.

## Infrastructure (Terraform)

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars  # Edit values
terraform init
terraform plan
terraform apply
```

Creates: GCS bucket, Vertex AI Search data store + engine, Cloud Run service, IAM roles.

## Deployment

```bash
# Full deployment
./scripts/deploy.sh

# Just trigger document import
./scripts/import_docs.sh
```

## Response Schema

```json
{
  "reply": "Answer text...",
  "chart_type": "bar",
  "image_base64": "data:image/png;base64,...",
  "sources": [
    {"pdf_name": "Fund A Facts", "pdf_url": "https://...", "page": 2}
  ]
}
```

## Chart Types

- `bar` - Comparisons (MER, fund performance)
- `line` - Time series, trends
- `pie` - Distributions, allocations
- `scatter` - Correlations (risk vs return)
- `histogram` - Frequency distributions
