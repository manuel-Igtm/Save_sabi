# Cloud SQL Module

This module creates a Cloud SQL PostgreSQL instance for the Save Sabi application.

## Resources Created

- Cloud SQL PostgreSQL 15 instance
- Database
- Database user
- Private IP configuration (optional)

## Usage

```hcl
module "cloudsql" {
  source = "./modules/cloudsql"
  
  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  project_name = var.project_name
}
```

## Outputs

- `instance_connection_name`: Connection name for Cloud SQL Proxy
- `database_name`: Name of the created database
- `instance_ip_address`: IP address of the instance
