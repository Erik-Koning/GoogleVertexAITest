#!/bin/bash
# Test Docker image locally or in Cloud Workstation
# Usage: ./scripts/docker_test.sh [build|run|test|clean|all]

set -e

cd "$(dirname "$0")/.."

# Configuration
IMAGE_NAME="fund-rag-agent"
IMAGE_TAG="test"
CONTAINER_NAME="fund-rag-agent-test"
PORT=8080

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running in Cloud Workstation
is_cloud_workstation() {
    # Cloud Workstations have specific metadata
    if curl -s -f -H "Metadata-Flavor: Google" \
        "http://metadata.google.internal/computeMetadata/v1/instance/attributes/workstation-id" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Get project ID from gcloud
get_project_id() {
    gcloud config get-value project 2>/dev/null || echo ""
}

# Build Docker image
build_image() {
    log_info "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"

    # Ensure pdfs directory exists (even if empty)
    mkdir -p pdfs

    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

    log_info "Build complete!"
}

# Run Docker container
run_container() {
    log_info "Starting Docker container..."

    # Stop existing container if running
    docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

    # Get project ID
    PROJECT_ID=$(get_project_id)
    if [ -z "$PROJECT_ID" ]; then
        log_error "GCP project not set. Run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi

    # Check for .env file
    if [ ! -f ".env" ]; then
        log_error ".env file not found. Create one with required configuration."
        log_info "Required variables: GCP_PROJECT_ID, FAISS_INDEX_PATH"
        exit 1
    fi

    # Determine credential mounting strategy
    ADC_PATH=""
    CRED_MOUNT=""
    CRED_ENV=""

    # Check for ADC credentials file
    if [ -f "${HOME}/.config/gcloud/application_default_credentials.json" ]; then
        ADC_PATH="${HOME}/.config/gcloud/application_default_credentials.json"
        log_info "Using ADC credentials from: ${ADC_PATH}"
    fi

    # Check for service account key file
    if [ -f "./key.json" ]; then
        ADC_PATH="$(pwd)/key.json"
        log_info "Using service account key: ${ADC_PATH}"
    fi

    if [ -n "$ADC_PATH" ]; then
        CRED_MOUNT="-v ${ADC_PATH}:/app/credentials.json:ro"
        CRED_ENV="-e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json"
    else
        if is_cloud_workstation; then
            log_warn "No credentials file found. In Cloud Workstation, you may need to run:"
            log_warn "  gcloud auth application-default login --no-launch-browser"
            log_warn "Or create a service account key for testing."
        else
            log_warn "No credentials file found. Container may not be able to authenticate."
        fi
    fi

    # Run the container
    log_info "Running container on port ${PORT}..."

    docker run -d \
        --name "${CONTAINER_NAME}" \
        -p "${PORT}:8080" \
        --env-file .env \
        -e ENVIRONMENT=prod \
        -e GCP_PROJECT_ID="${PROJECT_ID}" \
        ${CRED_MOUNT} \
        ${CRED_ENV} \
        "${IMAGE_NAME}:${IMAGE_TAG}"

    log_info "Container started! Waiting for health check..."

    # Wait for container to be healthy
    for i in {1..30}; do
        if curl -s -f "http://localhost:${PORT}/health" > /dev/null 2>&1; then
            log_info "Container is healthy!"
            echo ""
            log_info "API available at: http://localhost:${PORT}"
            log_info "API docs at: http://localhost:${PORT}/docs"
            echo ""
            log_info "Test with:"
            echo "  curl -X POST http://localhost:${PORT}/chat \\"
            echo "    -H 'Content-Type: application/json' \\"
            echo "    -d '{\"message\": \"What is a TFSA?\"}'"
            echo ""
            log_info "View logs: docker logs -f ${CONTAINER_NAME}"
            log_info "Stop container: docker stop ${CONTAINER_NAME}"
            return 0
        fi
        sleep 1
    done

    log_error "Container failed to become healthy. Check logs:"
    docker logs "${CONTAINER_NAME}"
    exit 1
}

# Test the running container
test_container() {
    log_info "Testing container API..."

    # Health check
    log_info "Testing /health endpoint..."
    if curl -s -f "http://localhost:${PORT}/health" | grep -q "healthy"; then
        log_info "Health check: PASSED"
    else
        log_error "Health check: FAILED"
        exit 1
    fi

    # Root endpoint
    log_info "Testing / endpoint..."
    if curl -s -f "http://localhost:${PORT}/" | grep -q "Fund RAG Agent"; then
        log_info "Root endpoint: PASSED"
    else
        log_error "Root endpoint: FAILED"
        exit 1
    fi

    # Chat endpoint
    log_info "Testing /chat endpoint..."
    RESPONSE=$(curl -s -X POST "http://localhost:${PORT}/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "What is a TFSA?"}')

    if echo "$RESPONSE" | grep -q "reply"; then
        log_info "Chat endpoint: PASSED"
        echo ""
        log_info "Response preview:"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    else
        log_error "Chat endpoint: FAILED"
        log_error "Response: $RESPONSE"
        exit 1
    fi

    echo ""
    log_info "All tests passed!"
}

# Clean up
clean() {
    log_info "Cleaning up..."
    docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    docker rm "${CONTAINER_NAME}" 2>/dev/null || true
    log_info "Container removed."

    read -p "Also remove Docker image? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker rmi "${IMAGE_NAME}:${IMAGE_TAG}" 2>/dev/null || true
        log_info "Image removed."
    fi
}

# Show logs
logs() {
    docker logs -f "${CONTAINER_NAME}"
}

# Print usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build    Build the Docker image"
    echo "  run      Run the Docker container"
    echo "  test     Test the running container's API"
    echo "  logs     Show container logs (follow mode)"
    echo "  clean    Stop and remove container (optionally image)"
    echo "  all      Build, run, and test (default)"
    echo ""
    echo "Examples:"
    echo "  $0 build          # Build image only"
    echo "  $0 run            # Run container (must build first)"
    echo "  $0 all            # Build, run, and test"
    echo "  $0 clean          # Clean up"
}

# Main
case "${1:-all}" in
    build)
        build_image
        ;;
    run)
        run_container
        ;;
    test)
        test_container
        ;;
    logs)
        logs
        ;;
    clean)
        clean
        ;;
    all)
        build_image
        run_container
        sleep 2
        test_container
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        log_error "Unknown command: $1"
        usage
        exit 1
        ;;
esac
