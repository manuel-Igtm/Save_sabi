# Save Sabi - Full-Stack Deployment

Complete deployment guide for Save Sabi to Google Cloud Platform.

## Prerequisites

- Google Cloud SDK (`gcloud`)
- Terraform >= 1.0
- Docker
- Node.js 18+ and npm
- Python 3.11+
- GCP Project with billing enabled

## Quick Start

### 1. Configure GCP

```powershell
# Authenticate
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project save-sabi

# Enable APIs
cd terraform
.\enable-apis.ps1
```

### 2. Deploy Infrastructure

```powershell
# Initialize Terraform
terraform init

# Review plan
terraform plan

# Deploy
terraform apply
```

### 3. Deploy Full Stack

```powershell
# Run deployment script
cd ../scripts
.\deploy.ps1  # Windows
# or
./deploy.sh   # Linux/Mac
```

## Manual Deployment Steps

### Backend Deployment

```powershell
# Build Docker image
cd back_end
docker build -t gcr.io/save-sabi/save-sabi-api:latest .

# Push to GCR
docker push gcr.io/save-sabi/save-sabi-api:latest

# Deploy with Terraform
cd ../terraform
terraform apply -var="backend_image=gcr.io/save-sabi/save-sabi-api:latest"

# Run migrations
gcloud run jobs execute save-sabi-migrate --region=us-central1 --wait
```

### Frontend Deployment

```powershell
# Build frontend
cd front_end
npm install
npm run build

# Deploy to Cloud Storage
$BUCKET = terraform output -raw storage_bucket_name
gsutil -m rsync -r dist/ gs://$BUCKET/
gsutil iam ch allUsers:objectViewer gs://$BUCKET
```

## Environment Variables

### Backend (.env)
```bash
DEBUG=False
DJANGO_SECRET_KEY=<from-secret-manager>
DATABASE_URL=<from-secret-manager>
GCS_BUCKET_NAME=<from-terraform-output>
CORS_ALLOWED_ORIGINS=<frontend-url>
```

### Frontend (.env)
```bash
VITE_API_URL=<backend-url-from-terraform>
VITE_API_VERSION=v1
```

## Post-Deployment

### Create Superuser

```powershell
gcloud run jobs create save-sabi-createsuperuser \
  --image gcr.io/save-sabi/save-sabi-api:latest \
  --region us-central1 \
  --set-cloudsql-instances <connection-name> \
  --set-secrets="DATABASE_URL=<secret-id>:latest" \
  --command="python" \
  --args="manage.py,createsuperuser" \
  --execute-now
```

### Configure Cloud Scheduler

```powershell
# Daily budget rules
gcloud scheduler jobs create http save-sabi-daily-rules \
  --location=us-central1 \
  --schedule="0 6 * * *" \
  --uri="<backend-url>/api/v1/tasks/evaluate-daily-rules/" \
  --http-method=POST

# Streak check
gcloud scheduler jobs create http save-sabi-streak-check \
  --location=us-central1 \
  --schedule="0 0 * * *" \
  --uri="<backend-url>/api/v1/tasks/check-streaks/" \
  --http-method=POST
```

## Verification

### Backend Health Check
```powershell
curl <backend-url>/healthz
```

### Frontend Access
```
https://storage.googleapis.com/<bucket-name>/index.html
```

### API Test
```powershell
curl <backend-url>/api/v1/
```

## Troubleshooting

### Backend Issues

**Cloud Run not starting:**
- Check logs: `gcloud run services logs read save-sabi-dev-api --region=us-central1`
- Verify secrets are accessible
- Check Cloud SQL connection

**Database connection failed:**
- Verify Cloud SQL instance is running
- Check service account has `cloudsql.client` role
- Verify DATABASE_URL secret is correct

### Frontend Issues

**API calls failing:**
- Check CORS configuration in backend
- Verify API URL in frontend .env
- Check browser console for errors

**404 errors:**
- Verify bucket is public
- Check files were uploaded to bucket
- Verify bucket website configuration

## Cleanup

```powershell
# Destroy all infrastructure
cd terraform
terraform destroy

# Delete Docker images
gcloud container images delete gcr.io/save-sabi/save-sabi-api:latest
```

## Cost Optimization

- Set Cloud Run min instances to 0 for dev
- Use db-f1-micro for development
- Enable Cloud CDN for frontend
- Set up budget alerts

## Security Checklist

- [ ] Secrets in Secret Manager (not in code)
- [ ] CORS restricted to frontend domain
- [ ] Cloud SQL deletion protection enabled (production)
- [ ] HTTPS enforced
- [ ] Service account least privilege
- [ ] Regular security updates
