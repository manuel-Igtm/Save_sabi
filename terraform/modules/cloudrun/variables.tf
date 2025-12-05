# Cloud Run Module Variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run service"
  type        = string
  default     = "us-central1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "container_image" {
  description = "Docker container image URL (e.g., gcr.io/project/image:tag)"
  type        = string
}

variable "cpu_limit" {
  description = "CPU limit for container"
  type        = string
  default     = "1000m"
}

variable "memory_limit" {
  description = "Memory limit for container"
  type        = string
  default     = "512Mi"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = string
  default     = "0"
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = string
  default     = "10"
}

variable "debug" {
  description = "Enable Django DEBUG mode"
  type        = bool
  default     = false
}

variable "custom_domain" {
  description = "Custom domain for the service"
  type        = string
  default     = ""
}

variable "gcs_bucket_name" {
  description = "GCS bucket name for static/media files"
  type        = string
}

variable "cors_allowed_origins" {
  description = "CORS allowed origins"
  type        = string
  default     = ""
}

variable "csrf_trusted_origins" {
  description = "CSRF trusted origins"
  type        = string
  default     = ""
}

variable "django_secret_id" {
  description = "Secret Manager secret ID for Django secret key"
  type        = string
}

variable "database_url_secret_id" {
  description = "Secret Manager secret ID for database URL"
  type        = string
}

variable "cloudsql_connection" {
  description = "Cloud SQL connection name"
  type        = string
  default     = ""
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the service"
  type        = bool
  default     = true
}
