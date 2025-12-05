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

variable "subnet_cidr" {
  description = "CIDR range for the subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "pods_cidr" {
  description = "CIDR range for pods (GKE)"
  type        = string
  default     = "10.1.0.0/16"
}

variable "services_cidr" {
  description = "CIDR range for services (GKE)"
  type        = string
  default     = "10.2.0.0/16"
}

variable "ssh_source_ranges" {
  description = "Source IP ranges allowed for SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
