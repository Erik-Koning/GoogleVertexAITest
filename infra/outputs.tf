output "cloud_run_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.api.uri
}

output "gcs_bucket_name" {
  description = "Name of the GCS bucket for PDF documents"
  value       = google_storage_bucket.documents.name
}

output "vertex_search_data_store_id" {
  description = "ID of the Vertex AI Search data store"
  value       = google_discovery_engine_data_store.fund_docs.data_store_id
}

output "vertex_search_engine_id" {
  description = "ID of the Vertex AI Search engine"
  value       = google_discovery_engine_search_engine.fund_search.engine_id
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Run"
  value       = google_service_account.api.email
}
