# Cloud Run service
resource "google_cloud_run_v2_service" "api" {
  name     = "fund-rag-agent"
  location = var.region

  template {
    service_account = google_service_account.api.email

    containers {
      image = var.container_image

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
        value = "gemini-1.5-pro"
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
    google_project_service.apis,
    google_storage_bucket.documents,
    google_discovery_engine_search_engine.fund_search,
  ]
}

# Allow unauthenticated access (configure as needed)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.api.location
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
