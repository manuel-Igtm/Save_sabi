output "django_secret_key_id" {
  description = "Secret Manager secret ID for Django secret key"
  value       = google_secret_manager_secret.django_secret_key.secret_id
}

output "database_url_id" {
  description = "Secret Manager secret ID for database URL"
  value       = google_secret_manager_secret.database_url.secret_id
}

output "gcs_bucket_name_id" {
  description = "Secret Manager secret ID for GCS bucket name"
  value       = google_secret_manager_secret.gcs_bucket_name.secret_id
}
