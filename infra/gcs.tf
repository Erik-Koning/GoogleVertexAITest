# GCS bucket for PDF documents
resource "google_storage_bucket" "documents" {
  name     = "${var.project_id}-fund-documents"
  location = var.region

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    purpose     = "fund-rag-documents"
  }

  depends_on = [google_project_service.apis]
}

# Grant service account access to bucket
resource "google_storage_bucket_iam_member" "api_bucket_access" {
  bucket = google_storage_bucket.documents.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.api.email}"
}
