# Default container image if not specified
locals {
  container_image = var.container_image != "" ? var.container_image : "gcr.io/${var.project_id}/fund-rag-agent:latest"
}

# Build and push container image (only when build_container = true)
resource "null_resource" "build_container" {
  count = var.build_container && var.deploy_cloud_run ? 1 : 0

  triggers = {
    # Rebuild when these files change
    dockerfile = filemd5("${path.module}/../Dockerfile")
    # Force rebuild with: terraform apply -replace=null_resource.build_container
  }

  provisioner "local-exec" {
    working_dir = "${path.module}/.."
    command     = <<-EOT
      echo "Configuring Docker for GCR..."
      gcloud auth configure-docker --quiet

      echo "Building container image..."
      docker build -t ${local.container_image} .

      echo "Pushing container image..."
      docker push ${local.container_image}

      echo "Container build and push complete!"
    EOT
  }
}

# Cloud Run service (only deployed when deploy_cloud_run = true)
resource "google_cloud_run_v2_service" "api" {
  count    = var.deploy_cloud_run ? 1 : 0
  name     = "fund-rag-agent"
  location = var.region

  template {
    service_account = google_service_account.api.email

    containers {
      image = local.container_image

      ports {
        container_port = 8080
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCP_REGION"
        value = var.region
      }

      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.documents.name
      }

      env {
        name  = "VERTEX_SEARCH_DATA_STORE_ID"
        value = google_discovery_engine_data_store.fund_docs.data_store_id
      }

      env {
        name  = "VERTEX_SEARCH_ENGINE_ID"
        value = google_discovery_engine_search_engine.fund_search.engine_id
      }

      env {
        name  = "GEMINI_MODEL"
        value = var.gemini_model
      }

      env {
        name  = "PDF_BASE_URL"
        value = var.pdf_base_url
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 10
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
        }
        period_seconds = 30
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    null_resource.build_container,
    google_project_service.apis,
    google_storage_bucket.documents,
    google_discovery_engine_search_engine.fund_search,
  ]
}

# Allow unauthenticated access (configure as needed)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count    = var.deploy_cloud_run ? 1 : 0
  location = google_cloud_run_v2_service.api[0].location
  name     = google_cloud_run_v2_service.api[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
