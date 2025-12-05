#!/bin/bash
# =============================================================================
# Initial GCP Setup Script for Save Sabi
# Run this script once to set up all required GCP resources
# =============================================================================

set -e

# Configuration
PROJECT_ID="${1:-}"
REGION="${2:-us-central1}"
SERVICE_NAME="save-sabi"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <project-id> [region]"
    echo "Example: $0 my-gcp-project us-central1"
    exit 1
fi

echo "=== Save Sabi GCP Setup ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set the project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "=== Enabling Required APIs ==="
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    secretmanager.googleapis.com \
    storage.googleapis.com

# Create Cloud SQL instance (PostgreSQL)
echo "=== Creating Cloud SQL Instance ==="
gcloud sql instances create save-sabi-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region="$REGION" \
    --storage-auto-increase \
    --storage-size=10GB \
    --backup-start-time=03:00 \
    --availability-type=zonal \
    || echo "Cloud SQL instance may already exist"

# Create database
echo "=== Creating Database ==="
gcloud sql databases create save_sabi \
    --instance=save-sabi-db \
    || echo "Database may already exist"

# Create database user
DB_PASSWORD=$(openssl rand -base64 32)
echo "=== Creating Database User ==="
gcloud sql users create savesabi \
    --instance=save-sabi-db \
    --password="$DB_PASSWORD" \
    || echo "User may already exist"

# Create Redis instance (Memorystore)
echo "=== Creating Redis Instance ==="
gcloud redis instances create save-sabi-redis \
    --size=1 \
    --region="$REGION" \
    --redis-version=redis_6_x \
    --tier=basic \
    || echo "Redis instance may already exist"

# Create GCS bucket for static/media files
BUCKET_NAME="${PROJECT_ID}-save-sabi-assets"
echo "=== Creating GCS Bucket ==="
gsutil mb -l "$REGION" "gs://$BUCKET_NAME" \
    || echo "Bucket may already exist"

# Set bucket CORS policy
cat > /tmp/cors.json << 'EOF'
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF
gsutil cors set /tmp/cors.json "gs://$BUCKET_NAME"

# Make bucket publicly readable for static files
gsutil iam ch allUsers:objectViewer "gs://$BUCKET_NAME"

# Create service account for Cloud Run
SA_NAME="save-sabi-service"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=== Creating Service Account ==="
gcloud iam service-accounts create "$SA_NAME" \
    --display-name="Save Sabi Service Account" \
    || echo "Service account may already exist"

# Grant required roles
echo "=== Granting IAM Roles ==="
for role in \
    roles/cloudsql.client \
    roles/storage.objectAdmin \
    roles/secretmanager.secretAccessor \
    roles/redis.editor
do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role" \
        --quiet
done

# Create secrets in Secret Manager
echo "=== Creating Secrets ==="

# Django secret key
DJANGO_SECRET=$(openssl rand -base64 50 | tr -d '\n')
echo -n "$DJANGO_SECRET" | gcloud secrets create django-secret-key --data-file=- \
    || echo "Secret may already exist"

# Database URL
DB_URL="postgresql://savesabi:${DB_PASSWORD}@/save_sabi?host=/cloudsql/${PROJECT_ID}:${REGION}:save-sabi-db"
echo -n "$DB_URL" | gcloud secrets create database-url --data-file=- \
    || echo "Secret may already exist"

# Get Redis host
REDIS_HOST=$(gcloud redis instances describe save-sabi-redis --region="$REGION" --format="value(host)" 2>/dev/null || echo "pending")
REDIS_URL="redis://${REDIS_HOST}:6379/0"
echo -n "$REDIS_URL" | gcloud secrets create redis-url --data-file=- \
    || echo "Secret may already exist"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Resources created:"
echo "  - Cloud SQL: save-sabi-db"
echo "  - Database: save_sabi"
echo "  - Redis: save-sabi-redis"
echo "  - GCS Bucket: $BUCKET_NAME"
echo "  - Service Account: $SA_EMAIL"
echo ""
echo "Secrets created in Secret Manager:"
echo "  - django-secret-key"
echo "  - database-url"
echo "  - redis-url"
echo ""
echo "Next steps:"
echo "  1. Update Cloud Run deployment to use these secrets"
echo "  2. Configure VPC connector for Redis access"
echo "  3. Deploy the application"
echo ""
echo "IMPORTANT: Save these values securely:"
echo "  Database Password: $DB_PASSWORD"
