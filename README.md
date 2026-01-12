# Fund RAG Agent

A RAG-powered assistant for Fund Facts, TFSA, and RRSP information. Built with Python, FastAPI, LangChain, Vertex AI Search, and Gemini.

## Architecture

```
POST /chat --> Orchestrator --> Tool (TFSA/RRSP/Fund Facts) --> Response
                   |                      |
             Route + Chart?         Vertex AI Search + Gemini RAG
                                          |
                                   Chart Generator (optional)
```

### How It Works

1. User sends a message to `POST /chat`
2. **Orchestrator** (LangChain + Gemini Flash) analyzes the query to determine:
   - Which tool to use (`tfsa`, `rrsp`, or `fund_facts`)
   - Whether to generate a chart and what type
3. **Tool** queries Vertex AI Search with topic-specific filters
4. **Gemini** generates a RAG response using retrieved document context
5. If requested, **Chart Generator** extracts data via Gemini structured output and creates a Matplotlib chart
6. Returns response with text reply, optional base64 chart image, and source citations

## Quick Start

### Prerequisites

- Python 3.11+
- GCP project with Vertex AI Search enabled
- Google API key (for local development)

### Local Development

```bash
# Clone and setup
git clone <repo-url>
cd fund-rag-agent

# Run the setup script
./scripts/local_dev.sh

# Or manually:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your config
uvicorn src.main:app --reload --port 8080
```

The API will be available at http://localhost:8080 with docs at http://localhost:8080/docs.

### Running Tests

```bash
pytest                          # All tests
pytest tests/test_charts.py     # Single file
pytest -k "test_bar_chart"      # Single test by name
```

### Linting

```bash
ruff check .
ruff format .
mypy .
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ENVIRONMENT` | `dev` or `prod` | Yes |
| `GCP_PROJECT_ID` | Your GCP project ID | Yes |
| `GCP_REGION` | GCP region (default: `us-central1`) | No |
| `GOOGLE_API_KEY` | API key for Gemini (dev only) | Dev only |
| `GCS_BUCKET_NAME` | GCS bucket for PDF documents | Yes |
| `VERTEX_SEARCH_DATA_STORE_ID` | Vertex AI Search data store ID | Yes |
| `VERTEX_SEARCH_ENGINE_ID` | Vertex AI Search engine ID | Yes |
| `GEMINI_MODEL` | Gemini model (default: `gemini-1.5-pro`) | No |
| `SYNC_PDFS_IN_DEV` | Sync PDFs in dev mode (default: `false`) | No |
| `PDF_BASE_URL` | Base URL for PDF source links | No |

### Authentication

| Environment | Method | Description |
|-------------|--------|-------------|
| `dev` | API Key | Uses `GOOGLE_API_KEY` environment variable |
| `prod` | ADC | Uses Application Default Credentials (service account on Cloud Run) |

## API Reference

### POST /chat

Send a message and receive a response with optional chart.

**Request:**
```json
{
  "message": "What is the MER for Fund A? Show me a chart comparing all funds."
}
```

**Response:**
```json
{
  "reply": "Fund A has an MER of 1.2%. Here's how it compares...",
  "chart_type": "bar",
  "image_base64": "data:image/png;base64,iVBORw0KGgo...",
  "sources": [
    {
      "pdf_name": "Fund A Facts",
      "pdf_url": "https://example.com/funds/fund-a-facts.pdf",
      "page": 1,
      "snippet": "Management Expense Ratio: 1.2%..."
    }
  ]
}
```

### GET /health

Health check endpoint.

### GET /

API information and available endpoints.

## Chart Types

| Type | Use Case |
|------|----------|
| `bar` | Comparisons (MER, fund performance) |
| `line` | Time series, trends |
| `pie` | Distributions, allocations |
| `scatter` | Correlations (risk vs return) |
| `histogram` | Frequency distributions |

## Project Structure

```
fund-rag-agent/
├── src/
│   ├── main.py                 # FastAPI app, /chat endpoint
│   ├── config.py               # Environment settings
│   ├── orchestrator/
│   │   ├── router.py           # LangChain router
│   │   └── prompts.py          # Routing prompts
│   ├── tools/
│   │   ├── base.py             # BaseTool with Vertex Search RAG
│   │   ├── tfsa_tool.py        # TFSA specialist
│   │   ├── rrsp_tool.py        # RRSP specialist
│   │   ├── fund_facts_tool.py  # Fund Facts specialist
│   │   ├── vertex_search.py    # Vertex AI Search client
│   │   └── schemas.py          # Pydantic schemas
│   ├── charts/
│   │   ├── generator.py        # Matplotlib chart generation
│   │   ├── data_extractor.py   # Gemini structured output
│   │   └── types.py            # Chart type definitions
│   ├── startup/
│   │   ├── pdf_sync.py         # PDF sync to GCS + Vertex
│   │   └── metadata.py         # PDF metadata definitions
│   └── utils/
│       ├── gemini.py           # Gemini client factory
│       └── responses.py        # Response formatting
├── tests/
├── infra/                      # Terraform infrastructure
├── scripts/                    # Deployment scripts
├── pdfs/                       # PDF documents
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

## Adding Documents

### Adding PDF Documents

1. Add PDF files to the `/pdfs` directory
2. Add metadata to `src/startup/metadata.py`:
   ```python
   PDF_METADATA = {
       "my-new-fund.pdf": {
           "display_name": "My New Fund - Fund Facts",
           "source_url": "https://example.com/funds/my-new-fund.pdf",
           "category": "fund_facts",  # or "tfsa", "rrsp"
           "fund_code": "NEW-FUND",
       },
   }
   ```
3. On startup, PDFs automatically sync to GCS and trigger Vertex AI import

### Adding a New Tool

1. Create `src/tools/new_tool.py`:
   ```python
   from src.tools.base import BaseTool

   class NewTool(BaseTool):
       search_filter = "category:new_category"
       system_prompt = "You are an expert in..."

       @property
       def name(self) -> str:
           return "new_tool"
   ```
2. Register in `src/tools/__init__.py`
3. Add routing rules in `src/orchestrator/prompts.py`
4. Add to orchestrator in `src/orchestrator/router.py`

## Infrastructure

### Terraform Resources

| Resource | Purpose |
|----------|---------|
| `google_storage_bucket` | Store PDF documents |
| `google_discovery_engine_data_store` | Vertex AI Search data store |
| `google_discovery_engine_search_engine` | Search engine config |
| `google_cloud_run_v2_service` | API deployment |
| `google_service_account` | Service identity |
| `google_project_iam_member` | Permissions |

### Deployment

```bash
# Full deployment (build, push, terraform apply)
./scripts/deploy.sh

# Just trigger document import
./scripts/import_docs.sh
```

### Manual Terraform

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars  # Edit values
terraform init
terraform plan
terraform apply
```

## Development

### Key Patterns

- **Dev/Prod Auth**: Dev uses API key, prod uses ADC with service account
- **Checksum-based PDF sync**: Only uploads changed files
- **Non-blocking import**: Vertex AI import runs async, doesn't block startup
- **Structured output**: Uses Gemini JSON mode for chart data extraction

### Running Locally with PDF Sync

To sync PDFs in local development:
```bash
export SYNC_PDFS_IN_DEV=true
uvicorn src.main:app --reload --port 8080
```

## License

[Add your license here]
