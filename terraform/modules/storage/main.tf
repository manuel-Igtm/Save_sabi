# Storage Bucket
resource "google_storage_bucket" "bucket" {
  name          = "${var.project_name}-${var.environment}-${var.bucket_suffix}"
  location      = var.region
  project       = var.project_id
  storage_class = var.storage_class
  
  uniform_bucket_level_access = true

  versioning {
    enabled = var.versioning_enabled
  }

  lifecycle_rule {
    condition {
      age = var.lifecycle_age_days
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# Optional: Bucket IAM binding for public read access (commented out for security)
# resource "google_storage_bucket_iam_member" "public_read" {
#   bucket = google_storage_bucket.bucket.name
#   role   = "roles/storage.objectViewer"
#   member = "allUsers"
# }
