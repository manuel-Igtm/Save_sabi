output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "The GCP region"
  value       = var.region
}

output "vpc_network_name" {
  description = "The name of the VPC network"
  value       = module.networking.vpc_network_name
}

output "vpc_network_id" {
  description = "The ID of the VPC network"
  value       = module.networking.vpc_network_id
}

output "subnet_names" {
  description = "The names of the subnets"
  value       = module.networking.subnet_names
}

output "storage_bucket_name" {
  description = "The name of the storage bucket"
  value       = module.storage.bucket_name
}

output "storage_bucket_url" {
  description = "The URL of the storage bucket"
  value       = module.storage.bucket_url
}

# Cloud SQL Outputs
output "cloudsql_instance_name" {
  description = "Cloud SQL instance name"
  value       = module.cloudsql.instance_name
}

output "cloudsql_connection_name" {
  description = "Cloud SQL connection name for Cloud SQL Proxy"
  value       = module.cloudsql.instance_connection_name
}

output "cloudsql_database_name" {
  description = "Database name"
  value       = module.cloudsql.database_name
}

output "cloudsql_database_user" {
  description = "Database user name"
  value       = module.cloudsql.database_user
}

output "cloudsql_ip_address" {
  description = "Cloud SQL instance IP address"
  value       = module.cloudsql.instance_ip_address
}

# Secret Manager Outputs
output "django_secret_key_id" {
  description = "Secret Manager ID for Django secret key"
  value       = module.secrets.django_secret_key_id
}

output "database_url_secret_id" {
  description = "Secret Manager ID for database URL"
  value       = module.secrets.database_url_id
}

output "gcs_bucket_secret_id" {
  description = "Secret Manager ID for GCS bucket name"
  value       = module.secrets.gcs_bucket_name_id
}

