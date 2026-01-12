variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "container_image" {
  description = "Container image for Cloud Run"
  type        = string
}

variable "vertex_search_location" {
  description = "Location for Vertex AI Search (global or regional)"
  type        = string
  default     = "global"
}

variable "pdf_base_url" {
  description = "Base URL for PDF source documents"
  type        = string
  default     = ""
}
