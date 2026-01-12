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
  default     = ""
}

variable "deploy_cloud_run" {
  description = "Whether to deploy Cloud Run service (set false for local dev infrastructure only)"
  type        = bool
  default     = false
}

variable "build_container" {
  description = "Build and push container image before deploying (requires Docker)"
  type        = bool
  default     = false
}

variable "faiss_index_path" {
  description = "Path to the FAISS index directory"
  type        = string
  default     = "./faiss_index"
}

variable "pdf_base_url" {
  description = "Base URL for PDF source documents"
  type        = string
  default     = ""
}

variable "gemini_model" {
  description = "Gemini model version"
  type        = string
  default     = "gemini-2.5-flash"
}
