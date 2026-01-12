#!/bin/bash
# Full deployment script for Fund RAG Agent

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="fund-rag-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check required environment variables
if [ -z "$PROJECT_ID" ]; then
    log_error "GCP_PROJECT_ID is not set"
    exit 1
fi

log_info "Deploying to project: ${PROJECT_ID}"
log_info "Region: ${REGION}"

# Set project
gcloud config set project "${PROJECT_ID}"

# Build and push container
log_info "Building container image..."
docker build -t "${IMAGE_NAME}:latest" .

log_info "Pushing container image..."
docker push "${IMAGE_NAME}:latest"

# Deploy infrastructure with Terraform
log_info "Deploying infrastructure..."
cd infra

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    terraform init
fi

# Apply Terraform
terraform apply \
    -var="project_id=${PROJECT_ID}" \
    -var="region=${REGION}" \
    -var="container_image=${IMAGE_NAME}:latest" \
    -auto-approve

# Get outputs
CLOUD_RUN_URL=$(terraform output -raw cloud_run_url)

cd ..

log_info "Deployment complete!"
log_info "Cloud Run URL: ${CLOUD_RUN_URL}"
log_info ""
log_info "Test the API:"
log_info "  curl -X POST ${CLOUD_RUN_URL}/chat -H 'Content-Type: application/json' -d '{\"message\": \"What is a TFSA?\"}'"
