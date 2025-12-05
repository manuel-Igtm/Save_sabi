# Save Sabi - Terraform Infrastructure

This repository contains Infrastructure as Code (IaC) for deploying the Save Sabi project to Google Cloud Platform.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.0
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- A GCP project with billing enabled
- Appropriate IAM permissions

## Project Structure

```
terraform/
├── main.tf                    # Main configuration file
├── provider.tf                # Provider configuration
├── variables.tf               # Global variables
├── outputs.tf                 # Global outputs
├── versions.tf                # Terraform and provider versions
├── terraform.tfvars.example   # Example variable values
├── .gitignore                 # Git ignore file
└── modules/
    ├── networking/            # VPC, subnets, firewall rules
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── README.md
    └── storage/               # Cloud Storage buckets
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── README.md
```

## Getting Started

### 1. Configure Variables

Copy the example variables file and update with your values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set your GCP project ID and other variables:

```hcl
project_id   = "your-gcp-project-id"
region       = "us-central1"
zone         = "us-central1-a"
environment  = "dev"
project_name = "save-sabi"
```

### 2. Authenticate with GCP

```bash
gcloud auth application-default login
```

### 3. Initialize Terraform

```bash
cd terraform
terraform init
```

### 4. Review the Plan

```bash
terraform plan
```

### 5. Apply the Configuration

```bash
terraform apply
```

## Modules

### Networking Module

Creates:
- VPC network
- Subnet with secondary IP ranges for GKE
- Firewall rules (internal, SSH, HTTP/HTTPS)

See [modules/networking/README.md](modules/networking/README.md) for details.

### Storage Module

Creates:
- Cloud Storage bucket with versioning
- Lifecycle rules for automatic deletion
- Uniform bucket-level access

See [modules/storage/README.md](modules/storage/README.md) for details.

## Remote State (Optional)

To use remote state storage in GCS, uncomment the backend configuration in `main.tf`:

```hcl
terraform {
  backend "gcs" {
    bucket = "your-terraform-state-bucket"
    prefix = "terraform/state"
  }
}
```

Create the state bucket first:

```bash
gsutil mb gs://your-terraform-state-bucket
gsutil versioning set on gs://your-terraform-state-bucket
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

## Security Notes

- `terraform.tfvars` is gitignored to prevent committing sensitive data
- Review firewall rules before deploying to production
- Consider restricting SSH access to specific IP ranges
- Enable VPC Flow Logs for production environments

## Adding More Modules

To add additional modules (e.g., compute, database):

1. Create a new directory under `modules/`
2. Add `main.tf`, `variables.tf`, and `outputs.tf`
3. Reference the module in the root `main.tf`
4. Update `outputs.tf` to expose module outputs

Example:

```hcl
module "compute" {
  source = "./modules/compute"
  
  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  project_name = var.project_name
}
```
