#!/bin/bash
# =============================================================================
# Cloud Run Migration Job Setup Script
# Creates a Cloud Run Job for running Django migrations
# =============================================================================

set -e

PROJECT_ID="${GCP_PROJECT:-your-project-id}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-}"
IMAGE="${GCR_REGISTRY:-gcr.io/$PROJECT_ID}/save-sabi:latest"

echo "=== Setting up Cloud Run Migration Job ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Image: $IMAGE"

# Create the migration job
gcloud run jobs create save-sabi-migrate \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --image="$IMAGE" \
    --command="python" \
    --args="manage.py,migrate,--noinput" \
    --set-env-vars="DJANGO_SETTINGS_MODULE=save_sabi.settings" \
    --memory="512Mi" \
    --cpu="1" \
    --max-retries=3 \
    --task-timeout="10m" \
    ${SERVICE_ACCOUNT:+--service-account="$SERVICE_ACCOUNT"}

echo "=== Migration job created successfully ==="
echo ""
echo "To run migrations manually:"
echo "  gcloud run jobs execute save-sabi-migrate --region=$REGION --wait"
echo ""
echo "To update the job with a new image:"
echo "  gcloud run jobs update save-sabi-migrate --image=NEW_IMAGE --region=$REGION"
