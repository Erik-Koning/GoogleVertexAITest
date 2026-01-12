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

- Python 3.11
- GCP project with billing enabled
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed

### 1. Install Python 3.11

**macOS (using pyenv - recommended):**
```bash
# Install pyenv
brew install pyenv

# Add to your shell profile (~/.zshrc or ~/.bashrc)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Restart shell or source profile
source ~/.zshrc

# Install and set Python 3.11
pyenv install 3.11
pyenv local 3.11  # Sets Python 3.11 for this project directory

# Verify
python --version  # Should show Python 3.11.x
```

**macOS (using Homebrew directly):**
```bash
brew install python@3.11

# Use python3.11 explicitly or add to PATH
echo 'export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.11 python3.11-venv python3.11-dev

# Verify
python3.11 --version
```

**Windows:**
```powershell
# Download installer from https://www.python.org/downloads/release/python-3110/
# Or use winget:
winget install Python.Python.3.11

# Verify
python --version
```

### 2. Install Google Cloud CLI

**macOS:**
```bash
brew install google-cloud-sdk
```

**Ubuntu/Debian:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Windows:**
```powershell
# Download installer from https://cloud.google.com/sdk/docs/install
# Or use winget:
winget install Google.CloudSDK
```

### 3. GCP Project Setup

```bash
# Login to GCP
gcloud auth login

# Create a new project (or use existing)
gcloud projects create YOUR_PROJECT_ID
gcloud config set project YOUR_PROJECT_ID

# Enable billing via Console: https://console.cloud.google.com/billing
```

### 4. Enable Required APIs

```bash
gcloud services enable \
    aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    storage.googleapis.com \
    run.googleapis.com \
    generativelanguage.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com
```

### 5. Create API Key (for local development)

```bash
# Option A: Create via gcloud
gcloud services api-keys create --display-name="Fund RAG Dev Key"

# Option B: Create via Console
# https://console.cloud.google.com/apis/credentials
# Click "Create Credentials" → "API Key"
```

### 6. Clone and Run

```bash
# Clone the repository
git clone <repo-url>
cd fund-rag-agent

# Create virtual environment with Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY and GCP_PROJECT_ID

# Run the application
uvicorn src.main:app --reload --port 8080
```

The API will be available at http://localhost:8080 with docs at http://localhost:8080/docs.

### 7. Verify Setup

```bash
# Test the API
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is a TFSA?"}'

# Test Gemini API key directly
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

---

## Production Setup (Service Account)

For Cloud Run deployment, create a service account with required permissions:

```bash
# Create service account
gcloud iam service-accounts create fund-rag-agent-sa \
    --display-name="Fund RAG Service Account"

# Grant required roles
PROJECT_ID=$(gcloud config get-value project)

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:fund-rag-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:fund-rag-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/discoveryengine.editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:fund-rag-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

### (Optional) Local Testing with Service Account

```bash
# Download key (keep secure, don't commit!)
gcloud iam service-accounts keys create ./key.json \
    --iam-account=fund-rag-agent-sa@$PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="./key.json"
```

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

For detailed setup instructions and example configurations, see [SETUP.md](SETUP.md).

### Environment Variables (`.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `ENVIRONMENT` | `dev`, `workstation`, or `prod` | Yes |
| `GCP_PROJECT_ID` | Your GCP project ID | Yes |
| `GCP_REGION` | GCP region (default: `us-central1`) | No |
| `GOOGLE_API_KEY` | API key for Gemini (dev only) | Dev only |
| `GCS_BUCKET_NAME` | GCS bucket for PDF documents | Yes |
| `VERTEX_SEARCH_DATA_STORE_ID` | Vertex AI Search data store ID | Yes |
| `VERTEX_SEARCH_ENGINE_ID` | Vertex AI Search engine ID | Yes |
| `GEMINI_MODEL` | Gemini model (default: `gemini-2.5-flash`) | No |
| `ALLOW_GENERAL_KNOWLEDGE_FALLBACK` | Allow Gemini to answer from internal knowledge when no docs found (default: `true`) | No |
| `SYNC_PDFS_IN_DEV` | Sync PDFs in dev mode (default: `false`) | No |
| `PDF_BASE_URL` | Base URL for PDF source links | No |

### Authentication

| Environment | Method | Description |
|-------------|--------|-------------|
| `dev` | API Key | Uses `GOOGLE_API_KEY` environment variable |
| `workstation` | Service Account (ADC) | Uses workstation's attached service account |
| `prod` | Service Account (ADC) | Uses Cloud Run's service account |

### Terraform Variables (`terraform.tfvars`)

| Variable | Description | Required |
|----------|-------------|----------|
| `project_id` | Your GCP project ID | Yes |
| `region` | GCP region (default: `us-central1`) | No |
| `data_store_id` | Vertex AI Search data store ID | No |
| `engine_id` | Vertex AI Search engine ID | No |
| `deploy_cloud_run` | Deploy Cloud Run service (default: `false`) | No |
| `build_container` | Build Docker image before deploy (default: `false`) | No |
| `container_image` | Custom container image URL | No |

See [infra/terraform.tfvars.example](infra/terraform.tfvars.example) for example configurations.

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

### Install Terraform

**macOS:**
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Verify installation
terraform --version
```

**Ubuntu/Debian:**
```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

**Windows:**
```powershell
winget install Hashicorp.Terraform
```

### Deploy Infrastructure with Terraform

Terraform can be run from your local machine, Cloud Workstation, or CI/CD - it applies to remote GCP regardless of where it runs.

#### Option A: From Local Machine

**1. Authenticate with GCP:**

```bash
# Login to gcloud (opens browser)
gcloud auth login

# Set Application Default Credentials (required for Terraform)
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Set quota project (required for Discovery Engine API)
gcloud auth application-default set-quota-project YOUR_PROJECT_ID

# Enable Cloud Resource Manager API (required before Terraform can enable other APIs)
gcloud services enable cloudresourcemanager.googleapis.com --project=YOUR_PROJECT_ID
```

#### Option B: From Cloud Workstation (Service Account Only)

Cloud Workstations use an attached service account for authentication. **No API keys or user OAuth required.**

**Prerequisites:**
1. Cloud Workstation configured with a service account that has required IAM roles
2. Service account needs: `roles/aiplatform.user`, `roles/discoveryengine.editor`, `roles/storage.objectAdmin`

**1. Connect to Cloud Workstation:**

```bash
# Via GCP Console (recommended):
# https://console.cloud.google.com/workstations

# Or via gcloud:
gcloud workstations list --project=YOUR_PROJECT_ID --region=YOUR_REGION

gcloud workstations start WORKSTATION_NAME \
  --project=YOUR_PROJECT_ID \
  --region=YOUR_REGION \
  --cluster=CLUSTER_NAME \
  --config=CONFIG_NAME
```

**2. Verify service account authentication:**

The workstation's service account credentials are automatically available via the metadata server:

```bash
# Verify the attached service account
gcloud auth list
# Should show the workstation's service account as active

# Verify project is set
gcloud config get-value project

# If project not set:
gcloud config set project YOUR_PROJECT_ID

# Enable Cloud Resource Manager API (if not already enabled)
gcloud services enable cloudresourcemanager.googleapis.com --project=YOUR_PROJECT_ID
```

**3. Clone and configure:**

```bash
# Clone the repo
git clone <repo-url>
cd fund-rag-agent

# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Important:** No `gcloud auth login` or API keys needed. The service account attached to your Cloud Workstation provides all authentication automatically via Application Default Credentials (ADC).

#### Continue with Terraform (both options)

**Configure Terraform variables:**

```bash
cd infra

# Create terraform.tfvars for local development (no Cloud Run)
cat > terraform.tfvars << EOF
project_id       = "YOUR_PROJECT_ID"
region           = "us-central1"
deploy_cloud_run = false
EOF

# OR for full production deployment (with Cloud Run)
cat > terraform.tfvars << EOF
project_id       = "YOUR_PROJECT_ID"
region           = "us-central1"
deploy_cloud_run = true
build_container  = true  # Builds and pushes Docker image automatically
EOF
```

| Variable | Required | Description |
|----------|----------|-------------|
| `project_id` | Yes | Your GCP project ID |
| `region` | No | GCP region (default: `us-central1`) |
| `deploy_cloud_run` | No | Set `true` to deploy Cloud Run (default: `false`) |
| `build_container` | No | Set `true` to build/push Docker image before deploying (requires Docker) |
| `container_image` | No | Custom container image URL (auto-generated if not set) |

**Run Terraform:**

```bash
# Initialize (downloads providers)
terraform init

# Preview changes
terraform plan

# Apply (creates resources)
terraform apply
```

**Using environment variables instead of tfvars:**

```bash
# Local dev infrastructure only
TF_VAR_project_id=YOUR_PROJECT_ID terraform apply

# Full deployment with container build
TF_VAR_project_id=YOUR_PROJECT_ID \
TF_VAR_deploy_cloud_run=true \
TF_VAR_build_container=true \
terraform apply

# Force rebuild container (when code changes)
terraform apply -replace=null_resource.build_container
```

**View Terraform Outputs:**

After successful deployment, view the created resource IDs:

```bash
# Show all outputs
terraform output

# Get specific values
terraform output cloud_run_url
terraform output gcs_bucket_name
terraform output vertex_search_data_store_id
terraform output vertex_search_engine_id
terraform output service_account_email
```

| Output | Description |
|--------|-------------|
| `cloud_run_url` | URL of deployed Cloud Run service |
| `gcs_bucket_name` | GCS bucket name for PDF documents |
| `vertex_search_data_store_id` | Vertex AI Search data store ID |
| `vertex_search_engine_id` | Vertex AI Search engine ID |
| `service_account_email` | Service account used by Cloud Run |

Use these values to populate your local `.env` file for development. See [SETUP.md](SETUP.md) for detailed instructions.

### Scripts

Helper scripts are available in the `scripts/` directory. See [scripts/README.md](scripts/README.md) for detailed documentation.

| Script | Purpose |
|--------|---------|
| `local_dev.sh` | Start local development server |
| `docker_test.sh` | Build and test Docker image |
| `generate_env.sh` | Generate .env from Terraform outputs |
| `deploy.sh` | Full production deployment |
| `import_docs.sh` | Trigger PDF import to Vertex AI Search |
| `terraform_destroy.sh` | Tear down infrastructure |

```bash
# After terraform apply - generate .env from outputs
./scripts/generate_env.sh

# Start local development server
./scripts/local_dev.sh

# Build and test Docker image
./scripts/docker_test.sh all

# Full deployment (build, push, terraform apply)
./scripts/deploy.sh

# Trigger document import
./scripts/import_docs.sh

# Destroy Cloud Run only (keeps data)
./scripts/terraform_destroy.sh

# Destroy ALL infrastructure (requires confirmation)
./scripts/terraform_destroy.sh --all
```

### Troubleshooting Terraform

| Error | Solution |
|-------|----------|
| `invalid_grant` / `invalid_rapt` | Re-run `gcloud auth login` and `gcloud auth application-default login` |
| `requires a quota project` | Run `gcloud auth application-default set-quota-project YOUR_PROJECT_ID` |
| `Cloud Resource Manager API has not been used` | Run `gcloud services enable cloudresourcemanager.googleapis.com --project=YOUR_PROJECT_ID` |
| `Permission denied` | Check IAM roles, re-authenticate |
| `Resource already exists` | Run `terraform import` or delete manually |
| `API not enabled` | Terraform enables APIs automatically, wait and retry |

## Development

### Cloud Workstation Quick Start

Complete workflow for developing and testing in Cloud Workstation (service account auth only, no API keys):

```bash
# 1. Connect to Cloud Workstation via GCP Console
#    https://console.cloud.google.com/workstations

# 2. Verify service account is active
gcloud auth list
gcloud config set project YOUR_PROJECT_ID

# 3. Clone and setup
git clone <repo-url>
cd fund-rag-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Deploy infrastructure (first time only)
cd infra
cat > terraform.tfvars << EOF
project_id       = "YOUR_PROJECT_ID"
region           = "us-central1"
deploy_cloud_run = false
EOF
terraform init
terraform apply
cd ..

# 5. Generate .env from Terraform outputs
./scripts/generate_env.sh

# 6. Update .env for workstation
sed -i 's/ENVIRONMENT=dev/ENVIRONMENT=workstation/' .env

# 7. Test the server (choose one):

# Option A: Run directly (fastest for development)
uvicorn src.main:app --reload --port 8080

# Option B: Test Docker image (validates prod deployment)
./scripts/docker_test.sh all
```

### Testing Docker in Cloud Workstation

```bash
# Build and test Docker image
./scripts/docker_test.sh all

# Or step by step:
./scripts/docker_test.sh build    # Build image
./scripts/docker_test.sh run      # Start container
./scripts/docker_test.sh test     # Test API endpoints
./scripts/docker_test.sh logs     # View container logs
./scripts/docker_test.sh clean    # Stop and remove container
```

The script automatically mounts service account credentials into the container.

### Key Patterns

- **Dev/Workstation/Prod Auth**: Dev uses API key, workstation/prod use service account via ADC
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
