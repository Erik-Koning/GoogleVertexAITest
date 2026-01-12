output "cloud_run_url" {
  description = "URL of the Cloud Run service"
  value       = var.deploy_cloud_run ? google_cloud_run_v2_service.api[0].uri : "Not deployed (deploy_cloud_run=false)"
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Run"
  value       = google_service_account.api.email
}
