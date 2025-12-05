# Django Secret Key
resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "${var.project_name}-${var.environment}-django-secret-key"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

resource "google_secret_manager_secret_version" "django_secret_key_version" {
  secret      = google_secret_manager_secret.django_secret_key.id
  secret_data = var.django_secret_key
}

# Database URL
resource "google_secret_manager_secret" "database_url" {
  secret_id = "${var.project_name}-${var.environment}-database-url"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

resource "google_secret_manager_secret_version" "database_url_version" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = var.database_url
}

# GCS Bucket Name
resource "google_secret_manager_secret" "gcs_bucket_name" {
  secret_id = "${var.project_name}-${var.environment}-gcs-bucket-name"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

resource "google_secret_manager_secret_version" "gcs_bucket_name_version" {
  secret      = google_secret_manager_secret.gcs_bucket_name.id
  secret_data = var.gcs_bucket_name
}
