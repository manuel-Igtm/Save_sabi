# Backend configuration (uncomment and configure for remote state)
# terraform {
#   backend "gcs" {
#     bucket = "your-terraform-state-bucket"
#     prefix = "terraform/state"
#   }
# }

# Generate Django secret key
resource "random_password" "django_secret_key" {
  length  = 50
  special = true
}

# Networking Module
module "networking" {
  source = "./modules/networking"

  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  project_name = var.project_name
}

# Storage Module
module "storage" {
  source = "./modules/storage"

  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  project_name = var.project_name
}

# Cloud SQL Module
module "cloudsql" {
  source = "./modules/cloudsql"

  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  project_name = var.project_name
  
  database_version     = "POSTGRES_15"
  tier                 = var.cloudsql_tier
  disk_size            = var.cloudsql_disk_size
  deletion_protection  = var.cloudsql_deletion_protection
  availability_type    = var.cloudsql_availability_type
}

# Secret Manager Module
module "secrets" {
  source = "./modules/secrets"

  project_id   = var.project_id
  environment  = var.environment
  project_name = var.project_name

  django_secret_key = random_password.django_secret_key.result
  database_url      = module.cloudsql.database_url
  gcs_bucket_name   = module.storage.bucket_name
}

# Cloud Run Module (Backend API)
module "cloudrun" {
  source = "./modules/cloudrun"

  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  project_name = var.project_name

  # Container image (will be built and pushed separately)
  container_image = var.backend_image

  # Resource limits
  cpu_limit    = var.cloudrun_cpu
  memory_limit = var.cloudrun_memory
  min_instances = var.cloudrun_min_instances
  max_instances = var.cloudrun_max_instances

  # Application configuration
  debug               = var.environment == "dev" ? true : false
  gcs_bucket_name     = module.storage.bucket_name
  cors_allowed_origins = var.frontend_url
  csrf_trusted_origins = var.frontend_url

  # Secrets
  django_secret_id        = module.secrets.django_secret_key_id
  database_url_secret_id  = module.secrets.database_url_id

  # Cloud SQL
  cloudsql_connection = module.cloudsql.instance_connection_name

  # Public access
  allow_unauthenticated = true

  depends_on = [module.secrets, module.cloudsql]
}
