# Networking Module

This module creates:
- VPC Network
- Subnet with secondary IP ranges for GKE pods and services
- Firewall rules for internal traffic, SSH, HTTP/HTTPS

## Usage

```hcl
module "networking" {
  source = "./modules/networking"

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
| subnet_cidr | CIDR range for the subnet | string | 10.0.0.0/24 |
| pods_cidr | CIDR range for pods (GKE) | string | 10.1.0.0/16 |
| services_cidr | CIDR range for services (GKE) | string | 10.2.0.0/16 |
| ssh_source_ranges | Source IP ranges allowed for SSH | list(string) | ["0.0.0.0/0"] |

## Outputs

| Name | Description |
|------|-------------|
| vpc_network_name | The name of the VPC network |
| vpc_network_id | The ID of the VPC network |
| subnet_name | The name of the subnet |
| subnet_id | The ID of the subnet |
