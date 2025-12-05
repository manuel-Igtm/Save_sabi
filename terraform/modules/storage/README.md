# Storage Module

This module creates:
- Google Cloud Storage bucket with versioning
- Lifecycle rules for automatic deletion
- Uniform bucket-level access

## Usage

```hcl
module "storage" {
  source = "./modules/storage"

  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  project_name = var.project_name
}
```

## Inputs

| Name | Description | Type | Default |
|------|-------------|------|---------|
| project_id | The GCP project ID | string | - |
| region | The GCP region | string | - |
| environment | Environment name | string | - |
| project_name | Name of the project | string | - |
| bucket_suffix | Suffix for the bucket name | string | "data" |
| storage_class | Storage class for the bucket | string | "STANDARD" |
| versioning_enabled | Enable versioning for the bucket | bool | true |
| lifecycle_age_days | Age in days for lifecycle deletion | number | 365 |

## Outputs

| Name | Description |
|------|-------------|
| bucket_name | The name of the storage bucket |
| bucket_url | The URL of the storage bucket |
| bucket_self_link | The self-link of the storage bucket |
