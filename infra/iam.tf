# Service account for Cloud Run
resource "google_service_account" "api" {
  account_id   = "fund-rag-agent-sa"
  display_name = "Fund RAG Agent Service Account"
  description  = "Service account for the Fund RAG Agent Cloud Run service"
}

# Vertex AI User role (for Gemini access)
resource "google_project_iam_member" "api_vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.api.email}"
}
