# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fund RAG Agent - A RAG-powered assistant for Fund Facts, TFSA, and RRSP information. Built with Python, FastAPI, LangChain, FAISS (local vector search), and Gemini.

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
           Route + Chart?    FAISS Search + Gemini RAG
                                  ↓
                           Chart Generator (optional)
```

### Core Components

- **`src/main.py`** - FastAPI app with `/chat` endpoint, FAISS index validation on startup
- **`src/orchestrator/router.py`** - LangChain router that determines tool + chart parameters
- **`src/tools/`** - Specialist tools (TFSATool, RRSPTool, FundFactsTool) with local FAISS RAG
- **`src/tools/local_search.py`** - FAISS vector search client for document retrieval
- **`src/charts/`** - Matplotlib chart generation with Gemini structured output for data extraction
- **`src/startup/pdf_sync.py`** - Validates FAISS index exists on startup

### Request Flow

1. User sends message to `POST /chat`
2. Orchestrator routes query to appropriate tool (tfsa/rrsp/fund_facts) and detects chart requests
3. Tool queries local FAISS index with topic-specific filter
4. Tool generates RAG response via Gemini with retrieved context
5. If `generate_chart=True`, extracts data via Gemini structured output and generates Matplotlib chart
6. Returns response with reply, sources, and optional base64 chart image

## Key Patterns

### Adding a New Tool

1. Create `src/tools/new_tool.py` extending `BaseTool`
2. Set `search_filter` for FAISS metadata filtering (e.g., `"category:new_topic"`)
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

### FAISS Index

The FAISS index should be pre-built and placed at `FAISS_INDEX_PATH`. The index must contain:
- `index.faiss` - The vector index file
- `index.pkl` - Metadata/docstore pickle file

Documents in the index should have metadata including: `title`, `source_url`, `category`, `page`.

## Configuration

### Environment Variables

```bash
ENVIRONMENT=dev                      # dev | workstation | prod
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
FAISS_INDEX_PATH=./faiss_index       # Path to FAISS index directory
GEMINI_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=your-key              # Dev only
PDF_BASE_URL=https://yoursite.com/funds
```

### Authentication

| Environment | Method | Usage |
|-------------|--------|-------|
| dev | API Key | Set `GOOGLE_API_KEY` env var |
| workstation | Service Account (ADC) | Uses workstation's attached service account |
| prod | Service Account (ADC) | Uses Cloud Run's service account |

Dev uses `langchain_google_genai`, workstation/prod use `langchain_google_vertexai`.

## Infrastructure (Terraform)

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars  # Edit values
terraform init
terraform plan
terraform apply
```

Creates: Cloud Run service, IAM roles for Gemini access.

## Deployment

```bash
# Full deployment
./scripts/deploy.sh
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
