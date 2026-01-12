# Scripts

Helper scripts for development, deployment, and infrastructure management.

## Quick Reference

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `local_dev.sh` | Start local dev server | Daily development |
| `docker_test.sh` | Build and test Docker image | Testing container locally or in Cloud Workstation |
| `deploy.sh` | Full production deployment | Deploying to Cloud Run |
| `import_docs.sh` | Trigger PDF import to Vertex AI | After adding new PDFs |
| `terraform_destroy.sh` | Tear down infrastructure | Cleaning up resources |
| `generate_env.sh` | Generate .env from Terraform | After terraform apply |

---

## docker_test.sh

Build and test the Docker image locally or in Cloud Workstation.

```bash
./scripts/docker_test.sh [command]
```

### Commands

| Command | Description |
|---------|-------------|
| `build` | Build the Docker image |
| `run` | Run the Docker container |
| `test` | Test the running container's API |
| `logs` | Show container logs (follow mode) |
| `clean` | Stop and remove container |
| `all` | Build, run, and test (default) |

### Usage Examples

```bash
# Build, run, and test (recommended)
./scripts/docker_test.sh all

# Or just:
./scripts/docker_test.sh

# Build only
./scripts/docker_test.sh build

# Run after building
./scripts/docker_test.sh run

# Test running container
./scripts/docker_test.sh test

# View logs
./scripts/docker_test.sh logs

# Clean up
./scripts/docker_test.sh clean
```

### Cloud Workstation Usage

In Cloud Workstation, credentials are handled automatically via the attached service account:

```bash
# 1. Ensure .env is configured
cat .env  # Should have GCP_PROJECT_ID, bucket, data store IDs

# 2. Build and test
./scripts/docker_test.sh all
```

The script automatically:
- Detects Cloud Workstation environment
- Mounts ADC credentials into the container
- Sets `ENVIRONMENT=prod` for service account auth

### Credential Mounting

The script looks for credentials in this order:
1. `./key.json` - Service account key file (if present)
2. `~/.config/gcloud/application_default_credentials.json` - ADC credentials

If no credentials are found, the script warns you but continues (useful for testing health endpoints).

### Prerequisites

- Docker installed and running
- `.env` file configured with required variables
- GCP credentials (ADC or service account key)

---

## local_dev.sh

Sets up and runs the local development environment.

```bash
./scripts/local_dev.sh
```

**What it does:**
1. Creates `.env` from `.env.example` if not exists
2. Creates Python virtual environment if not exists
3. Installs dependencies from `requirements.txt`
4. Starts uvicorn server on `http://localhost:8080`

**Prerequisites:**
- Python 3.11+ installed
- `.env` file configured (see [SETUP.md](../SETUP.md))

---

## deploy.sh

Full production deployment to Cloud Run.

```bash
./scripts/deploy.sh
```

**What it does:**
1. Builds Docker container
2. Pushes to Google Container Registry
3. Runs `terraform apply` to deploy infrastructure
4. Outputs the Cloud Run URL

**Prerequisites:**
- Docker installed and running
- GCP authentication configured
- `infra/terraform.tfvars` configured

**Environment Variables:**
- `GCP_PROJECT_ID` - Your GCP project ID
- `GCP_REGION` - Target region (default: `us-central1`)

---

## import_docs.sh

Triggers Vertex AI Search to import/re-import PDFs from GCS.

```bash
./scripts/import_docs.sh
```

**What it does:**
1. Connects to your Vertex AI Search data store
2. Triggers incremental import from GCS bucket
3. Indexes new/updated PDF documents

**When to use:**
- After uploading new PDFs to GCS
- After modifying existing PDFs
- To refresh the search index

**Prerequisites:**
- GCS bucket exists with PDFs uploaded
- Vertex AI Search data store created

**Environment Variables:**
- `GCP_PROJECT_ID` - Your GCP project ID (required)
- `VERTEX_SEARCH_DATA_STORE_ID` - Data store ID (default: `fund-knowledge-base`)
- `GCS_BUCKET_NAME` - Bucket name (default: `{project}-fund-documents`)

---

## terraform_destroy.sh

Tears down Terraform-managed infrastructure with proper ordering.

### Safe Mode (Default)

```bash
./scripts/terraform_destroy.sh
```

**Destroys:**
- Cloud Run service

**Preserves:**
- GCS bucket (your PDFs)
- Vertex AI Search data store (indexed documents)
- Vertex AI Search engine

Use this when you want to redeploy Cloud Run without losing your indexed data.

### Full Destroy

```bash
./scripts/terraform_destroy.sh --all
```

**Destroys everything:**
- Cloud Run service
- Vertex AI Search engine
- Vertex AI Search data store (⚠️ indexed documents lost)
- GCS bucket (⚠️ uploaded PDFs lost)
- Service accounts and IAM bindings

Requires confirmation. Use this for complete cleanup.

### Options

| Flag | Description |
|------|-------------|
| (none) | Safe mode - keeps data resources |
| `--all` | Destroy everything (asks for confirmation) |
| `-h, --help` | Show help message |

### Why This Script Exists

Vertex AI Search has dependencies that require specific deletion order:
1. Search Engine must be deleted before Data Store
2. Data Store deletion fails if Engine still references it

This script handles the ordering automatically.

---

## generate_env.sh

Generates `.env` file from Terraform outputs - eliminates duplicate configuration.

```bash
./scripts/generate_env.sh
```

**What it does:**
1. Reads terraform outputs (data store ID, engine ID, bucket name)
2. Generates `.env` file with correct values
3. Preserves existing `GOOGLE_API_KEY` if present
4. Backs up existing `.env` to `.env.backup`

**When to use:**
- After `terraform apply` to sync your local environment
- When Terraform resource IDs change
- Setting up a new development machine

**Workflow:**
```bash
# 1. Deploy infrastructure
cd infra && terraform apply

# 2. Generate .env from terraform outputs
./scripts/generate_env.sh

# 3. Add your API key (if not already set)
# Edit .env and add GOOGLE_API_KEY

# 4. Start development
./scripts/local_dev.sh
```

This eliminates the need to manually copy IDs between `terraform.tfvars` and `.env`.

---

## Making Scripts Executable

If you get "permission denied" errors:

```bash
chmod +x scripts/*.sh
```

---

## Adding New Scripts

When adding new scripts:
1. Add to `scripts/` directory
2. Make executable: `chmod +x scripts/your_script.sh`
3. Document in this README
4. Add shebang: `#!/bin/bash`
5. Use `set -e` to exit on errors
