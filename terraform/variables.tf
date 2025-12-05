variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone for resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "save-sabi"
}

# Cloud SQL Variables
variable "cloudsql_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "cloudsql_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 10
}

variable "cloudsql_deletion_protection" {
  description = "Enable deletion protection for Cloud SQL"
  type        = bool
  default     = false
}

variable "cloudsql_availability_type" {
  description = "Cloud SQL availability type (ZONAL or REGIONAL)"
  type        = string
  default     = "ZONAL"
}

# Cloud Run Configuration
variable "backend_image" {
  description = "Docker image for backend (e.g., gcr.io/project/image:tag)"
  type        = string
  default     = "gcr.io/cloudrun/hello"  # Placeholder, will be updated during deployment
}

variable "cloudrun_cpu" {
  description = "CPU limit for Cloud Run"
  type        = string
  default     = "1000m"
}

variable "cloudrun_memory" {
  description = "Memory limit for Cloud Run"
  type        = string
  default     = "512Mi"
}

variable "cloudrun_min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = string
  default     = "0"
}

variable "cloudrun_max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = string
  default     = "10"
}

# Frontend Configuration
variable "frontend_url" {
  description = "Frontend URL for CORS configuration"
  type        = string
  default     = "http://localhost:5173"
}
