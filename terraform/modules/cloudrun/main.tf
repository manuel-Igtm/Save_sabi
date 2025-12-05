# Cloud Run Service for Django Backend

resource "google_cloud_run_service" "backend" {
  name     = "${var.project_name}-${var.environment}-api"
  location = var.region
  project  = var.project_id

  template {
    spec {
      service_account_name = google_service_account.cloudrun_sa.email
      
      containers {
        image = var.container_image

        # Resource limits
        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
        }

        # Environment variables
        env {
          name  = "DEBUG"
          value = var.debug ? "True" : "False"
        }

        env {
          name  = "ALLOWED_HOSTS"
          value = ".run.app,${var.custom_domain}"
        }

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }

        env {
          name  = "GCS_BUCKET_NAME"
          value = var.gcs_bucket_name
        }

        env {
          name  = "CORS_ALLOWED_ORIGINS"
          value = var.cors_allowed_origins
        }

        env {
          name  = "CSRF_TRUSTED_ORIGINS"
          value = var.csrf_trusted_origins
        }

        # Secrets from Secret Manager
        env {
          name = "DJANGO_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = var.django_secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = var.database_url_secret_id
              key  = "latest"
            }
          }
        }

        # Health check
        ports {
          container_port = 8000
        }

        # Startup probe
        startup_probe {
          http_get {
            path = "/healthz"
            port = 8000
          }
          initial_delay_seconds = 10
          timeout_seconds       = 5
          period_seconds        = 10
          failure_threshold     = 3
        }

        # Liveness probe
        liveness_probe {
          http_get {
            path = "/healthz"
            port = 8000
          }
          initial_delay_seconds = 30
          timeout_seconds       = 5
          period_seconds        = 30
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"      = var.min_instances
        "autoscaling.knative.dev/maxScale"      = var.max_instances
        "run.googleapis.com/cloudsql-instances" = var.cloudsql_connection
        "run.googleapis.com/client-name"        = "terraform"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}

# Service Account for Cloud Run
resource "google_service_account" "cloudrun_sa" {
  account_id   = "${var.project_name}-${var.environment}-run-sa"
  display_name = "Cloud Run Service Account for ${var.project_name}"
  project      = var.project_id
}

# IAM binding for Cloud SQL Client
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# IAM binding for Secret Manager access
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# IAM binding for Storage access
resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Allow unauthenticated access (for public API)
resource "google_cloud_run_service_iam_member" "public_access" {
  count    = var.allow_unauthenticated ? 1 : 0
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
