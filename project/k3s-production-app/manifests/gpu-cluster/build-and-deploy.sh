#!/bin/bash

# LlamaIndex FastAPI API Server Build and Deploy Script

set -e

# Configuration
IMAGE_NAME="llamaindex-api"
IMAGE_TAG="latest"
NAMESPACE="ai-services"
REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in git repository
if [ ! -d ".git" ]; then
    echo_warn "Not in a git repository, using 'latest' as tag"
    GIT_TAG="latest"
else
    GIT_TAG=$(git describe --tags --always --dirty)
    echo_info "Using git tag: $GIT_TAG"
fi

# Build Docker image
echo_info "Building Docker image..."
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    -t "${IMAGE_NAME}:${GIT_TAG}" \
    -f manifests/gpu-cluster/Dockerfile \
    manifests/gpu-cluster/

# Tag for registry
if [ ! -z "${REGISTRY}" ] && [ "${REGISTRY}" != "localhost:5000" ]; then
    echo_info "Tagging image for registry: $REGISTRY"
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    docker tag "${IMAGE_NAME}:${GIT_TAG}" "${REGISTRY}/${IMAGE_NAME}:${GIT_TAG}"
    
    echo_info "Pushing image to registry..."
    docker push "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    docker push "${REGISTRY}/${IMAGE_NAME}:${GIT_TAG}"
fi

# Create namespace if it doesn't exist
echo_info "Creating namespace if it doesn't exist..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Apply the deployment
echo_info "Applying Kubernetes manifests..."
kubectl apply -f manifests/gpu-cluster/llamaindex-api-deployment.yaml

# Wait for deployment to be ready
echo_info "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/llamaindex-api -n ${NAMESPACE}

# Check deployment status
echo_info "Deployment status:"
kubectl get pods -n ${NAMESPACE} -l app=llamaindex-api

# Get service information
echo_info "Service information:"
kubectl get svc -n ${NAMESPACE} llamaindex-api-service

# Show access information
NODEPORT=$(kubectl get svc llamaindex-api-service -n ${NAMESPACE} -o jsonpath='{.spec.ports[0].nodePort}')
echo_info "API Server is accessible at:"
echo_info "  Local: http://localhost:${NODEPORT}"
echo_info "  Documentation: http://localhost:${NODEPORT}/docs"
echo_info "  Health Check: http://localhost:${NODEPORT}/health"

echo_info "Deployment completed successfully!"
