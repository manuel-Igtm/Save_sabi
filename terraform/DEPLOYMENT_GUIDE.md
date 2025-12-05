# Save Sabi - Terraform Deployment Guide

This guide walks you through deploying the Save Sabi infrastructure to Google Cloud Platform using Terraform.

## What Will Be Deployed

The Terraform configuration will create:

### Core Infrastructure
- **VPC Network**: Custom VPC with subnets configured for GKE
- **Cloud SQL**: PostgreSQL 15 database instance with automated backups
- **Cloud Storage**: Bucket for static and media files
- **Secret Manager**: Secure storage for Django secrets and credentials

### Firewall Rules
- Internal traffic (all ports within VPC)
- SSH access (port 22)
- HTTP/HTTPS access (ports 80, 443)

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **GCP Project** created
3. **gcloud CLI** installed and authenticated
4. **Terraform** >= 1.0 installed

## Step-by-Step Deployment

### 1. Authenticate with GCP

```powershell
# Login to GCP
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs

Run the provided script to enable all necessary GCP APIs:

```powershell
cd terraform
.\enable-apis.ps1
```

Or manually enable them:

```powershell
gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable run.googleapis.com
```

### 3. Configure Variables

Copy the example variables file:

```powershell
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set your project ID:

```hcl
project_id   = "your-actual-project-id"
region       = "us-central1"
zone         = "us-central1-a"
environment  = "dev"
project_name = "save-sabi"
```

### 4. Initialize Terraform

```powershell
terraform init
```

This will:
- Download the Google Cloud provider
- Download the Random provider
- Initialize the backend
- Set up modules

### 5. Review the Plan

```powershell
terraform plan
```

Expected resources to be created:
- 1 VPC network
- 1 subnet with secondary IP ranges
- 3 firewall rules
- 1 Cloud SQL instance
- 1 Cloud SQL database
- 1 Cloud SQL user
- 1 Cloud Storage bucket
- 3 Secret Manager secrets (Django key, database URL, bucket name)

### 6. Apply the Configuration

```powershell
terraform apply
```

Type `yes` when prompted. This will take 5-10 minutes, primarily waiting for Cloud SQL instance creation.

### 7. View Outputs

After successful deployment:

```powershell
terraform output
```

Important outputs:
- `cloudsql_connection_name`: Use this for Cloud Run deployment
- `storage_bucket_name`: GCS bucket for static/media files
- `django_secret_key_id`: Secret Manager ID for Django secret
- `database_url_secret_id`: Secret Manager ID for database URL

## Post-Deployment Steps

### 1. Retrieve Database Password

```powershell
# Get the database password from Terraform state
terraform output -raw cloudsql_database_password
```

### 2. Connect to Cloud SQL (Optional)

For testing, you can connect using Cloud SQL Proxy:

```powershell
# Download Cloud SQL Proxy
# https://cloud.google.com/sql/docs/postgres/sql-proxy

# Get connection name
$CONNECTION_NAME = terraform output -raw cloudsql_connection_name

# Start proxy
cloud-sql-proxy $CONNECTION_NAME
```

### 3. Verify Secret Manager

```powershell
# List secrets
gcloud secrets list

# View secret value (Django secret key)
gcloud secrets versions access latest --secret="save-sabi-dev-django-secret-key"
```

### 4. Test Storage Bucket

```powershell
# List buckets
gcloud storage buckets list

# Upload test file
echo "test" > test.txt
gcloud storage cp test.txt gs://save-sabi-dev-data/test.txt
```

## Next Steps

After infrastructure is deployed:

1. **Deploy Django Application to Cloud Run**
   - Build Docker image
   - Push to Container Registry
   - Deploy to Cloud Run with Cloud SQL connection

2. **Run Database Migrations**
   - Use Cloud Run Jobs or connect via Cloud SQL Proxy
   - Run `python manage.py migrate`

3. **Collect Static Files**
   - Run `python manage.py collectstatic`
   - Files will be uploaded to GCS bucket

4. **Configure Cloud Scheduler**
   - Set up periodic tasks (daily rules, streak checks)

## Cleanup

To destroy all resources:

```powershell
terraform destroy
```

**WARNING**: This will delete:
- Cloud SQL instance and all data
- Storage bucket and all files
- All secrets
- VPC network and firewall rules

## Troubleshooting

### API Not Enabled Error

If you see "API not enabled" errors:

```powershell
# Enable the specific API
gcloud services enable <API_NAME>

# Then retry
terraform apply
```

### Cloud SQL Connection Issues

If Cloud SQL creation fails:

1. Check quota limits in GCP Console
2. Verify billing is enabled
3. Ensure Cloud SQL Admin API is enabled

### Permission Errors

Ensure your account has the following roles:
- Compute Admin
- Cloud SQL Admin
- Secret Manager Admin
- Storage Admin

## Cost Estimation

For `dev` environment with default settings:

- **Cloud SQL (db-f1-micro)**: ~$7-10/month
- **Cloud Storage**: ~$0.02/GB/month
- **VPC Network**: Free (egress charges apply)
- **Secret Manager**: $0.06 per 10,000 accesses

**Total estimated cost**: ~$10-15/month for development

For production, use:
- `cloudsql_tier = "db-n1-standard-1"` (~$50/month)
- `cloudsql_availability_type = "REGIONAL"` (higher availability)
- `cloudsql_deletion_protection = true`

## Security Recommendations

1. **Enable deletion protection** for production databases
2. **Restrict SSH access** to specific IP ranges
3. **Use VPC Service Controls** for enhanced security
4. **Enable Cloud SQL SSL** for encrypted connections
5. **Rotate secrets regularly** using Secret Manager
6. **Enable audit logging** for compliance

## Support

For issues or questions:
- Check Terraform logs: `terraform apply -debug`
- Review GCP Console for resource status
- Check Cloud Logging for errors
