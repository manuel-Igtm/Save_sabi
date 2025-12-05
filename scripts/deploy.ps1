# Full-Stack Deployment Script for Save Sabi (PowerShell)
# Deploys both backend (Cloud Run) and frontend (Cloud Storage)

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = "save-sabi"
$REGION = "us-central1"
$BACKEND_IMAGE = "gcr.io/$PROJECT_ID/save-sabi-api:latest"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Save Sabi - Full Stack Deployment" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Step 1: Check prerequisites
Write-Host "`nStep 1: Checking prerequisites..." -ForegroundColor Yellow
$commands = @("gcloud", "terraform", "docker")
foreach ($cmd in $commands) {
    if (!(Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "Error: $cmd is required but not installed." -ForegroundColor Red
        exit 1
    }
}
Write-Host "✓ All prerequisites met" -ForegroundColor Green

# Step 2: Set GCP project
Write-Host "`nStep 2: Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID
Write-Host "✓ Project set to $PROJECT_ID" -ForegroundColor Green

# Step 3: Build and push backend Docker image
Write-Host "`nStep 3: Building backend Docker image..." -ForegroundColor Yellow
Set-Location ..\back_end
docker build -t $BACKEND_IMAGE .
Write-Host "✓ Backend image built" -ForegroundColor Green

Write-Host "`nStep 4: Pushing backend image to GCR..." -ForegroundColor Yellow
docker push $BACKEND_IMAGE
Write-Host "✓ Backend image pushed to GCR" -ForegroundColor Green

# Step 5: Deploy infrastructure with Terraform
Write-Host "`nStep 5: Deploying infrastructure with Terraform..." -ForegroundColor Yellow
Set-Location ..\terraform

# Initialize Terraform if not already done
if (!(Test-Path ".terraform")) {
    terraform init
}

# Update backend_image variable
$env:TF_VAR_backend_image = $BACKEND_IMAGE

# Apply Terraform configuration
terraform apply -auto-approve

# Get outputs
$BACKEND_URL = terraform output -raw backend_url
$BUCKET_NAME = terraform output -raw storage_bucket_name

Write-Host "✓ Infrastructure deployed" -ForegroundColor Green
Write-Host "  Backend URL: $BACKEND_URL" -ForegroundColor Green
Write-Host "  Storage Bucket: $BUCKET_NAME" -ForegroundColor Green

# Step 6: Run database migrations
Write-Host "`nStep 6: Running database migrations..." -ForegroundColor Yellow
$CLOUDSQL_CONNECTION = terraform output -raw cloudsql_connection_name
$DATABASE_SECRET = terraform output -raw database_url_secret_id

# Create migration job if it doesn't exist
try {
    gcloud run jobs describe save-sabi-migrate --region=$REGION 2>$null
} catch {
    gcloud run jobs create save-sabi-migrate `
      --image $BACKEND_IMAGE `
      --region $REGION `
      --set-cloudsql-instances $CLOUDSQL_CONNECTION `
      --set-secrets="DATABASE_URL=${DATABASE_SECRET}:latest" `
      --command="python" `
      --args="manage.py,migrate" `
      --max-retries 3
}

# Execute migration
gcloud run jobs execute save-sabi-migrate --region=$REGION --wait
Write-Host "✓ Database migrations completed" -ForegroundColor Green

# Step 7: Build and deploy frontend
Write-Host "`nStep 8: Building frontend..." -ForegroundColor Yellow
Set-Location ..\front_end

# Set API URL from Terraform output
"VITE_API_URL=$BACKEND_URL" | Out-File -FilePath .env.production -Encoding utf8
"VITE_API_VERSION=v1" | Out-File -FilePath .env.production -Append -Encoding utf8

# Build frontend
npm run build
Write-Host "✓ Frontend built" -ForegroundColor Green

# Step 8: Deploy frontend to Cloud Storage
Write-Host "`nStep 9: Deploying frontend to Cloud Storage..." -ForegroundColor Yellow
gsutil -m rsync -r -d dist/ gs://$BUCKET_NAME/

# Set bucket for website hosting
gsutil web set -m index.html -e index.html gs://$BUCKET_NAME

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

Write-Host "✓ Frontend deployed" -ForegroundColor Green
Write-Host "  Frontend URL: https://storage.googleapis.com/$BUCKET_NAME/index.html" -ForegroundColor Green

# Step 9: Summary
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Backend API: $BACKEND_URL" -ForegroundColor Green
Write-Host "Frontend: https://storage.googleapis.com/$BUCKET_NAME/index.html" -ForegroundColor Green
Write-Host "Admin Panel: $BACKEND_URL/admin/" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Update frontend .env with production backend URL"
Write-Host "2. Configure custom domain (optional)"
Write-Host "3. Set up Cloud Scheduler for periodic tasks"
Write-Host "4. Configure monitoring and alerts"
