# Save Sabi Infrastructure Deployment Script
# This script enables required GCP APIs and prepares for Terraform deployment

# Set your project ID
$PROJECT_ID = "save-sabi"
$REGION = "us-central1"

Write-Host "Setting GCP project to: $PROJECT_ID" -ForegroundColor Green
gcloud config set project $PROJECT_ID

Write-Host "`nEnabling required GCP APIs..." -ForegroundColor Green
$apis = @(
    "compute.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "run.googleapis.com",
    "cloudtasks.googleapis.com",
    "cloudscheduler.googleapis.com",
    "cloudbuild.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "Enabling $api..." -ForegroundColor Cyan
    gcloud services enable $api
}

Write-Host "`nAll APIs enabled successfully!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Copy terraform.tfvars.example to terraform.tfvars"
Write-Host "2. Update terraform.tfvars with your project ID"
Write-Host "3. Run: terraform init"
Write-Host "4. Run: terraform plan"
Write-Host "5. Run: terraform apply"
