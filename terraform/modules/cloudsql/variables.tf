variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "database_version" {
  description = "PostgreSQL database version"
  type        = string
  default     = "POSTGRES_15"
}

variable "tier" {
  description = "The machine tier for the instance"
  type        = string
  default     = "db-f1-micro"
}

variable "disk_size" {
  description = "Disk size in GB"
  type        = number
  default     = 10
}

variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = "savesabi"
}

variable "database_user" {
  description = "Database user name"
  type        = string
  default     = "savesabi"
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = false
}

variable "backup_enabled" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "availability_type" {
  description = "Availability type (ZONAL or REGIONAL)"
  type        = string
  default     = "ZONAL"
}
