#!/bin/bash
# Deploy NZ Habitat Intelligence to production
# Usage: ./deploy.sh [dev|staging|prod]

set -e

ENVIRONMENT=${1:-dev}
IMAGE_TAG=${2:-latest}
ECR_REPOSITORY="nz-habitat-dashboard"

echo "Deploying to $ENVIRONMENT environment..."

# Build and tag image
echo "Building Docker image..."
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .

if [ "$ENVIRONMENT" = "prod" ]; then
    # Push to ECR (AWS)
    echo "Pushing to ECR..."
    aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-2.amazonaws.com
    docker tag $ECR_REPOSITORY:$IMAGE_TAG ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-2.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
    docker push ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-2.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG
fi

# Deploy with docker-compose
echo "Starting services..."
docker compose -f deploy/docker-compose.prod.yml up -d

echo "Deployment complete!"
echo "Dashboard: http://localhost:8050"
echo "Prefect UI: http://localhost:4200"
