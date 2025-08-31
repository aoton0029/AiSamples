#!/bin/bash

# Rollback to the previous version of the application
# Usage: ./rollback.sh <deployment-name>

DEPLOYMENT_NAME=$1

if [ -z "$DEPLOYMENT_NAME" ]; then
  echo "Error: Deployment name is required."
  echo "Usage: ./rollback.sh <deployment-name>"
  exit 1
fi

# Get the current revision of the deployment
CURRENT_REVISION=$(kubectl get deployment $DEPLOYMENT_NAME -o=jsonpath='{.status.revision}')

if [ -z "$CURRENT_REVISION" ]; then
  echo "Error: Deployment '$DEPLOYMENT_NAME' not found."
  exit 1
fi

# Rollback to the previous revision
kubectl rollout undo deployment/$DEPLOYMENT_NAME

if [ $? -eq 0 ]; then
  echo "Successfully rolled back deployment '$DEPLOYMENT_NAME' to revision $CURRENT_REVISION."
else
  echo "Error: Failed to rollback deployment '$DEPLOYMENT_NAME'."
  exit 1
fi