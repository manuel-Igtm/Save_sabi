#!/bin/bash
# Full-Stack Deployment Script for Save Sabi
# Deploys both backend (Cloud Run) and frontend (Cloud Storage)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="save-sabi"
REGION="us-central1"
BACKEND_IMAGE="gcr.io/${PROJECT_ID}/save-sabi-api:latest"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Save Sabi - Full Stack Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Step 1: Check prerequisites
echo -e "\n${YELLOW}Step 1: Checking prerequisites...${NC}"
command -v gcloud >/dev/null 2>&1 || { echo -e "${RED}gcloud CLI is required but not installed.${NC}" >&2; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo -e "${RED}Terraform is required but not installed.${NC}" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed.${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ All prerequisites met${NC}"

# Step 2: Set GCP project
echo -e "\n${YELLOW}Step 2: Setting GCP project...${NC}"
gcloud config set project ${PROJECT_ID}
echo -e "${GREEN}✓ Project set to ${PROJECT_ID}${NC}"

# Step 3: Build and push backend Docker image
echo -e "\n${YELLOW}Step 3: Building backend Docker image...${NC}"
cd ../back_end
docker build -t ${BACKEND_IMAGE} .
echo -e "${GREEN}✓ Backend image built${NC}"

echo -e "\n${YELLOW}Step 4: Pushing backend image to GCR...${NC}"
docker push ${BACKEND_IMAGE}
echo -e "${GREEN}✓ Backend image pushed to GCR${NC}"

# Step 5: Deploy infrastructure with Terraform
echo -e "\n${YELLOW}Step 5: Deploying infrastructure with Terraform...${NC}"
cd ../terraform

# Initialize Terraform if not already done
if [ ! -d ".terraform" ]; then
    terraform init
fi

# Update backend_image variable
export TF_VAR_backend_image=${BACKEND_IMAGE}

# Apply Terraform configuration
terraform apply -auto-approve

# Get outputs
BACKEND_URL=$(terraform output -raw backend_url)
BUCKET_NAME=$(terraform output -raw storage_bucket_name)

echo -e "${GREEN}✓ Infrastructure deployed${NC}"
echo -e "${GREEN}  Backend URL: ${BACKEND_URL}${NC}"
echo -e "${GREEN}  Storage Bucket: ${BUCKET_NAME}${NC}"

# Step 6: Run database migrations
echo -e "\n${YELLOW}Step 6: Running database migrations...${NC}"
# Create migration job if it doesn't exist
gcloud run jobs describe save-sabi-migrate --region=${REGION} >/dev/null 2>&1 || \
gcloud run jobs create save-sabi-migrate \
  --image ${BACKEND_IMAGE} \
  --region ${REGION} \
  --set-cloudsql-instances $(terraform output -raw cloudsql_connection_name) \
  --set-secrets="DATABASE_URL=$(terraform output -raw database_url_secret_id):latest" \
  --command="python" \
  --args="manage.py,migrate" \
  --max-retries 3

# Execute migration
gcloud run jobs execute save-sabi-migrate --region=${REGION} --wait
echo -e "${GREEN}✓ Database migrations completed${NC}"

# Step 7: Create superuser (optional, interactive)
echo -e "\n${YELLOW}Step 7: Create Django superuser? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    gcloud run jobs create save-sabi-createsuperuser \
      --image ${BACKEND_IMAGE} \
      --region ${REGION} \
      --set-cloudsql-instances $(terraform output -raw cloudsql_connection_name) \
      --set-secrets="DATABASE_URL=$(terraform output -raw database_url_secret_id):latest" \
      --command="python" \
      --args="manage.py,createsuperuser" \
      --execute-now \
      --wait
fi

# Step 8: Build and deploy frontend
echo -e "\n${YELLOW}Step 8: Building frontend...${NC}"
cd ../front_end

# Set API URL from Terraform output
echo "VITE_API_URL=${BACKEND_URL}" > .env.production
echo "VITE_API_VERSION=v1" >> .env.production

# Build frontend
npm run build
echo -e "${GREEN}✓ Frontend built${NC}"

# Step 9: Deploy frontend to Cloud Storage
echo -e "\n${YELLOW}Step 9: Deploying frontend to Cloud Storage...${NC}"
gsutil -m rsync -r -d dist/ gs://${BUCKET_NAME}/

# Set bucket for website hosting
gsutil web set -m index.html -e index.html gs://${BUCKET_NAME}

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}

echo -e "${GREEN}✓ Frontend deployed${NC}"
echo -e "${GREEN}  Frontend URL: https://storage.googleapis.com/${BUCKET_NAME}/index.html${NC}"

# Step 10: Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backend API: ${BACKEND_URL}${NC}"
echo -e "${GREEN}Frontend: https://storage.googleapis.com/${BUCKET_NAME}/index.html${NC}"
echo -e "${GREEN}Admin Panel: ${BACKEND_URL}/admin/${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "1. Update frontend .env with production backend URL"
echo -e "2. Configure custom domain (optional)"
echo -e "3. Set up Cloud Scheduler for periodic tasks"
echo -e "4. Configure monitoring and alerts"
