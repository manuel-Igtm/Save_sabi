#!/bin/bash
# =============================================================================
# Deploy to Cloud Run Script
# Deploys Save Sabi to Google Cloud Run with all configurations
# =============================================================================

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT:-}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
SERVICE_NAME="save-sabi"
IMAGE="${1:-}"
ENVIRONMENT="${2:-staging}"  # staging or production

if [ -z "$PROJECT_ID" ] || [ -z "$IMAGE" ]; then
    echo "Usage: GCP_PROJECT=your-project $0 <image> [environment]"
    echo "Example: GCP_PROJECT=my-project $0 gcr.io/my-project/save-sabi:v1 production"
    exit 1
fi

echo "=== Deploying Save Sabi to Cloud Run ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Image: $IMAGE"
echo "Environment: $ENVIRONMENT"
echo ""

# Set project
gcloud config set project "$PROJECT_ID"

# Determine configuration based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    SERVICE_SUFFIX=""
    DEBUG="False"
    MIN_INSTANCES=1
    MAX_INSTANCES=10
    MEMORY="512Mi"
    CPU="1"
else
    SERVICE_SUFFIX="-staging"
    DEBUG="True"
    MIN_INSTANCES=0
    MAX_INSTANCES=3
    MEMORY="512Mi"
    CPU="1"
fi

FULL_SERVICE_NAME="${SERVICE_NAME}${SERVICE_SUFFIX}"
SA_EMAIL="save-sabi-service@${PROJECT_ID}.iam.gserviceaccount.com"
BUCKET_NAME="${PROJECT_ID}-save-sabi-assets"

echo "=== Running Migrations ==="
gcloud run jobs execute save-sabi-migrate --region="$REGION" --wait || echo "Migration job not found, skipping..."

echo "=== Deploying Service ==="
gcloud run deploy "$FULL_SERVICE_NAME" \
    --image="$IMAGE" \
    --platform=managed \
    --region="$REGION" \
    --service-account="$SA_EMAIL" \
    --allow-unauthenticated \
    --memory="$MEMORY" \
    --cpu="$CPU" \
    --min-instances="$MIN_INSTANCES" \
    --max-instances="$MAX_INSTANCES" \
    --concurrency=80 \
    --timeout=60 \
    --port=8000 \
    --set-env-vars="DEBUG=$DEBUG" \
    --set-env-vars="GS_BUCKET_NAME=$BUCKET_NAME" \
    --set-env-vars="DJANGO_SETTINGS_MODULE=save_sabi.settings" \
    --set-secrets="SECRET_KEY=django-secret-key:latest" \
    --set-secrets="DATABASE_URL=database-url:latest" \
    --set-secrets="REDIS_URL=redis-url:latest" \
    --add-cloudsql-instances="${PROJECT_ID}:${REGION}:save-sabi-db"

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$FULL_SERVICE_NAME" \
    --region="$REGION" \
    --format="value(status.url)")

echo ""
echo "=== Deployment Complete ==="
echo "Service URL: $SERVICE_URL"
echo ""
echo "Health check: curl ${SERVICE_URL}/api/health/"
echo ""

# Run health check
echo "=== Running Health Check ==="
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/api/health/" || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✓ Health check passed (HTTP $HTTP_STATUS)"
else
    echo "⚠ Health check returned HTTP $HTTP_STATUS"
fi

# Collect static files (optional - can be done in build)
echo ""
echo "=== Collecting Static Files ==="
gcloud run jobs execute save-sabi-collectstatic --region="$REGION" --wait 2>/dev/null || echo "Static collection job not configured, skipping..."

echo ""
echo "=== Deployment Summary ==="
echo "Service: $FULL_SERVICE_NAME"
echo "URL: $SERVICE_URL"
echo "Environment: $ENVIRONMENT"
echo "Debug: $DEBUG"
echo "Instances: $MIN_INSTANCES - $MAX_INSTANCES"
