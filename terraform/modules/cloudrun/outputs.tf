# Cloud Run Module Outputs

output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.backend.status[0].url
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_service.backend.name
}

output "service_location" {
  description = "Location of the Cloud Run service"
  value       = google_cloud_run_service.backend.location
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Run"
  value       = google_service_account.cloudrun_sa.email
}

output "latest_revision" {
  description = "Latest revision name"
  value       = google_cloud_run_service.backend.status[0].latest_ready_revision_name
}
