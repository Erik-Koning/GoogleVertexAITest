#!/bin/bash
# Terraform destroy script with proper resource ordering
# Handles Vertex AI Search engine/data store dependency
#
# Usage:
#   ./terraform_destroy.sh          # Destroy Cloud Run only (safe, keeps data)
#   ./terraform_destroy.sh --all    # Destroy everything including data

set -e

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

DESTROY_ALL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            DESTROY_ALL=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --all     Destroy ALL resources including data (GCS bucket, Vertex AI data store)"
            echo "  -h        Show this help message"
            echo ""
            echo "Without --all, only destroys Cloud Run (keeps your indexed PDFs and bucket)"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Change to infra directory
cd "$(dirname "$0")/../infra"

# Check if terraform is initialized
if [ ! -d ".terraform" ]; then
    log_error "Terraform not initialized. Run 'terraform init' first."
    exit 1
fi

log_info "Starting Terraform destroy sequence..."

if [ "$DESTROY_ALL" = true ]; then
    log_warn "⚠️  DESTROYING ALL RESOURCES including data!"
    log_warn "This will delete:"
    log_warn "  - GCS bucket (uploaded PDFs)"
    log_warn "  - Vertex AI Search data store (indexed documents)"
    echo ""
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Aborted."
        exit 0
    fi
fi

# Step 1: Destroy Cloud Run (if exists)
log_info "Step 1: Destroying Cloud Run service..."
terraform destroy \
    -target=google_cloud_run_v2_service_iam_member.public_access \
    -target=google_cloud_run_v2_service.api \
    -auto-approve 2>/dev/null || log_warn "Cloud Run resources not found or already destroyed"

if [ "$DESTROY_ALL" = true ]; then
    # Step 2: Destroy Search Engine (must be before data store)
    log_info "Step 2: Destroying Vertex AI Search Engine..."
    terraform destroy \
        -target=google_discovery_engine_search_engine.fund_search \
        -auto-approve 2>/dev/null || log_warn "Search engine not found or already destroyed"

    # Wait for engine deletion to propagate
    log_info "Waiting for engine deletion to propagate..."
    sleep 10

    # Step 3: Destroy Data Store
    log_info "Step 3: Destroying Vertex AI Search Data Store..."
    terraform destroy \
        -target=google_discovery_engine_data_store.fund_docs \
        -auto-approve 2>/dev/null || log_warn "Data store not found or already destroyed"

    # Step 4: Destroy remaining resources (GCS, IAM, etc.)
    log_info "Step 4: Destroying remaining resources..."
    terraform destroy -auto-approve

    log_info "✅ Full destroy complete - all resources removed!"
else
    log_info "✅ Cloud Run destroyed. Data resources preserved."
    log_info ""
    log_info "Kept:"
    log_info "  - GCS bucket (your PDFs)"
    log_info "  - Vertex AI Search data store (indexed documents)"
    log_info "  - Vertex AI Search engine"
    log_info ""
    log_info "To destroy everything: ./terraform_destroy.sh --all"
fi
