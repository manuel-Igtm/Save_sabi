# Save Sabi - Cloud Run Deployment Guide

This guide covers deploying Save Sabi to Google Cloud Run with Cloud SQL and Cloud Tasks.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Google Cloud Platform                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐    ┌──────────────┐  │
│  │  Cloud Run   │────▶│  Cloud SQL   │    │   Cloud      │  │
│  │  (Django)    │     │ (PostgreSQL) │    │   Storage    │  │
│  └──────────────┘     └──────────────┘    │  (Static)    │  │
│         │                                  └──────────────┘  │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐     ┌──────────────┐                      │
│  │ Cloud Tasks  │────▶│  Cloud Run   │                      │
│  │  (Celery     │     │  (Worker)    │                      │
│  │   Queue)     │     │              │                      │
│  └──────────────┘     └──────────────┘                      │
│                                                              │
│  ┌──────────────┐     ┌──────────────┐                      │
│  │   Secret     │     │   Cloud      │                      │
│  │   Manager    │     │   Scheduler  │                      │
│  └──────────────┘     └──────────────┘                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. Google Cloud account with billing enabled
2. Google Cloud SDK (`gcloud`) installed
3. Docker installed (for local testing)

## Step 1: GCP Project Setup

```bash
# Set your project ID
export PROJECT_ID=your-project-id
export REGION=us-central1

# Authenticate
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    cloudtasks.googleapis.com \
    cloudscheduler.googleapis.com
```

## Step 2: Cloud SQL Setup

```bash
# Create PostgreSQL instance
gcloud sql instances create save-sabi-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password=your-root-password \
    --storage-type=SSD \
    --storage-size=10GB

# Create database
gcloud sql databases create savesabi --instance=save-sabi-db

# Create user
gcloud sql users create savesabi \
    --instance=save-sabi-db \
    --password=your-db-password

# Get connection name
gcloud sql instances describe save-sabi-db --format='value(connectionName)'
# Output: your-project-id:us-central1:save-sabi-db
```

## Step 3: Secret Manager Setup

```bash
# Create secrets
echo -n "your-django-secret-key" | \
    gcloud secrets create django-secret-key --data-file=-

echo -n "postgres://savesabi:your-db-password@/savesabi?host=/cloudsql/${PROJECT_ID}:${REGION}:save-sabi-db" | \
    gcloud secrets create database-url --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding django-secret-key \
    --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding database-url \
    --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Step 4: Cloud Storage Bucket Setup

```bash
# Create bucket for static and media files
export BUCKET_NAME=${PROJECT_ID}-save-sabi-assets

gsutil mb -l $REGION gs://$BUCKET_NAME

# Set bucket to public read for static files
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

# Enable CORS for the bucket
cat > cors.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF
gsutil cors set cors.json gs://$BUCKET_NAME

# Store bucket name as secret
echo -n "$BUCKET_NAME" | \
    gcloud secrets create gcs-bucket-name --data-file=-

gcloud secrets add-iam-policy-binding gcs-bucket-name \
    --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Grant Cloud Run service account access to bucket
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
    --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

## Step 5: Build and Push Container

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build image
docker build -t gcr.io/$PROJECT_ID/save-sabi:latest .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/save-sabi:latest

# Or use Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/save-sabi:latest
```

## Step 6: Deploy to Cloud Run

```bash
# Deploy web service
gcloud run deploy save-sabi \
    --image gcr.io/$PROJECT_ID/save-sabi:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --add-cloudsql-instances ${PROJECT_ID}:${REGION}:save-sabi-db \
    --set-secrets="SECRET_KEY=django-secret-key:latest,DATABASE_URL=database-url:latest,GCS_BUCKET_NAME=gcs-bucket-name:latest" \
    --set-env-vars="DEBUG=False,ALLOWED_HOSTS=*.run.app,GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 80

# Collect static files to GCS bucket
gcloud run jobs create save-sabi-collectstatic \
    --image gcr.io/$PROJECT_ID/save-sabi:latest \
    --region $REGION \
    --set-secrets="SECRET_KEY=django-secret-key:latest,GCS_BUCKET_NAME=gcs-bucket-name:latest" \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --command="python" \
    --args="manage.py,collectstatic,--noinput"

# Execute collectstatic job
gcloud run jobs execute save-sabi-collectstatic --region $REGION --wait
```

## Step 7: Run Migrations

```bash
# Create a one-time job to run migrations
gcloud run jobs create save-sabi-migrate \
    --image gcr.io/$PROJECT_ID/save-sabi:latest \
    --region $REGION \
    --add-cloudsql-instances ${PROJECT_ID}:${REGION}:save-sabi-db \
    --set-secrets="SECRET_KEY=django-secret-key:latest,DATABASE_URL=database-url:latest" \
    --command="python" \
    --args="manage.py,migrate"

# Execute migration job
gcloud run jobs execute save-sabi-migrate --region $REGION --wait
```

## Step 7: Cloud Tasks Setup (for Celery replacement)

For Cloud Run, we use Cloud Tasks instead of Celery:

```bash
# Create task queue
gcloud tasks queues create save-sabi-tasks \
    --location=$REGION \
    --max-concurrent-dispatches=10 \
    --max-attempts=3

# Create worker service
gcloud run deploy save-sabi-worker \
    --image gcr.io/$PROJECT_ID/save-sabi:latest \
    --platform managed \
    --region $REGION \
    --no-allow-unauthenticated \
    --add-cloudsql-instances ${PROJECT_ID}:${REGION}:save-sabi-db \
    --set-secrets="SECRET_KEY=django-secret-key:latest,DATABASE_URL=database-url:latest" \
    --memory 256Mi
```

## Step 8: Cloud Scheduler (for periodic tasks)

```bash
# Daily rule evaluation
gcloud scheduler jobs create http save-sabi-daily-rules \
    --location=$REGION \
    --schedule="0 6 * * *" \
    --uri="https://save-sabi-xxxxx.run.app/api/v1/tasks/evaluate-daily-rules/" \
    --http-method=POST \
    --oidc-service-account-email=${PROJECT_ID}@appspot.gserviceaccount.com

# Streak check
gcloud scheduler jobs create http save-sabi-streak-check \
    --location=$REGION \
    --schedule="0 0 * * *" \
    --uri="https://save-sabi-xxxxx.run.app/api/v1/tasks/check-streaks/" \
    --http-method=POST \
    --oidc-service-account-email=${PROJECT_ID}@appspot.gserviceaccount.com
```

## Step 9: Custom Domain (Optional)

```bash
# Map domain
gcloud run domain-mappings create \
    --service save-sabi \
    --domain api.savesabi.com \
    --region $REGION

# Update DNS with provided records
# Add CNAME record pointing to ghs.googlehosted.com
```

## Environment Variables

Set these in Cloud Run:

| Variable | Description |
|----------|-------------|
| `DEBUG` | `False` |
| `SECRET_KEY` | From Secret Manager |
| `DATABASE_URL` | From Secret Manager |
| `GCS_BUCKET_NAME` | From Secret Manager |
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID |
| `ALLOWED_HOSTS` | `*.run.app,api.savesabi.com` |
| `CORS_ALLOWED_ORIGINS` | `https://savesabi.com` |

## CI/CD with Cloud Build

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/save-sabi:$COMMIT_SHA', '.']

  # Push image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/save-sabi:$COMMIT_SHA']

  # Run migrations
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'jobs'
      - 'update'
      - 'save-sabi-migrate'
      - '--image'
      - 'gcr.io/$PROJECT_ID/save-sabi:$COMMIT_SHA'
      - '--region'
      - 'us-central1'

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'jobs'
      - 'execute'
      - 'save-sabi-migrate'
      - '--region'
      - 'us-central1'
      - '--wait'

  # Deploy
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'save-sabi'
      - '--image'
      - 'gcr.io/$PROJECT_ID/save-sabi:$COMMIT_SHA'
      - '--region'
      - 'us-central1'

images:
  - 'gcr.io/$PROJECT_ID/save-sabi:$COMMIT_SHA'
```

Connect to GitHub:

```bash
gcloud builds triggers create github \
    --repo-name=save-sabi \
    --repo-owner=your-org \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml
```

## Monitoring

### View Logs
```bash
gcloud run logs read save-sabi --region=$REGION
```

### Setup Alerts
```bash
# Alert on high error rate
gcloud monitoring policies create \
    --policy-from-file=alert-policy.yaml
```

## Cost Optimization

1. **Use min-instances=0** for dev/staging
2. **Set concurrency=80** to maximize container usage
3. **Use db-f1-micro** for Cloud SQL (free tier eligible)
4. **Enable Cloud SQL auto-backup** instead of manual

## Rollback

```bash
# List revisions
gcloud run revisions list --service save-sabi --region $REGION

# Rollback to previous revision
gcloud run services update-traffic save-sabi \
    --to-revisions=save-sabi-xxxxx=100 \
    --region $REGION
```

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` in Secret Manager
- [ ] Database password in Secret Manager
- [ ] HTTPS enforced (automatic with Cloud Run)
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] SQL injection protection (Django ORM)
- [ ] CSRF protection for admin
- [ ] Security headers configured
